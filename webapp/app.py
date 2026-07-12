"""
app.py -- tarts the server.

    python -m pip install -r ../requirements.txt
    cd webapp && python app.py     # then open http://localhost:5000

Phone access (same network as laptop + Pis):
    1. Connect the laptop to the network.
    2. Find the laptop IP: run `ipconfig`, read the Wi-Fi IPv4 Address.
    3. Allow port 5000 (ADMIN PowerShell):
       netsh advfirewall firewall add rule name="TALOS 5000" dir=in action=allow protocol=TCP localport=5000
    4. On the phone browser: http://<laptop-ip>:5000  (http, keep the :5000)
"""

from flask import Flask
from flask_socketio import SocketIO

import config
from controller import Controller
import mqtt_client
import routes

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")


# Two callbacks:
def on_actuator(led, servo):
    mqtt_client.publish_actuator(led, servo)

def on_change(snapshot):
    socketio.emit("update", snapshot)          # push to laptop + phone
    mqtt_client.publish_state(snapshot["state"])

controller = Controller(on_actuator=on_actuator, on_change=on_change)

mqtt_client.init(controller)                   # sensors 
routes.init(app, socketio, controller)         # web UI


if __name__ == "__main__":
    mqtt_client.start()
    socketio.run(app, host="0.0.0.0", port=config.WEB_PORT)
