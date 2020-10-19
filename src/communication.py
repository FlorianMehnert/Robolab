#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
import json
import platform
import ssl

import debug
import time
import uuid
from typing import Tuple

import paho.mqtt.client as mqtt

from color import ColorPrint as Color
from planet import Direction

# Fix: SSL certificate problem on macOS
if all(platform.mac_ver()):
    from OpenSSL import SSL


class Communication:
    """
    Class to hold the MQTT client communication
    """

    def __init__(self, mqtt_client, group, logger, planet):
        """
        Initializes communication module, connect to server, subscribe, etc.
        :param mqtt_client: paho.mqtt.client.Client
        :param logger: logging.Logger
        :param planet: Planet
        """
        self.group = group
        self.planet = planet
        self.wait = False
        self.wait_send_finish = False
        self.timeout_complete = True
        self.last_connection_time = time.time()
        self.error_msg_received = False

        self.debug = debug.Debug()
        self.logger = logger
        self.logger.debug(f"Group-ID: {self.group}")

        # MQTT client setup
        self.client = mqtt_client
        self.client = mqtt.Client(client_id=self.group + str(uuid.uuid4()),  # Unique Client-ID to recognize our program
                                  clean_session=True,  # We want a clean session after disconnect or abort/crash
                                  protocol=mqtt.MQTTv311  # Define MQTT protocol version
                                  )
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        self.client.on_message = self.safe_on_message_handler
        self.client.enable_logger(logger)
        self.client.username_pw_set(self.group, 'eYa0NxbLnI')
        self.client.connect('mothership.inf.tu-dresden.de', port=8883)
        self.client.subscribe("explorer/" + self.group, qos=1)
        self.client.loop_start()  # Start listening to incoming messages

    # DO NOT EDIT THE METHOD SIGNATURE
    def on_message(self, client, data, message):
        """
        Handles the callback if any message arrived
        :param client: paho.mqtt.client.Client
        :param data: Object
        :param message: Object
        :return: void
        """
        self.last_connection_time = time.time()
        self.timeout_complete = False
        payload = json.loads(message.payload.decode('utf-8'))
        self.logger.debug(json.dumps(payload, indent=2))
        msg_from = payload["from"]
        msg_type = payload["type"]
        # self.debug.bprint(json.dumps(payload, indent=2))
        # self.debug.bprint(msg_from, msg_type, "on_message")

        if msg_from == "server":
            payload = payload["payload"]
            if msg_type == "planet":
                self.planet.planet_name = payload["planetName"]
                self.debug.bprint(f"Robot is on Planet {self.planet.planet_name}")
                self.client.subscribe("planet/" + self.planet.planet_name + "/" + self.group, qos=1)
                self.logger.debug("Planet name: " + self.planet.planet_name)
                self.planet.set_start((payload["startX"], payload["startY"]), payload["startOrientation"])
                start_path_dir = (payload["startOrientation"] + 180) % 360
                self.planet.add_path(((payload["startX"], payload["startY"]), start_path_dir),
                                     ((payload["startX"], payload["startY"]), start_path_dir), -1)

                self.debug.bprint(f"robot starts at: {self.planet.start}")
                self.wait = False
            elif msg_type == "path":
                self.planet.add_path(((payload["startX"], payload["startY"]), payload["startDirection"]),
                                     ((payload["endX"], payload["endY"]), payload["endDirection"]),
                                     payload["pathWeight"])
                self.planet.set_start((payload["endX"], payload["endY"]),
                                      Direction((payload["endDirection"] + 180) % 360))
                self.wait = False
            elif msg_type == "pathSelect":
                self.planet.set_start_direction(payload["startDirection"])
                msg = "PathSelect Correction:" + str(payload["startDirection"])
                self.debug.bprint(msg)
            elif msg_type == "target":
                self.planet.target = (payload["targetX"], payload["targetY"])
                self.debug.bprint(f"Target is set {self.planet.target}")
            elif msg_type == "pathUnveiled":
                self.planet.add_path(((payload["startX"], payload["startY"]), payload["startDirection"]),
                                     ((payload["endX"], payload["endY"]), payload["endDirection"]),
                                     payload["pathWeight"])
            elif msg_type == "done":
                self.wait = False
                self.debug.bprint(payload["message"])
        elif msg_from == "client":
            self.wait_send_finish = False
        elif msg_from == "debug":
            if msg_type == "error":
                self.debug.bprint(json.dumps(payload, indent=2))
                self.error_msg_received = True
                self.wait = False
                self.wait_send_finish = False

    # DO NOT EDIT THE METHOD SIGNATURE
    #
    # In order to keep the logging working you must provide a topic string and
    # an already encoded JSON-Object as message.
    def send_message(self, topic, message):
        """
        Sends given message to specified channel
        :param topic: String
        :param message: Object
        :return: void
        """
        self.last_connection_time = time.time()
        self.logger.debug('Send to: ' + topic)
        self.logger.debug(json.dumps(message, indent=2))

    # DO NOT EDIT THE METHOD SIGNATURE OR BODY
    #
    # This helper method encapsulated the original "on_message" method and handles
    # exceptions thrown by threads spawned by "paho-mqtt"
    def safe_on_message_handler(self, client, data, message):
        """
        Handle exceptions thrown by the paho library
        :param client: paho.mqtt.client.Client
        :param data: Object
        :param message: Object
        :return: void
        """
        try:
            self.on_message(client, data, message)
        except:
            import traceback
            traceback.print_exc()
            raise

    def send_ready(self):
        payload = {"from": "client", "type": "ready"}
        payload = json.dumps(payload)
        self.debug.bprint("Send Ready")
        self.wait = True
        self.send_robot_message(payload, "explorer/" + self.group)
        self.planet.new_planet = False
        while self.wait:
            continue
        self.timeout()

    def send_path(self, start: Tuple[Tuple[int, int], Direction], target: Tuple[Tuple[int, int], Direction],
                  status: str):
        """
        sends selected path to server
        start -- ((startX, startY), startDirection)
        target -- ((endX, endY), endDirection)
        status -- either "free"
        """
        payload = {"from": "client",
                   "type": "path",
                   "payload": {
                       "startX": start[0][0],
                       "startY": start[0][1],
                       "startDirection": start[1],
                       "endX": target[0][0],
                       "endY": target[0][1],
                       "endDirection": target[1],
                       "pathStatus": status
                   }
                   }
        payload = json.dumps(payload)
        topic = "planet/" + self.planet.planet_name + "/" + self.group
        self.wait = True
        self.send_robot_message(payload, topic)
        while self.wait:
            continue
        server_target = (self.planet.paths[start[0]][start[1]][0], Direction(self.planet.paths[start[0]][start[1]][1]))
        if server_target == target:
            self.debug.bprint(f"{Color.green}Odometry success{Color.reset}")
        else:
            self.debug.bprint(f"{Color.yellow}Odometry error! "
                  f"Odometry target: {target}, server target: {server_target}{Color.reset}")
        self.timeout()

    def send_path_select(self, path: Tuple[Tuple[int, int], Direction]):
        payload = {
            "from": "client",
            "type": "pathSelect",
            "payload": {
                "startX": path[0][0],
                "startY": path[0][1],
                "startDirection": path[1]
            }
        }
        payload = json.dumps(payload)
        topic = "planet/" + self.planet.planet_name + "/" + self.group
        self.send_robot_message(payload, topic)
        self.planet.start = path
        self.timeout()

    def send_target_reached(self):
        payload = {
            "from": "client",
            "type": "targetReached",
            "payload": {
                "message": "Finish",
            }
        }
        payload = json.dumps(payload)
        topic = "explorer/" + self.group
        self.wait = True
        self.send_robot_message(payload, topic)
        while self.wait:
            continue
        self.timeout()

    def send_exploration_completed(self):
        payload = {
            "from": "client",
            "type": "explorationCompleted",
            "payload": {
                "message": "Finish",
            }
        }
        payload = json.dumps(payload)
        topic = "explorer/" + self.group
        self.wait = True
        self.send_robot_message(payload, topic)
        while self.wait:
            continue
        self.timeout()

    def timeout(self):
        while time.time() - self.last_connection_time < 3:
            continue
        if not self.timeout_complete:
            # TODO: get Sound
            self.timeout_complete = True

    def send_robot_message(self, payload: str, topic: str):
        """
        Send message to mothership
        Example:
            sendMessage("{"from" : "client", "type" : "ready"}", "explorer/217")
        :param payload: String: payload in JSON of MQTT message
        :param topic: String: topic of MQTT message
        """
        self.wait_send_finish = True
        self.client.publish(topic, payload=payload, qos=1)
        while self.wait_send_finish:
            continue
