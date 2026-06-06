# app/listeners/poomsae_fitofan_worker.py
import json
import socket
from PyQt5.QtCore import QObject
from app.injector import Injector
from app.main_manager import MainManager

# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------
INIT_STATE       = "init"        # No competitor loaded
READY_STATE      = "ready"       # Competitor on mat, waiting for gong
PERFORMING_STATE = "performing"  # Timer running (gong fired)
PAUSED_STATE     = "paused"      # Timer stopped mid-performance
SCORED_STATE     = "scored"      # Performance over, final scores visible

# Program IDs used by fitofan poomsae scoring
PROG_ACCURACY     = 1   # max 4.0 per judge
PROG_PRESENTATION = 2   # max 6.0 per judge (3 sub-programs × 2.0)


class PoomsaeFitofanWorker(QObject):
    """
    Receives UDP datagrams forwarded by mitmproxy_poomsae_addon.py,
    parses the fitofan poomsae scoring protocol and drives hub signals.

    ── Op mapping (all RECV, server → client) ──────────────────────────────
    event.scoring.getAdminArea    Bootstrap / area state (sent once on change)
    event.scoring.getAdminPair    Competitor info        (sent once on pair change)
    scoringUpdateScoresData       Live score push        (no "event." prefix)
    scoringUpdateTimerData        Live timer push        (no "event." prefix)
    event.scoring.startTime       Timer started (gong)
    event.scoring.stopTime        Timer paused

    ── Score structure (finalResults) ──────────────────────────────────────
    finalResults[round_str][sp_id_str] = {
        judgesPrograms:    [{r, p, j, s}]   p=1 Accuracy, p=2 Presentation
        judgesSubprograms: [{r, p, j, s}]   p=3 Acc, p=4/5/6 Pres sub-programs
        totalPrograms:     [{p, s}]          sum across all judges (before cutoff)
        avgPrograms:       [{p, s}]          average (after cutoff: drop min+max)
        minJudges / maxJudges               judges dropped by cutoff
        finalScore:        float             official round score
        deduction:         float
    }

    ── Notes on scoringUpdateScoresData ────────────────────────────────────
    The message may contain BOTH pairData (full) and pairPartial (delta) at
    the same time — pairPartial does NOT mean pairData is absent.
    Always read pairData if present; only skip if pairData is missing entirely.
    """

    def __init__(self, port: int):
        super().__init__()
        self.port        = port
        self._is_running = False
        self.udp_socket  = None
        self.hub: MainManager = Injector.find(MainManager)

        self.reset_data()

        self.flags = {
            "event.scoring.getAdminArea": self.on_admin_area,
            "event.scoring.getAdminPair": self.on_admin_pair,
            "scoringUpdateScoresData":    self.on_scores_update,
            "scoringUpdateTimerData":     self.on_timer_update,
            "event.scoring.startTime":    self.on_start_time,
            "event.scoring.stopTime":     self.on_stop_time,
        }

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start_listener(self):
        self._is_running = True
        self.udp_socket  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.udp_socket.bind(("127.0.0.1", self.port))
            print(f"[Poomsae Worker] Listening on 127.0.0.1:{self.port}")
        except OSError as e:
            print(f"[Poomsae Worker] FATAL: cannot bind port {self.port}: {e}")
            self._is_running = False
            return

        while self._is_running:
            try:
                self.udp_socket.settimeout(1.0)
                data, addr = self.udp_socket.recvfrom(65535)
                raw = data.decode("utf-8", errors="ignore").strip()
                if raw:
                    self.hub.listener_log.emit(f"[poomsae] {raw[:120]}")
                    self._dispatch(raw)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[Poomsae Worker] Error: {e}")

        if self.udp_socket:
            self.udp_socket.close()
        print("[Poomsae Worker] Stopped.")

    def stop_listener(self):
        self._is_running = False

    # ── Dispatch ──────────────────────────────────────────────────────────────

    def _dispatch(self, raw: str):
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return
        op = msg.get("op", "")
        d  = msg.get("d", {})
        handler = self.flags.get(op)
        if handler:
            handler(d)
        else:
            print(f"[Poomsae Worker] Unhandled op: {op!r}")

    # ── Handlers ──────────────────────────────────────────────────────────────

    def on_admin_area(self, d: dict):
        print(f"[Poomsae] on_admin_area")
        """
        Bootstrap — emitted by the addon only when active_pair_id changes.
        Stores event/area metadata; does NOT reset competitor data
        (getAdminPair arrives immediately after and handles the reset).
        """
        event = d.get("event", {})
        area  = d.get("area", {})

        self.data["event_id"]       = event.get("id", 0)
        self.data["event_title"]    = event.get("title", "")
        self.data["area_id"]        = area.get("id", 0)
        self.data["area_token"]     = area.get("token", "")
        self.data["solo_time"]      = area.get("solo_time", 60)
        self.data["active_pair_id"] = area.get("active_pair_id", 0)
        self.emit_stable_update()

    def on_admin_pair(self, d: dict):
        print(f"[Poomsae] on_admin_pair")
        """
        New competitor loaded onto the mat.
        Resets scoring state and emits new_fight_signal.
        """
        if not d.get("success", True):
            return

        pair    = d.get("pair", {})
        pair_id = pair.get("id", 0)

        # # Guard: ignore repeated polls for the same pair
        # if pair_id == self.data.get("pair_id") and self.data["state"] != INIT_STATE:
        #     return

        self.reset_data()

        user1    = pair.get("user1", {})
        user     = user1.get("user", {})
        org      = user1.get("org", {})
        settings = pair.get("settings", {})
        pdata    = pair.get("data", {})

        self.data.update({
            "pair_id":         pair_id,
            "pair_number":     pair.get("number", 0),
            "category":        pair.get("fullTitle", ""),
            "is_team":         bool(pair.get("is_team", 0)),
            "competitor_name": f"{user.get('name','')} {user.get('surname','')}".strip(),
            "club":            org.get("title", ""),
            "flag2":           org.get("country_code", "un").lower(),
            "country_code":    org.get("country_code", ""),
            "state":           READY_STATE,
        })

        self.data["num_judges"] = settings.get("judges", 5)
        self.data["num_rounds"] = settings.get("rounds", 2)
        self.data["round_time"] = settings.get("roundTime", 90)
        self.data["cutoff"]     = settings.get("programParams", {}).get("cutoff", True)

        self.data["rounds"] = [
            self._empty_round(r + 1)
            for r in range(self.data["num_rounds"])
        ]

        # Seed existing scores when proxying into an in-progress session
        final_results = pdata.get("finalResults", {})
        sp_id_str     = str(pair.get("sp1_id", ""))
        for r_str, sp_dict in final_results.items():
            sp_data = sp_dict.get(sp_id_str, {})
            if sp_data:
                r_idx = int(r_str) - 1
                if 0 <= r_idx < len(self.data["rounds"]):
                    self._apply_final_result(r_idx, sp_data)

        print(f"[Poomsae] Pair {pair_id}: {self.data['competitor_name']}  "
              f"({self.data['category']})")

        self.emit_stable_update()
        self.hub.new_fight_signal.emit()

    def on_scores_update(self, d: dict):
        print(f"[Poomsae] on_scores_update")
        """
        scoringUpdateScoresData — real-time score push from server.

        IMPORTANT: A message may contain BOTH pairData (full state) and
        pairPartial (delta) at the same time.  pairPartial is NOT a signal
        to skip processing.  Always read pairData when it is present.

        Scores arrive incrementally DURING the performance (one judge at a
        time).  Do NOT change state to SCORED here — that transition is
        driven by the timer stopping (on_timer_update / on_stop_time) after
        all judges have confirmed.

        Timer state (is_pause in pairData) tells us whether the round is
        live.  We use it here only to trigger start_fight_signal if we
        somehow missed the startTime op.
        """
        scores_data = d.get("scoresData", {})
        pair_data   = scores_data.get("pairData")

        # Skip only when there is genuinely no pairData at all
        if not pair_data:
            return

        # ── Resolve sp_id (competitor) from finalResults ──────────────────────
        final_results = pair_data.get("finalResults", {})
        sp_id_str = None
        for r_str, sp_dict in final_results.items():
            if sp_dict:
                sp_id_str = next(iter(sp_dict), None)
                break

        if not sp_id_str:
            return

        # ── Apply per-round scores ─────────────────────────────────────────────
        for r_str, sp_dict in final_results.items():
            sp_data = sp_dict.get(sp_id_str)
            if not sp_data:
                continue
            r_idx = int(r_str) - 1
            while len(self.data["rounds"]) <= r_idx:
                self.data["rounds"].append(self._empty_round(r_idx + 1))
            self._apply_final_result(r_idx, sp_data)

        # ── Running total ─────────────────────────────────────────────────────
        comp_scores = scores_data.get("competitorsScores", {})
        if comp_scores:
            self.data["total_score"] = float(comp_scores.get("score_one", 0))

        # ── Catch missed start signal ─────────────────────────────────────────
        # If the timer is running but we are still in READY state we missed
        # the startTime op (e.g. listener started after gong).
        # is_paused = bool(pair_data.get("is_pause", 1))
        # if not is_paused and self.data["state"] == READY_STATE:
        #     self.data["state"] = PERFORMING_STATE
        #     self.hub.start_fight_signal.emit()

        self.emit_stable_update()

    def on_timer_update(self, d: dict):
        print(f"[Poomsae] on_timer_update")
        """
        scoringUpdateTimerData — real-time timer tick.

        Fields:
          timerData.timeLeft   int   milliseconds remaining
          timerData.isPause    bool  True = paused / stopped
          timerData.round_id   int   current round (1-based)
          timerData.forceGong  bool  True = gong just fired
        """
        timer = d.get("timerData", d)

        time_left_ms = timer.get("timeLeft", 0)
        is_pause     = timer.get("isPause", True)
        round_id     = timer.get("round_id", 1)
        force_gong   = timer.get("forceGong", False)

        total_secs             = max(0, int(time_left_ms / 1000))
        self.data["clk"]       = f"{total_secs // 60}:{total_secs % 60:02d}"
        self.data["current_round"] = round_id

        # if force_gong:
        #     if self.data["state"] in [READY_STATE, PAUSED_STATE]:
        #         self.data["state"] = PERFORMING_STATE
        #         self.hub.start_fight_signal.emit()
        #         self.emit_stable_update()
        #         self.hub.start_round_signal.emit()

        # elif not is_pause and self.data["state"] == READY_STATE:
        #     self.data["state"] = PERFORMING_STATE
        #     self.hub.start_fight_signal.emit()
        #     self.emit_stable_update()

        # elif is_pause and self.data["state"] == PERFORMING_STATE:
        #     self.data["state"] = PAUSED_STATE
        #     self.emit_stable_update()

        self.emit_stable_update()

        # self.hub.listener_fast_signal.emit({"event": "clock", "data": {"clk": self.data["clk"]}})

    def on_start_time(self, d: dict):
        print(f"[Poomsae] on_start_time")
        """Fallback — timer-start confirmation echoed to all clients."""
        self.emit_stable_update()
        self.hub.start_round_signal.emit()
        # if self.data["state"] in [READY_STATE, PAUSED_STATE]:
        #     self.data["state"] = PERFORMING_STATE
        #     self.hub.start_fight_signal.emit()

    def on_stop_time(self, d: dict):
        print(f"[Poomsae] on_stop_time")
        """
        Timer stopped — transition to SCORED if the current round has a
        non-zero finalScore, otherwise to PAUSED (mid-performance stop).
        """
        current_r   = self.data.get("current_round", 1) - 1
        rounds      = self.data.get("rounds", [])
        round_done  = (
            0 <= current_r < len(rounds)
            and rounds[current_r]["final_score"] > 0
        )

        self.emit_stable_update()
        self.hub.start_break_signal.emit()
        # if self.data["state"] == PERFORMING_STATE:
        #     self.data["state"] = SCORED_STATE if round_done else PAUSED_STATE
        #     self.emit_stable_update()
        #     if round_done:
        #         self.hub.win_signal.emit()

    # ── Score helpers ─────────────────────────────────────────────────────────

    def _apply_final_result(self, r_idx: int, sp_data: dict):
        """Merge finalResults[r][sp] into self.data['rounds'][r_idx]."""
        rnd = self.data["rounds"][r_idx]

        rnd["final_score"] = float(sp_data.get("finalScore", 0))
        rnd["deduction"]   = float(sp_data.get("deduction", 0))

        for entry in sp_data.get("totalPrograms", []):
            if entry["p"] == PROG_ACCURACY:
                rnd["total_accuracy"]     = float(entry["s"])
            elif entry["p"] == PROG_PRESENTATION:
                rnd["total_presentation"] = float(entry["s"])

        for entry in sp_data.get("avgPrograms", []):
            if entry["p"] == PROG_ACCURACY:
                rnd["avg_accuracy"]     = float(entry["s"])
            elif entry["p"] == PROG_PRESENTATION:
                rnd["avg_presentation"] = float(entry["s"])

        rnd["min_judges"] = {e["p"]: e["j"] for e in sp_data.get("minJudges", [])}
        rnd["max_judges"] = {e["p"]: e["j"] for e in sp_data.get("maxJudges", [])}

        judges_map = {}
        for entry in sp_data.get("judgesPrograms", []):
            j = entry["j"]
            if j not in judges_map:
                judges_map[j] = {"accuracy": 0.0, "presentation": 0.0}
            if entry["p"] == PROG_ACCURACY:
                judges_map[j]["accuracy"] = float(entry["s"])
            elif entry["p"] == PROG_PRESENTATION:
                judges_map[j]["presentation"] = float(entry["s"])

        rnd["judges"] = [
            {
                "judge":        j,
                "accuracy":     vals["accuracy"],
                "presentation": vals["presentation"],
                "total":        round(vals["accuracy"] + vals["presentation"], 3),
                "is_min":       self._judge_dropped(j, rnd["min_judges"]),
                "is_max":       self._judge_dropped(j, rnd["max_judges"]),
            }
            for j, vals in sorted(judges_map.items())
        ]

    @staticmethod
    def _judge_dropped(j: int, dropped: dict) -> bool:
        return j in dropped.values()

    # ── Emitters ──────────────────────────────────────────────────────────────

    def emit_stable_update(self):
        self.hub.listener_stable_signal.emit({"event": "update", "data": self.data})

    # ── Reset ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _empty_round(r: int) -> dict:
        return {
            "round":              r,
            "final_score":        0.0,
            "deduction":          0.0,
            "total_accuracy":     0.0,
            "total_presentation": 0.0,
            "avg_accuracy":       0.0,
            "avg_presentation":   0.0,
            "min_judges":         {},
            "max_judges":         {},
            "judges":             [],
        }

    def reset_data(self):
        self.data = {
            "event_id":       0,
            "event_title":    "",
            "area_id":        0,
            "area_token":     "",
            "solo_time":      60,
            "active_pair_id": 0,

            "state":           INIT_STATE,
            "pair_id":         0,
            "pair_number":     0,
            "category":        "",
            "is_team":         False,
            "competitor_name": "",
            "club":            "",
            "flag2":           "",
            "country_code":    "",

            "num_judges":  5,
            "num_rounds":  2,
            "round_time":  90,
            "cutoff":      True,

            "current_round": 1,
            "clk":           "01:30",
            "total_score":   0.0,

            "rounds": [],
        }