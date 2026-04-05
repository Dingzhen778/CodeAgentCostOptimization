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
| `olsync/olsync.py` | `PySide6` not available on server | Made `olbrowserlogin` import optional with try/except |
| `socketIO_client/transports.py` | `websocket.SSLError` removed in new websocket-client | Replaced with `ssl.SSLError` + added `import ssl` |

### get_project_infos approach

Overleaf requires `?projectId=` in the Socket.IO v1 handshake URL (not just in the `joinProject` event). The response comes as a Socket.IO event (not ack):

```
5:::{"name":"joinProjectResponse","args":[{"project": {..., "rootFolder": [...]}, "publicId": "..."}]}
```

The `rootFolder[0]._id` for this project is `69b275a0cb82593435d6a1cf`.

## If sync breaks after a Python/package update

Re-apply the core patch to `get_project_infos` in:
`/home/azureuser/anaconda3/lib/python3.11/site-packages/olsync/olclient.py`

See `references/olclient-patch.md` for the full patched function.

## Workflow for thesis editing

1. Edit `.tex` files in `overleaf/paper/data/`
2. Run `ols --store-path ../.olauth -n "毕业论文___江润汉" -l` (local-only push)
3. Verify changes appear in Overleaf browser editor

To pull Overleaf edits back to server:
```bash
ols --store-path ../.olauth -n "毕业论文___江润汉" -r
```
