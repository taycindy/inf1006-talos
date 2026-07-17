"""
controller.py -- pure logic: the DISARMED/ARMED/LOCKDOWN state machine.

Flow:
    owner arms the system  -> ARMED
    sound OR motion fires  -> LOCKDOWN (LED on + servo locks, intruder blocked)
    owner disarms (webapp) -> DISARMED (LED off + servo unlocks)

Events come in through two methods:
    on_sensor("sound"|"motion")     # from the Pis OR the sim buttons
    command("arm"|"disarm"|...)     # from the web UI

Two callbacks:
    on_actuator(led, servo)   # "please turn the LED/servo to this state"
    on_change(snapshot)       # "state changed, here's the current picture"
"""

import time
import threading


class Controller:
    def __init__(self, on_actuator=None, on_change=None):
        self.state = "DISARMED"
        self.led = "off"
        self.door = "unlocked"
        self.log = []
        self._on_actuator = on_actuator or (lambda led, servo: None)
        self._on_change = on_change or (lambda snapshot: None)
        self._lock = threading.Lock()

    # -- internal helpers ---------------------------------------------------
    def _apply(self, led=None, servo=None):
        if led is not None:
            self.led = led
        if servo is not None:
            self.door = servo
        self._on_actuator(led, servo)

    def _emit(self, note):
        entry = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "text": note}
        self.log.insert(0, entry)
        self.log = self.log[:50]
        self._on_change({"state": self.state, "led": self.led,
                         "door": self.door, "entry": entry})

    def _set(self, new_state, led=None, servo=None, note=""):
        self.state = new_state
        self._apply(led=led, servo=servo)
        self._emit(note or new_state)

    # -- automatic transitions (real sensors OR sim buttons) ----------------
    def on_sensor(self, kind):
        with self._lock:
            # either sensor is enough: light up AND lock the door
            if kind in ("sound", "motion") and self.state == "ARMED":
                self._set("LOCKDOWN", led="on", servo="locked",
                          note=f"{kind.capitalize()} detected -> lockdown")

    # -- manual commands (web UI) -------------------------------------------
    def command(self, cmd):
        with self._lock:
            if cmd == "arm" and self.state == "DISARMED":
                self._set("ARMED", led="off", servo="unlocked", note="Armed")
            elif cmd in ("disarm", "reset"):
                self._set("DISARMED", led="off", servo="unlocked",
                          note="Manually disarmed")
            elif cmd == "led_on":
                self._apply(led="on");  self._emit("Manual LED on")
            elif cmd == "led_off":
                self._apply(led="off"); self._emit("Manual LED off")
            elif cmd == "lock":
                self._apply(servo="locked");   self._emit("Manual lock")
            elif cmd == "unlock":
                self._apply(servo="unlocked"); self._emit("Manual unlock")
            else:
                return False
            return True