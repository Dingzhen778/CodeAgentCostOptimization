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

## 5. socketIO_client/transports.py: fix SSLError

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
