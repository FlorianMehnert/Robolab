#!/usr/bin/env python3

import ev3dev.ev3 as ev3
import logging
import os
import paho.mqtt.client as mqtt
import uuid

from communication import Communication
from odometry import Odometry
from planet import Direction, Planet

client = None  # DO NOT EDIT

m1: ev3.LargeMotor
m2: ev3.LargeMotor
us: ev3.UltrasonicSensor = ev3.UltrasonicSensor()
ts: ev3.TouchSensor = ev3.TouchSensor()


def run():
    # DO NOT CHANGE THESE VARIABLES
    #
    # The deploy-script uses the variable "client" to stop the mqtt-client after your program stops or crashes.
    # Your script isn't able to close the client after crashing.
    global client

    client_id = 'YOURGROUPID-' + str(uuid.uuid4())  # Replace YOURGROUPID with your group ID
    client = mqtt.Client(client_id=client_id,  # Unique Client-ID to recognize our program
                         clean_session=True,  # We want a clean session after disconnect or abort/crash
                         protocol=mqtt.MQTTv311  # Define MQTT protocol version
                         )
    log_file = os.path.realpath(__file__) + '/../../logs/project.log'
    logging.basicConfig(filename=log_file,  # Define log file
                        level=logging.DEBUG,  # Define default mode
                        format='%(asctime)s: %(message)s'  # Define default logging format
                        )
    logger = logging.getLogger('RoboLab')

    # THE EXECUTION OF ALL CODE SHALL BE STARTED FROM WITHIN THIS FUNCTION.
    # ADD YOUR OWN IMPLEMENTATION HEREAFTER.
    m1 = ev3.LargeMotor('outB')
    m2 = ev3.LargeMotor('outC')
    while True:
        if ts.is_pressed:
            m1.run_to_rel_pos(speed_sp=1000, position_sp=360)
        else:
            m1.stop()


# DO NOT EDIT
if __name__ == '__main__':
    run()
