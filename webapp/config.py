"""Shared settings for the home security system."""

# Broker Pi address
BROKER_IP = "192.168.1.6"
BROKER_PORT = 1883

# Web server
WEB_PORT = 5000

# ---- MQTT topics ----
# Sensors publish -> controller reacts
T_SOUND  = "home/sensor/sound"
T_MOTION = "home/sensor/motion"
T_TOUCH  = "home/sensor/touch"
# Controller publishes -> actuators react
T_LED    = "home/actuator/led"
T_SERVO  = "home/actuator/servo"
# Controller publishes system state (retained, so late clients catch up)
T_STATE  = "home/system/state"
