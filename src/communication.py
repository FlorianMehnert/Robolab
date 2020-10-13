#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
import json
import platform
import ssl
from planet import Direction
from typing import List, Tuple, Dict, Union
import time

# Fix: SSL certificate problem on macOS
if all(platform.mac_ver()):
    from OpenSSL import SSL

class Communication:
    """
    Class to hold the MQTT client communication
    """

    def __init__(self, mqtt_client, logger, planet):
        """
        Initializes communication module, connect to server, subscribe, etc.
        :param mqtt_client: paho.mqtt.client.Client
        :param logger: logging.Logger
        :param planet: Planet
        """
        # DO NOT CHANGE THE SETUP HERE
        self.client = mqtt_client
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        self.client.on_message = self.safe_on_message_handler
        # Add your client setup here
        self.logger = logger
        self.group = self.client._client_id[0:3].decode('utf-8')
        self.planet = planet
        self.wait = False
        self.lastConnectionTime = time.time()
        self.logger.debug(self.group)
        self.client.enable_logger(logger)
        self.client.username_pw_set(self.group, 'eYa0NxbLnI')
        self.client.connect('mothership.inf.tu-dresden.de', port=8883)
        self.client.subscribe("explorer/" + self.group, qos=1)
        self.client.loop_start() # Start listening to incoming messages

    # DO NOT EDIT THE METHOD SIGNATURE
    def on_message(self, client, data, message):
        """
        Handles the callback if any message arrived
        :param client: paho.mqtt.client.Client
        :param data: Object
        :param message: Object
        :return: void
        """
        self.lastConnectionTime = time.time()
        payload = json.loads(message.payload.decode('utf-8'))
        self.logger.debug(json.dumps(payload, indent=2))
        msgFrom = payload["from"]
        msgType = payload["type"]
        payload = payload["payload"]

        if msgFrom == "server":
            if msgType == "planet":
                self.planet.setName(payload["planetName"])
                self.client.subscribe("planet/" + self.planet.getName() + "/" + self.group, qos=1)
                self.logger.debug("Planet name: " + self.planet.getName())
                self.planet.setStart((payload["startX"], payload["startY"]), payload["startOrientation"])
                self.wait = False
            elif msgType == "path":
                self.planet.addPath(((payload["startX"], payload["startY"]), payload["startDirection"]),
                                    ((payload["endX"], payload["endY"]), payload["endDirection"]),
                                    payload["pathWeight"])
                self.planet.setStart((payload["endX"], payload["endY"]), payload["endDirection"])
                self.wait = False
            elif msgType == "pathSelect":
                self.planet.setStartDirection(payload["startDirection"])
            elif msgType == "target":
                self.planet.setTarget((payload["targetX"], payload["targetY"]))
            elif msgType == "pathUnveiled":
                self.planet.addPath(((payload["startX"], payload["startY"]), payload["startDirection"]),
                                    ((payload["endX"], payload["endY"]), payload["endDirection"]),
                                    payload["pathWeight"])
            elif msgType == "done":
                self.wait = False

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
        self.lastConnectionTime = time.time()
        self.logger.debug('Send to: ' + topic)
        self.logger.debug(json.dumps(message, indent=2))
        self.wait = True
        # YOUR CODE FOLLOWS
        

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

    def sendReady(self):
        payload = {"from" : "client", "type" : "ready"}
        payload = json.dumps(payload)
        self.client.publish("explorer/" + self.group, payload=payload, qos=1)
        self.planet.newPlanet = False
        while self.wait:
            continue

    def sendPath(self, start: Tuple[Tuple[int, int], Direction], target: Tuple[Tuple[int, int], Direction],
                 status: str):
        payload = { "from": "client",
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
        topic = "planet/" + self.planet.getName() + "/" + self.group
        self.client.publish(topic, payload=payload, qos=1)
        while self.wait:
            continue

    def sendPathSelect(self, path: Tuple[Tuple[int, int], Direction]):
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
        topic = "planet/" + self.planet.getName() + "/" + self.group
        self.client.publish(topic, payload=payload, qos=1)

    def sendTargetReached(self):
        payload = {
                  "from": "client",
                  "type": "targetReached",
                  "payload": {
                      "message": "Finish",
                  }
        }
        payload = json.dumps(payload)
        topic = "planet/" + self.planet.getName() + "/" + self.group
        self.client.publish(topic, payload=payload, qos=1)
        while self.wait:
            continue

    def sendExplorationCompleted(self):
        payload = {
                  "from": "client",
                  "type": "explorationCompleted",
                  "payload": {
                      "message": "Finish",
                  }
        }
        payload = json.dumps(payload)
        topic = "planet/" + self.planet.getName() + "/" + self.group
        self.client.publish(topic, payload=payload, qos=1)
        while self.wait:
            continue

    def timeout(self):
        while time.time() - self.lastConnectionTime < 3:
            continue