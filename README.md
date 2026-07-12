# TALOS -- Home Security System (Web App)

The web control panel + brain for a smart-home system.

## Network layout

```
                 HomeRouter (WiFi)
                /       |        \
        Publisher    Broker     Subscriber        + laptop (runs this web app)
         Pi           Pi          Pi                & phone  (view the panel)
       sound, motion  Mosquitto  LED, servo
       & touch
```

- **Publisher Pi** -- sound, motion + touch sensors (publishes events)
- **Broker Pi** -- Mosquitto (relays all MQTT traffic)
- **Subscriber Pi** -- LED + servo lock (subscribes to commands)
- **Laptop** -- runs this web app
- **Phone** -- just views the control panel over the same WiFi

## Structure

```
inf1006-talos/
├── webapp/
│   ├── app.py            # run this
│   ├── controller.py     # the brain: DISARMED/ARMED/ALERT/LOCKDOWN
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
Laptop + phone share the same WiFi.
1. `ipconfig` -> note the Wi-Fi IPv4 Address.
2. Allow the port (ADMIN PowerShell):
   `netsh advfirewall firewall add rule name="TALOS 5000" dir=in action=allow protocol=TCP localport=5000`
3. Phone browser: `http://<laptop-ip>:5000`

## Interface

The web app is already listening on these topics. Match these names and payloads
exactly.

| Topic                 | Who publishes      | Payload                          |
|-----------------------|--------------------|----------------------------------|
| `home/sensor/sound`   | Publisher Pi       | `{"triggered": true}`            |
| `home/sensor/motion`  | Publisher Pi       | `{"triggered": true}`            |
| `home/sensor/touch`   | Publisher Pi       | `{"triggered": true}`            |
| `home/actuator/led`   | webapp             | `{"state": "on"|"off"}`          |
| `home/actuator/servo` | webapp             | `{"state": "locked"|"unlocked"}` |
| `home/system/state`   | webapp (retained)  | `{"state": "ARMED"|...}`         |

Set `BROKER_IP` in `webapp/config.py` to the broker Pi's address.

**Reset:** the touch sensor resets the system (any state -> DISARMED, LED off,
door unlocked) by publishing `home/sensor/touch`. You can also reset from the
web panel (RESET / DISARM).

## State flow

| From      | Trigger            | To        | Effect            |
|-----------|--------------------|-----------|-------------------|
| DISARMED  | ARM (panel)        | ARMED     | monitoring        |
| ARMED     | sound              | ALERT     | LED on            |
| ALERT     | motion             | LOCKDOWN  | servo locks       |
| any       | touch (or RESET)   | DISARMED  | LED off, unlock   |

## Quick broker test (no hardware needed)

On the broker Pi:
```
mosquitto_sub -t 'home/#' -v
mosquitto_pub -h <broker-ip> -t home/sensor/sound -m '{"triggered":true}'
```
When armed, the web app should reply with `home/actuator/led {"state":"on"}`.
