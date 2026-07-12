"""
routes.py -- the web API. Serves the page and exposes endpoints the frontend
calls. Both /sim and /cmd funnel into the same brain the Pis will use.
"""

from flask import jsonify, render_template
import mqtt_client


def init(app, socketio, controller):

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/status")
    def status():
        return jsonify(state=controller.state, led=controller.led,
                       door=controller.door, log=controller.log,
                       mqtt=mqtt_client.enabled)

    @app.route("/cmd/<name>", methods=["POST"])
    def cmd(name):
        ok = controller.command(name)
        return jsonify(ok=ok, state=controller.state), (200 if ok else 400)

    @app.route("/sim/<kind>", methods=["POST"])
    def sim(kind):
        controller.on_sensor(kind)
        return jsonify(ok=True, state=controller.state)
