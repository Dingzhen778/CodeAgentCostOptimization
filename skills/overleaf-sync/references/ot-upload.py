#!/usr/bin/env python3
"""
ot-upload.py — Upload / restore a local .tex file to Overleaf via Socket.IO OT.

Usage:
    python3 ot-upload.py <local_tex_path> <overleaf_doc_id>

Example:
    python3 ot-upload.py overleaf/paper/data/chap01.tex 69d28c9e092a95a9a60aa0cb

Prerequisites:
    pip install websocket-client requests
    .olauth file must exist at overleaf/.olauth  (see make_olauth.py)

How it works
------------
1. Reads the local .tex file as a UTF-8 string.
2. Connects to Overleaf via Socket.IO v1 WebSocket.
3. Issues joinProject → joinDoc to get the current doc state (version N).
4. Sends applyOtUpdate with op=[{'d': old, 'p':0}, {'i': new, 'p':0}]
   (or just [{'i': new, 'p':0}] if the doc is empty).
5. Stays connected ~40 s while sending heartbeats so Overleaf flushes the
   in-memory state to the persistent docstore before we disconnect.

Key protocol notes (hard-won)
------------------------------
- Messages MUST use  "5:N+::"  (the '+' after the sequence number).
  Without the '+', the server sends bare acks "6:::N" with NO data.
  With '+', the server sends "6:::N+[err, data, ...]".

- applyOtUpdate op format  (sharejs-text-ot with Overleaf's document-updater):
    { "i": "<text to insert>", "p": <char offset> }   ← insert
    { "d": "<text to delete>", "p": <char offset> }   ← delete (value = exact text, NOT a count!)

- The content stored by Overleaf is the Unicode string as received; Chinese / non-ASCII
  characters that were originally submitted as raw UTF-8 bytes-decoded-as-latin-1 will
  round-trip correctly as long as you use the exact string returned by joinDoc as the
  delete value.

- Stay connected at least 35 s after the OT ack, then send leaveDoc before closing.
  Disconnecting immediately discards the in-memory update without flushing.
"""

import pickle, requests, json, ssl, websocket, time, sys, os

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR    = '/home/azureuser/jrh/CodeAgentCostOptimization/overleaf'
OLAUTH_PATH = os.path.join(BASE_DIR, '.olauth')
PROJECT_ID  = '69b27599cb82593435d69eb7'
BASE_URL    = 'https://www.overleaf.com'
FLUSH_WAIT  = 38  # seconds to stay connected after OT ack


def upload_doc(local_path: str, doc_id: str):
    # ── Load auth ────────────────────────────────────────────────────────────
    with open(OLAUTH_PATH, 'rb') as f:
        store = pickle.load(f)
    cookie = store['cookie']
    cookie_str = 'GCLB={}; overleaf_session2={}'.format(
        cookie['GCLB'], cookie['overleaf_session2'])

    with open(local_path, 'r', encoding='utf-8') as f:
        new_content = f.read()
    print(f'[ot-upload] local file : {local_path}  ({len(new_content)} chars)')
    print(f'[ot-upload] target doc : {doc_id}')

    # ── WebSocket handshake ───────────────────────────────────────────────────
    t0 = int(time.time())
    r = requests.get(
        f'{BASE_URL}/socket.io/1/?t={t0}&projectId={PROJECT_ID}',
        headers={'Cookie': cookie_str}, timeout=10)
    sid = r.text.split(':')[0]

    ws = websocket.create_connection(
        f'wss://www.overleaf.com/socket.io/1/websocket/{sid}?t={t0}&projectId={PROJECT_ID}',
        header=[f'Cookie: {cookie_str}'],
        sslopt={'cert_reqs': ssl.CERT_NONE},
        timeout=15)
    ws.settimeout(5)

    step = 'init'
    ot_done = False
    ot_time = None

    try:
        for i in range(2000):
            # ── Stay-connected flush window ──────────────────────────────────
            if ot_done and time.time() - ot_time > FLUSH_WAIT:
                print('\n[ot-upload] flush window elapsed — sending leaveDoc')
                ws.send('5:99+::' + json.dumps({'name': 'leaveDoc', 'args': [doc_id]}))
                time.sleep(3)
                break

            # ── Recv ─────────────────────────────────────────────────────────
            try:
                msg = ws.recv()
            except websocket.WebSocketTimeoutException:
                ws.send('2::')            # heartbeat
                if ot_done:
                    elapsed = time.time() - ot_time
                    sys.stdout.write(f'\r[ot-upload] waiting for flush {elapsed:.0f}/{FLUSH_WAIT}s …')
                    sys.stdout.flush()
                continue
            except Exception as e:
                print(f'\n[ot-upload] recv error: {e}')
                break

            if msg == '2::':
                ws.send('2::')
                continue

            # ── Protocol state machine ───────────────────────────────────────
            if msg == '1::' and step == 'init':
                step = 'jp'
                ws.send('5:1+::' + json.dumps(
                    {'name': 'joinProject', 'args': [{'project_id': PROJECT_ID}]}))

            elif ('rootFolder' in msg or 'joinProjectResponse' in msg) and step == 'jp':
                step = 'jd'
                ws.send('5:2+::' + json.dumps(
                    {'name': 'joinDoc', 'args': [doc_id, {'encodeRanges': True}]}))
                print('[ot-upload] joinDoc sent')

            elif msg.startswith('6:::2+') and step == 'jd':
                data = json.loads(msg[6:])
                if data[0]:
                    raise RuntimeError(f'joinDoc error: {data[0]}')
                cur_lines = data[1]
                version   = data[2]
                cur       = '\n'.join(cur_lines)
                print(f'[ot-upload] joinDoc OK  version={version}  existing={len(cur)} chars')

                # Build op: delete existing content, insert new content
                #
                # KEY ENCODING INSIGHT (hard-won):
                # Overleaf's document-updater stores documents as real Unicode strings internally.
                # joinDoc returns the content as mojibake (UTF-8 bytes decoded as Latin-1 chars,
                # e.g. 实 → U+00E5 U+00AE U+009E).
                # To delete, we must send the REAL UTF-8 decoded version of cur (not the mojibake).
                # Similarly, insert new_content as real UTF-8.
                # Both must use ensure_ascii=False in json.dumps so Unicode chars stay as-is.
                try:
                    delete_str = cur.encode('latin-1').decode('utf-8')
                except (UnicodeDecodeError, UnicodeEncodeError):
                    delete_str = cur  # fallback: use as-is if not mojibake

                ops = []
                if delete_str:
                    ops.append({'d': delete_str, 'p': 0})
                ops.append({'i': new_content, 'p': 0})

                ws.send('5:3+::' + json.dumps({
                    'name': 'applyOtUpdate',
                    'args': [doc_id, {'op': ops, 'v': version, 'meta': {'source': 'claude-code'}}]
                }, ensure_ascii=False))
                print(f'[ot-upload] applyOtUpdate sent  '
                      f'del={len(cur)}  ins={len(new_content)}')
                ot_time = time.time()
                step = 'ot'

            elif msg.startswith('6:::3') and step == 'ot':
                print(f'\n[ot-upload] OT ack received  ({repr(msg)})')
                ot_done = True
                ot_time = time.time()
                step = 'staying'

            elif 'otUpdateError' in msg:
                raise RuntimeError(f'OT error from server: {msg[:400]}')

            elif 'otUpdateApplied' in msg:
                print(f'\n[ot-upload] otUpdateApplied event received')

    finally:
        try:
            ws.close()
        except Exception:
            pass

    if not ot_done:
        raise RuntimeError('OT update was not confirmed — doc may not have been updated.')

    print(f'\n[ot-upload] Done.  doc_id={doc_id}')
    return doc_id


def verify_doc(doc_id: str, cookie_str: str):
    """Re-join the doc and print its current state for confirmation."""
    t1 = int(time.time())
    r = requests.get(
        f'{BASE_URL}/socket.io/1/?t={t1}&projectId={PROJECT_ID}',
        headers={'Cookie': cookie_str}, timeout=10)
    sid = r.text.split(':')[0]
    ws = websocket.create_connection(
        f'wss://www.overleaf.com/socket.io/1/websocket/{sid}?t={t1}&projectId={PROJECT_ID}',
        header=[f'Cookie: {cookie_str}'],
        sslopt={'cert_reqs': ssl.CERT_NONE}, timeout=15)
    try:
        for _ in range(60):
            try: msg = ws.recv()
            except: break
            if msg == '2::': ws.send('2::'); continue
            if msg == '1::':
                ws.send('5:1+::' + json.dumps(
                    {'name': 'joinProject', 'args': [{'project_id': PROJECT_ID}]}))
            elif 'rootFolder' in msg or 'joinProjectResponse' in msg:
                ws.send('5:2+::' + json.dumps(
                    {'name': 'joinDoc', 'args': [doc_id, {'encodeRanges': True}]}))
            elif msg.startswith('6:::2+'):
                d = json.loads(msg[6:])
                if d[0]:
                    print(f'[verify] error: {d[0]}')
                else:
                    c = '\n'.join(d[1])
                    print(f'[verify] version={d[2]}  lines={len(d[1])}  chars={len(c)}')
                    print(f'[verify] first 120 chars: {c[:120]}')
                break
    finally:
        try: ws.close()
        except: pass


# ── CLI entry point ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    local_path = sys.argv[1]
    doc_id     = sys.argv[2]

    with open(OLAUTH_PATH, 'rb') as f:
        store = pickle.load(f)
    cookie = store['cookie']
    cookie_str = 'GCLB={}; overleaf_session2={}'.format(
        cookie['GCLB'], cookie['overleaf_session2'])

    upload_doc(local_path, doc_id)
    print('\n[ot-upload] Verifying ...')
    time.sleep(3)
    verify_doc(doc_id, cookie_str)
