import json
import re
from mitmproxy import ctx

def websocket_message(flow):
    # print(flow.websocket.messages[4], "bbb")
    # print(flow.websocket.messages[6], "bbb")
    # print(flow.websocket.messages[10], "bbb")
    print(flow.websocket.messages[14], "bbb")
    print("")
    print("")
    print("")
    print("")
    print("")
    # 1. FIX: Get the request from the initial handshake
    if not hasattr(flow, "handshake_flow") or not flow.handshake_flow:
        return

    request = flow.handshake_flow.request

    # Filter for Fitofan and Socket.io
    if not request.host.endswith("fitofan.com"):
        return

    if "/socket.io/" not in request.path:
        return

    # 2. FIX: Just grab the latest message (it's always at the end of the list)
    if not flow.messages:
        return
        
    message = flow.messages[-1]

    # Ignore messages sent by the client (we only want server responses)
    if message.from_client or not message.is_text:
        return

    raw_text = message.text

    # Use ctx.log.info so it cleanly outputs to the mitmweb console
    ctx.log.info(f"📡 RAW: {raw_text[:150]}...")

    # 3. Handle the Socket.io '42' prefix
    match = re.match(r'^42(.*)', raw_text)
    if not match:
        return

    try:
        data = json.loads(match.group(1))

        # Ensure it matches the ["action", { payload }] array format
        if isinstance(data, list) and len(data) >= 2:
            payload = data[1]
            op = payload.get("op", "")

            # Filter for scoring events
            if op.startswith("event.scoring"):
                ctx.log.info(f"🔥 EVENT MATCHED: {op}")

    except json.JSONDecodeError:
        # Ignore failed JSON parses quietly
        pass
    except Exception as e:
        ctx.log.error(f"❌ ERROR: {e}")