# mitmproxy_poomsae_addon.py
#
# Run with:
#   mitmdump -s mitmproxy_poomsae_addon.py -q          # headless (recommended)
#   mitmproxy -s mitmproxy_poomsae_addon.py            # interactive
#
# Configure your browser / OS proxy to 127.0.0.1:8080 (mitmproxy default).
#
# What this does:
#   1. Captures all WebSocket frames from TARGET_DOMAIN.
#   2. Strips the Socket.IO envelope ("42[...]").
#   3. Filters to the RECV ops the worker needs.
#   4. Deduplicates noisy poll responses (getAdminPair fires every ~3 s).
#   5. Wraps each message as  {"op":..., "d":{...}}  and sends it via
#      UDP to 127.0.0.1:FORWARD_PORT for PoomsaeFitofanWorker to receive.

import datetime
import json
import re
import socket as _socket
from mitmproxy import http

# ── Configuration ─────────────────────────────────────────────────────────────

TARGET_DOMAIN = "fitofan.com"
FORWARD_PORT  = 9997          # Must match PoomsaeFitofanListener.udp_port
LOG_FILE      = "poomsae_traffic.log"
LOG_ALL       = True          # Write every captured frame to LOG_FILE

# ── Ops to forward ────────────────────────────────────────────────────────────
# SENT ops are ignored (direction check below).
# Only RECV ops listed here reach the worker.
FORWARDED_OPS = {
    # Polled responses — deduplicated by pair_id in the addon
    "event.scoring.getAdminArea",
    "event.scoring.getAdminPair",

    # Real-time server-push events (no "event." prefix — different namespace)
    "scoringUpdateScoresData",
    "scoringUpdateTimerData",

    # Explicit action confirmations sent to ALL clients
    "event.scoring.startTime",
    "event.scoring.stopTime",
}

# ── Socket.IO frame parser ─────────────────────────────────────────────────────
# Engine.IO / Socket.IO v4 wraps payload as:  42["event_name", body_object]
# The leading "4" = EIO message packet, "2" = Socket.IO EVENT.
_SIO_RE = re.compile(r"^\d+(\[.*\])$", re.DOTALL)


def _parse_socketio(raw: str):
    """
    Returns (op, payload_dict) for Socket.IO event frames, else (None, None).
    Handles both namespaced ops:
      • "event.scoring.xxx"  →  body has "op" key
      • "scoringUpdateXxx"   →  event_name IS the op
    """
    m = _SIO_RE.match(raw.strip())
    if not m:
        return None, None
    try:
        parts = json.loads(m.group(1))
    except (json.JSONDecodeError, ValueError):
        return None, None

    if not isinstance(parts, list) or len(parts) < 2:
        return None, None

    event_name = parts[0]   # "action" (client) or "message" (server)
    body       = parts[1]   # the payload dict

    if not isinstance(body, dict):
        return None, None

    # Server "message" events carry op in body["op"]
    # Server-push events ("scoringUpdateXxx") use event_name as op
    op = body.get("op") or event_name
    d  = body.get("d", body)   # "d" key when present, else whole body
    return op, d


# ── mitmproxy Addon ────────────────────────────────────────────────────────────

class PoomsaeWebSocketMonitor:

    def __init__(self):
        self._udp = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
        # Deduplication: only forward getAdminPair when the active pair changes.
        self._last_pair_id    = None
        self._last_area_pair  = None   # active_pair_id seen in getAdminArea

    # ── mitmproxy hook ────────────────────────────────────────────────────────

    def websocket_message(self, flow: http.HTTPFlow):
        if TARGET_DOMAIN not in flow.request.pretty_host:
            return

        message   = flow.websocket.messages[-1]
        direction = "SENT" if message.from_client else "RECV"
        raw       = message.content.decode("utf-8", errors="ignore")
        ts        = datetime.datetime.now()

        if LOG_ALL:
            with open(LOG_FILE, "a") as f:
                f.write(f"[{ts}] {direction}: {raw}\n")

        # Ignore heartbeat frames (e.g. "2", "3") and client-sent ops
        if direction == "SENT":
            return

        op, d = _parse_socketio(raw)
        if op is None or op not in FORWARDED_OPS:
            return

        # ── Deduplication for polled responses ────────────────────────────────
        if op == "event.scoring.getAdminPair":
            pair = d.get("pair", {})
            pair_id = pair.get("id")
            if pair_id is not None and pair_id == self._last_pair_id:
                return  # same competitor, skip
            self._last_pair_id = pair_id
            print(f"[mitmproxy] New active pair: {pair_id}")

        elif op == "event.scoring.getAdminArea":
            area = d.get("area", {})
            active = area.get("active_pair_id")
            if active == self._last_area_pair:
                return  # area unchanged, skip
            self._last_area_pair = active
            print(f"[mitmproxy] Area active_pair_id changed: {active}")

        # ── Forward to worker via UDP ─────────────────────────────────────────
        envelope = json.dumps({"op": op, "d": d}, ensure_ascii=False)
        try:
            self._udp.sendto(envelope.encode("utf-8"), ("127.0.0.1", FORWARD_PORT))
            print(f"[{ts}] → worker  op={op!r}")
        except OSError as e:
            print(f"[mitmproxy] UDP send error: {e}")


addons = [PoomsaeWebSocketMonitor()]
