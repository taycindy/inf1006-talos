# TALOS -- Home Security System (Web App)

Web control panel for a smart-home security system.

## System overview

The owner arms the system when leaving the house. If an intruder comes in
range, either the sound sensor or the motion sensor is enough to trigger the
response: the LED lights up and the servo locks the door, so the
intruder cannot get in. The owner disarms from the web app to stand the system
down -- LED off, door unlocked.

## Network layout

```
                 Router (WiFi)
                /      |       \
        Sensor Pi   Broker Pi   Output Pi        + laptop (runs this web app)
        sound,      Mosquitto   LED, servo         & phone (view the panel)
        motion      10.67.110.169
```

- **Sensor Pi** -- sound + motion sensors (publishes events)
- **Broker Pi** -- Mosquitto at `10.67.110.169` (relays all MQTT traffic)
- **Output Pi** -- LED + servo lock (subscribes to commands)
- **Laptop** -- runs this web app; it's the brain that turns a sensor event
  into an actuator command. Everything routes through the broker -- the app
  only ever connects to the broker, never to the Pis directly.
- **Phone** -- views the control panel over the same WiFi

All four devices must be on the same network as the broker.

## Structure

```
inf1006-talos/
├── webapp/
│   ├── app.py            # run this
│   ├── controller.py     # the brain: DISARMED/ARMED/LOCKDOWN
│   ├── routes.py         # web API + WebSocket
│   ├── mqtt_client.py    # where the Pis connect in over MQTT
│   ├── config.py         # broker IP + MQTT topic names
│   └── templates/index.html
├── requirements.txt
└── README.md
```

## Run

```
python -m pip install -r requirements.txt
cd webapp
python app.py            # open http://localhost:5000
```

### Phone access
Laptop + phone share the same WiFi as the broker.
1. `ipconfig` -> note the Wi-Fi IPv4 Address (should start with the same numbers
   as the broker).
2. Allow the port (ADMIN PowerShell):
   `netsh advfirewall firewall add rule name="TALOS 5000" dir=in action=allow protocol=TCP localport=5000`
3. Phone browser: `http://<laptop-ip>:5000`

## Interface

The web app is already listening on these topics. Match these names and payloads
exactly and integration is automatic.

| Topic                 | Who publishes      | Payload                          |
|-----------------------|--------------------|----------------------------------|
| `home/sensor/sound`   | Sensor Pi          | `{"triggered": true}`            |
| `home/sensor/motion`  | Sensor Pi          | `{"triggered": true}`            |
| `home/actuator/led`   | webapp             | `{"state": "on"|"off"}`          |
| `home/actuator/servo` | webapp             | `{"state": "locked"|"unlocked"}` |
| `home/system/state`   | webapp (retained)  | `{"state": "ARMED"|...}`         |

Set `BROKER_IP` in `webapp/config.py` to the broker Pi's address
(`10.67.110.169`).

Reset is done from the web panel (DISARM).

## State flow

| From      | Trigger              | To        | Effect               |
|-----------|----------------------|-----------|----------------------|
| DISARMED  | ARM (panel)          | ARMED     | monitoring           |
| ARMED     | sound **or** motion  | LOCKDOWN  | LED on, servo locks  |
| any       | DISARM (panel)       | DISARMED  | LED off, unlock      |

While DISARMED the sensors are deliberately ignored -- nothing happens until
the system is armed.

## Quick broker test

On the broker Pi:
```
mosquitto_sub -t 'home/#' -v
mosquitto_pub -h 10.67.110.169 -t home/sensor/sound -m '{"triggered":true}'
```
When armed, the web app should reply with `home/actuator/led {"state":"on"}`
and `home/actuator/servo {"state":"locked"}`.
