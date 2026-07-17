"""
mqtt_client.py -- client to connect the edge Pis.

Incoming: subscribes to home/sensor/# and forwards each event.
Outgoing: publishes actuator commands + retained system state.

If the broker isn't reachable, the app still runs in UI-only mode (the sim
buttons work) -- `enabled` just stays False.
"""

import json
import paho.mqtt.client as mqtt
import config

_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
_controller = None
enabled = False          # True once connected to the broker


def init(controller):
    """Wire the MQTT client to the brain. Called once at startup."""
    global _controller
    _controller = controller
    _client.on_connect = _on_connect
    _client.on_message = _on_message


def _on_connect(client, userdata, flags, reason_code, properties):
    print(f"[mqtt] connected rc={reason_code}")
    client.subscribe("home/sensor/#")


def _on_message(client, userdata, msg):
    kind = msg.topic.rsplit("/", 1)[-1]        # sound | motion
    try:
        payload = json.loads(msg.payload.decode())
    except (ValueError, UnicodeDecodeError):
        payload = {}
    if payload.get("triggered", True):
        _controller.on_sensor(kind)


# -- outgoing (called by the app when the brain changes actuators/state) ----
def publish_actuator(led, servo):
    if not enabled:
        return
    if led is not None:
        _client.publish(config.T_LED, json.dumps({"state": led}))
    if servo is not None:
        _client.publish(config.T_SERVO, json.dumps({"state": servo}))


def publish_state(state):
    if not enabled:
        return
    _client.publish(config.T_STATE, json.dumps({"state": state}), retain=True)


def start():
    global enabled
    try:
        _client.connect(config.BROKER_IP, config.BROKER_PORT, 60)
        _client.loop_start()
        enabled = True
        print(f"[mqtt] using broker at {config.BROKER_IP}")
    except OSError as e:
        print(f"[mqtt] no broker yet -> UI-only mode ({e})")
