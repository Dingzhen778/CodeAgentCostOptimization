# olclient.py Patches

If `overleaf-sync` is reinstalled or upgraded, re-apply these patches to:
`/home/azureuser/anaconda3/lib/python3.11/site-packages/olsync/olclient.py`

## 1. Replace imports (remove socketIO_client, add websocket/ssl/re)

```python
import requests as reqs
from bs4 import BeautifulSoup
import json
import uuid
import time
import ssl
import re
import websocket
```

## 2. Replace `all_projects` and `get_project` with `_get_projects_json` helper

Overleaf renamed `ol-projects` meta tag to `ol-prefetchedProjectsBlob` (post-2024), and wrapped the list under a `projects` key.

```python
def _get_projects_json(self):
    """Fetch projects list from the dashboard page, handling Overleaf's changing meta tag names."""
    projects_page = reqs.get(PROJECT_URL, cookies=self._cookie)
    soup = BeautifulSoup(projects_page.content, 'html.parser')
    for tag_name in ('ol-prefetchedProjectsBlob', 'ol-projects'):
        meta = soup.find('meta', {'name': tag_name})
        if meta:
            data = json.loads(meta.get('content'))
            return data['projects'] if isinstance(data, dict) else data
    raise Exception("Could not find projects meta tag on Overleaf dashboard.")

def all_projects(self):
    return list(OverleafClient.filter_projects(self._get_projects_json()))

def get_project(self, project_name):
    return next(OverleafClient.filter_projects(self._get_projects_json(), {"name": project_name}), None)
```

## 3. Replace `get_project_infos` (Socket.IO WebSocket with projectId)

Overleaf requires `?projectId=` in the Socket.IO v1 handshake URL.
The response is a `joinProjectResponse` event (not an ack).

```python
def get_project_infos(self, project_id):
    """
    Get detailed project infos via Socket.IO v1 WebSocket (with projectId in handshake).
    """
    cookie_str = "GCLB={}; overleaf_session2={}".format(
        self._cookie["GCLB"], self._cookie["overleaf_session2"]
    )
    t = int(time.time())

    # Socket.IO v1 handshake (must include projectId)
    r = reqs.get(
        "{}/socket.io/1/?t={}&projectId={}".format(BASE_URL, t, project_id),
        headers={"Cookie": cookie_str}, timeout=10
    )
    sid = r.text.split(":")[0]

    ws_url = "{}/socket.io/1/websocket/{}?t={}&projectId={}".format(
        BASE_URL.replace("https://", "wss://"), sid, t, project_id
    )

    project_infos = [None]

    ws = websocket.create_connection(
        ws_url,
        header=["Cookie: {}".format(cookie_str)],
        sslopt={"cert_reqs": ssl.CERT_NONE},
        timeout=20
    )

    try:
        for _ in range(20):
            msg = ws.recv()
            if msg == "1::":
                join_msg = "5:1::" + json.dumps(
                    {"name": "joinProject", "args": [{"project_id": project_id}]}
                )
                ws.send(join_msg)
            elif msg == "2::":
                ws.send("2::")
            elif "rootFolder" in msg:
                payload = re.sub(r"^5:::", "", msg)
                event = json.loads(payload)
                args = event.get("args", [])
                first = args[0] if args else {}
                project_infos[0] = first.get("project", first)
                break
            elif msg.startswith("0"):
                break
    finally:
        try:
            ws.close()
        except Exception:
            pass

    return project_infos[0]
```

## 4. olsync.py: make olbrowserlogin optional

Replace the top import block in `olsync.py`:

```python
from olsync.olclient import OverleafClient
try:
    import olsync.olbrowserlogin as olbrowserlogin
except (ImportError, Exception):
    olbrowserlogin = None
```

And in `login_handler`:

```python
def login_handler(path):
    if olbrowserlogin is None:
        raise click.ClickException("PySide6 not available. Use make_olauth.py to create .olauth manually.")
    ...
```

## 5. Replace `upload_file` (use Socket.IO OT for text files)

The original `upload_file` used `POST /project/{id}/doc` (REST) to create/update text docs.
**This creates file-tree entries but never initialises the docstore — the file appears in Overleaf
but is always empty.**  The correct approach is:

1. Delete existing doc via `DELETE /project/{id}/doc/{doc_id}` (REST — still needed to remove the file-tree entry).
2. Create an **empty** shell via `POST /project/{id}/doc` (REST) — this gives us a doc ID.
3. Connect via Socket.IO v1 WebSocket, `joinDoc` the new (empty) doc, then `applyOtUpdate` with the content.
4. **Stay connected ≥ 35 s** after the OT ack so the real-time server flushes to the persistent docstore.

See `references/ot-upload.py` for a standalone script using this flow.

Critical protocol details discovered through debugging:

| Detail | Wrong | Correct |
|--------|-------|---------|
| Message format | `5:N::` | `5:N+::` — the `+` requests a data-bearing ack |
| `applyOtUpdate` delete component | `{'d': N}` (count) | `{'d': "<exact text>", 'p': 0}` (actual string) |
| `applyOtUpdate` insert component | `{'i': text}` | `{'i': text, 'p': 0}` |
| Connection lifetime | Close immediately after ack | Stay ≥ 35 s, then send `leaveDoc` before closing |

```python
def _find_doc_in_folder(self, project_infos, file_path):
    parts = file_path.split(PATH_SEP)
    folder = project_infos['rootFolder'][0]
    for part in parts[:-1]:
        folder = next((f for f in folder.get('folders', [])
                       if f['name'].lower() == part.lower()), None)
        if folder is None:
            return None
    base = parts[-1]
    return next((d for d in folder.get('docs', [])
                 if d['name'].lower() == base.lower()), None)


TEXT_EXTENSIONS = {
    '.tex', '.bib', '.cls', '.sty', '.bst', '.lua', '.md',
    '.txt', '.cfg', '.def', '.dtx', '.ins', '.latexmkrc',
    '.gitignore', '.yaml', '.yml', '.json', '.js', ''
}

FLUSH_WAIT = 38  # seconds to hold WebSocket open after OT ack


def _ot_write_doc(self, project_id, doc_id, content: str):
    """
    Write `content` to an Overleaf doc via Socket.IO OT.

    Stays connected FLUSH_WAIT seconds after the OT ack so the real-time
    server flushes the in-memory state to the persistent docstore.
    """
    import ssl as _ssl
    import websocket as _ws

    cookie_str = "GCLB={}; overleaf_session2={}".format(
        self._cookie["GCLB"], self._cookie["overleaf_session2"]
    )
    t = int(time.time())
    r = reqs.get(
        "{}/socket.io/1/?t={}&projectId={}".format(BASE_URL, t, project_id),
        headers={"Cookie": cookie_str}, timeout=10
    )
    sid = r.text.split(":")[0]

    ws = _ws.create_connection(
        "{}/socket.io/1/websocket/{}?t={}&projectId={}".format(
            BASE_URL.replace("https://", "wss://"), sid, t, project_id),
        header=["Cookie: {}".format(cookie_str)],
        sslopt={"cert_reqs": _ssl.CERT_NONE},
        timeout=15
    )
    ws.settimeout(5)

    step = "init"
    ot_done = False
    ot_time = None

    try:
        for _ in range(2000):
            if ot_done and time.time() - ot_time > FLUSH_WAIT:
                ws.send("5:99+::" + json.dumps({"name": "leaveDoc", "args": [doc_id]}))
                time.sleep(3)
                break
            try:
                msg = ws.recv()
            except _ws.WebSocketTimeoutException:
                ws.send("2::")
                continue
            except Exception:
                break

            if msg == "2::":
                ws.send("2::")
                continue

            if msg == "1::" and step == "init":
                step = "jp"
                ws.send("5:1+::" + json.dumps(
                    {"name": "joinProject", "args": [{"project_id": project_id}]}))

            elif ("rootFolder" in msg or "joinProjectResponse" in msg) and step == "jp":
                step = "jd"
                ws.send("5:2+::" + json.dumps(
                    {"name": "joinDoc", "args": [doc_id, {"encodeRanges": True}]}))

            elif msg.startswith("6:::2+") and step == "jd":
                data = json.loads(msg[6:])
                if data[0]:
                    raise RuntimeError("joinDoc error: {}".format(data[0]))
                cur = "\n".join(data[1])
                version = data[2]
                ops = []
                if cur:
                    ops.append({"d": cur, "p": 0})
                ops.append({"i": content, "p": 0})
                ws.send("5:3+::" + json.dumps({
                    "name": "applyOtUpdate",
                    "args": [doc_id, {"op": ops, "v": version,
                                      "meta": {"source": "claude-code"}}]
                }))
                ot_time = time.time()
                step = "ot"

            elif msg.startswith("6:::3") and step == "ot":
                ot_done = True
                ot_time = time.time()
                step = "staying"

            elif "otUpdateError" in msg:
                raise RuntimeError("OT error: {}".format(msg[:300]))
    finally:
        try:
            ws.close()
        except Exception:
            pass

    if not ot_done:
        raise RuntimeError("OT update not confirmed")


def upload_file(self, project_id, project_infos, file_name, file_size, file):
    folder_id = project_infos['rootFolder'][0]['_id']

    # Resolve nested folder path
    if PATH_SEP in file_name:
        local_folders = file_name.split(PATH_SEP)[:-1]
        current_overleaf_folder = project_infos['rootFolder'][0]['folders']
        for local_folder in local_folders:
            exists_on_remote = False
            for remote_folder in current_overleaf_folder:
                if local_folder.lower() == remote_folder['name'].lower():
                    exists_on_remote = True
                    folder_id = remote_folder['_id']
                    current_overleaf_folder = remote_folder['folders']
                    break
            if not exists_on_remote:
                new_folder = self.create_folder(project_id, folder_id, local_folder)
                current_overleaf_folder.append(new_folder)
                folder_id = new_folder['_id']
                current_overleaf_folder = new_folder['folders']

    base_name = file_name.split(PATH_SEP)[-1]
    _, ext = os.path.splitext(base_name)

    if ext.lower() in TEXT_EXTENSIONS:
        # ── Text file: delete + REST-create shell + OT write ─────────────────
        existing_doc = self._find_doc_in_folder(project_infos, file_name)
        if existing_doc:
            headers = {"X-Csrf-Token": self._csrf}
            reqs.delete(
                DELETE_URL.format(project_id, existing_doc['_id']),
                cookies=self._cookie, headers=headers, json={})

        content = file.read().decode('utf-8', errors='replace')

        # Create empty shell (gives us a doc_id; docstore starts empty)
        doc_url = "{}/project/{}/doc".format(BASE_URL, project_id)
        r = reqs.post(doc_url, cookies=self._cookie,
                      headers={"X-Csrf-Token": self._csrf},
                      json={"name": base_name, "parent_folder_id": folder_id, "lines": []})
        if not r.ok:
            return False
        doc_id = r.json().get("_id")
        if not doc_id:
            return False

        # Write content via OT (stays connected to flush docstore)
        self._ot_write_doc(project_id, doc_id, content)
        return True
    else:
        # ── Binary file: multipart upload ────────────────────────────────────
        params = {
            "folder_id": folder_id, "_csrf": self._csrf,
            "qquuid": str(uuid.uuid4()), "qqfilename": base_name,
            "qqtotalfilesize": file_size,
        }
        r = reqs.post(UPLOAD_URL.format(project_id), cookies=self._cookie,
                      params=params, files={"qqfile": (base_name, file)})
        return r.status_code == 200 and json.loads(r.content).get("success", False)
```

## 6. socketIO_client/transports.py: fix SSLError

In `/home/azureuser/anaconda3/lib/python3.11/site-packages/socketIO_client/transports.py`:

Add `import ssl` to imports, then replace:
```python
except websocket.SSLError as e:
    if 'timed out' in e.message:
```
with:
```python
except (ssl.SSLError, OSError) as e:
    if 'timed out' in str(e):
```

## socketIO_client manual install

The `socketIO-client==0.5.7.2` package cannot be built by pip. Install manually:

```bash
python3 -c "
import requests, tarfile, io
r = requests.get('https://files.pythonhosted.org/packages/source/s/socketIO-client/socketIO-client-0.5.7.2.tar.gz')
open('/tmp/socketIO-client.tar.gz', 'wb').write(r.content)
"
cd /tmp && tar xzf socketIO-client.tar.gz
cp -r /tmp/socketIO-client-0.5.7.2/socketIO_client /home/azureuser/anaconda3/lib/python3.11/site-packages/
```
