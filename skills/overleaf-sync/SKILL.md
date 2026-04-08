---
name: overleaf-sync
description: Use when the user wants to sync the local thesis files with Overleaf, push edits to Overleaf, pull remote changes, refresh expired cookies, or troubleshoot the ols sync tool.
---

# Overleaf Sync Skill

Use this skill whenever the task is to sync `overleaf/paper/` with the Overleaf project, check sync status, or fix authentication issues.

## Key paths

- Local thesis files: `overleaf/paper/`
- Auth file: `overleaf/.olauth`
- Cookie helper script: `overleaf/make_olauth.py`
- Overleaf project name: `毕业论文___江润汉`
- Overleaf project ID: `69b27599cb82593435d69eb7`

## Sync command

```bash
cd /home/azureuser/jrh/CodeAgentCostOptimization/overleaf/paper
ols --store-path ../.olauth -n "毕业论文___江润汉"
```

Flags:
- `-l` / `--local-only`: push local → Overleaf only
- `-r` / `--remote-only`: pull Overleaf → local only
- `-v`: verbose error output

## Authentication

The `.olauth` file stores the session cookie as a pickle. It expires when the Overleaf session expires (typically days to weeks).

### To refresh expired cookies

1. Open https://www.overleaf.com in a browser and log in
2. F12 → Application → Cookies → `https://www.overleaf.com`
3. Copy `overleaf_session2` and `GCLB` values
4. In the Console tab, run: `document.getElementsByName('ol-csrfToken')[0].content`
5. Edit `overleaf/make_olauth.py` — fill in the three variables
6. Run: `python overleaf/make_olauth.py`

### To verify auth is working

```bash
ols list --store-path overleaf/.olauth
```

## Compatibility fixes applied

The stock `overleaf-sync==1.2.0` package needed several patches to work with the current Overleaf SaaS. All patches are already applied to the system Python packages.

### Summary of patches

| File | Problem | Fix |
|------|---------|-----|
| `olsync/olclient.py` | `socketIO_client` package uninstallable | Manually extracted to site-packages; replaced SocketIO call with direct `websocket.create_connection` |
| `olsync/olclient.py` | `ol-projects` meta tag renamed | Added `_get_projects_json()` helper checking `ol-prefetchedProjectsBlob` first |
| `olsync/olclient.py` | `get_project_infos` hangs | Rewrote using Socket.IO v1 WebSocket with `projectId` in handshake URL |
| `olsync/olclient.py` | `upload_file` for text docs empties files | Replaced delete+REST-create with delete+REST-create-shell+OT-write (see below) |
| `olsync/olsync.py` | `PySide6` not available on server | Made `olbrowserlogin` import optional with try/except |
| `socketIO_client/transports.py` | `websocket.SSLError` removed in new websocket-client | Replaced with `ssl.SSLError` + added `import ssl` |

### get_project_infos approach

Overleaf requires `?projectId=` in the Socket.IO v1 handshake URL (not just in the `joinProject` event). The response comes as a Socket.IO event (not ack):

```
5:::{"name":"joinProjectResponse","args":[{"project": {..., "rootFolder": [...]}, "publicId": "..."}]}
```

The `rootFolder[0]._id` for this project is `69b275a0cb82593435d6a1cf`.

---

## Socket.IO OT Upload Protocol (Critical)

### Why REST upload fails for text files

`POST /project/{id}/doc` only creates a **file-tree entry** — it does NOT initialise the
docstore backend. The doc appears in the editor but is always empty.
The only correct way to write content into a doc is via the Socket.IO **Operational Transform** (OT) API.

### Standalone restore/upload script

```
references/ot-upload.py
```

Usage:
```bash
python3 skills/overleaf-sync/references/ot-upload.py \
    overleaf/paper/data/chap01.tex \
    <overleaf_doc_id>
```

Get the `doc_id` from the `joinProjectResponse` rootFolder tree (logged by `ot-upload.py`
itself if you run it with the wrong ID) or from a prior `get_project_infos` call.

**Known doc IDs for this project**

| File | Doc ID |
|------|--------|
| `data/chap01.tex` | `69d3690f05cfc68b0a48a890` |
| `data/chap02.tex` | `69d3693cda3926239162c627` |
| `data/chap03.tex` | `69d398cf40ac3f149abf7bd3` |
| `data/chap04.tex` | `69b27599cb82593435d69f23` |
| `data/chap05.tex` | `69b27599cb82593435d69f24` |
| `data/chap06.tex` | `69b27599cb82593435d69f25` |
| `data/chap07.tex` | `69b27599cb82593435d69f26` |
| `data/abstract.tex` | `69b27599cb82593435d69f01` |
| `main.tex` | `69b2759ecb82593435d6a12e` |

### Protocol rules (hard-won)

| Detail | ❌ Wrong | ✅ Correct |
|--------|---------|---------|
| Message format | `5:N::` | `5:N+::` — `+` requests a data-bearing ack |
| `applyOtUpdate` delete | `{'d': N}` (integer count) | `{'d': "<exact text>", 'p': 0}` (actual string) |
| `applyOtUpdate` insert | `{'i': text}` | `{'i': text, 'p': 0}` — `p` (position) is required |
| Connection lifetime | Close immediately after OT ack | Stay **≥ 35 s**, send `leaveDoc`, then close |

### Minimal upload sequence

```python
# 1. Create empty doc shell via REST (gives doc_id; docstore initialised but empty)
r = requests.post(f'{BASE_URL}/project/{project_id}/doc',
    cookies=cookie, headers={'X-Csrf-Token': csrf},
    json={'name': 'chap01.tex', 'parent_folder_id': folder_id, 'lines': []})
doc_id = r.json()['_id']

# 2. WebSocket handshake (projectId in URL is mandatory)
r = requests.get(f'{BASE_URL}/socket.io/1/?t={t}&projectId={project_id}', ...)
sid = r.text.split(':')[0]
ws = websocket.create_connection(
    f'wss://www.overleaf.com/socket.io/1/websocket/{sid}?t={t}&projectId={project_id}', ...)
ws.settimeout(5)

# 3. State machine: joinProject → joinDoc → applyOtUpdate
#    NOTE: '5:N+::' format required throughout
ws.send('5:1+::' + json.dumps({'name': 'joinProject', 'args': [{'project_id': project_id}]}))
# ... on joinProjectResponse:
ws.send('5:2+::' + json.dumps({'name': 'joinDoc', 'args': [doc_id, {'encodeRanges': True}]}))
# ... on '6:::2+[null, lines, version, ...]':
ops = [{'i': new_content, 'p': 0}]          # doc is empty, so just insert
ws.send('5:3+::' + json.dumps({'name': 'applyOtUpdate',
    'args': [doc_id, {'op': ops, 'v': version, 'meta': {'source': 'claude-code'}}]}))

# 4. After '6:::3' ack → stay connected ~38 s (heartbeat every 5 s), then:
ws.send('5:99+::' + json.dumps({'name': 'leaveDoc', 'args': [doc_id]}))
time.sleep(3)
ws.close()
```

### Updating an existing doc (non-empty)

The delete component `'d'` must be the **exact string** returned by the prior `joinDoc` call.
Read current content first, then build the op:

```python
# cur = '\n'.join(lines_from_joinDoc)
ops = [{'d': cur, 'p': 0}, {'i': new_content, 'p': 0}]
```

If `cur` encodes non-ASCII as raw UTF-8 bytes-as-Latin-1 chars (visible as mojibake),
pass that mojibake string verbatim as `'d'` — do **not** re-encode it.

---

## If sync breaks after a Python/package update

Re-apply the patches documented in `references/olclient-patch.md` to:
`/home/azureuser/anaconda3/lib/python3.11/site-packages/olsync/olclient.py`

---

## Workflow for thesis editing

1. Edit `.tex` files in `overleaf/paper/data/`
2. Run `ols --store-path ../.olauth -n "毕业论文___江润汉" -l` (local-only push)
3. Verify changes appear in Overleaf browser editor

To pull Overleaf edits back to server:
```bash
ols --store-path ../.olauth -n "毕业论文___江润汉" -r
```

### If `ols` corrupts / empties a tex file on Overleaf

This happens because `ols` still calls the buggy REST `upload_file`.
Use the standalone OT script directly:

```bash
python3 skills/overleaf-sync/references/ot-upload.py \
    overleaf/paper/data/chap01.tex \
    69d28c9e092a95a9a60aa0cb
```

The script will delete the old doc, create a fresh shell, upload via OT, and verify.
