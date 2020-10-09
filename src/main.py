#!/usr/bin/env python3
import signal
from time import sleep

import ev3dev.ev3 as ev3
import logging
import os
import paho.mqtt.client as mqtt
import uuid

from communication import Communication
from odometry import Odometry
from planet import Direction, Planet
from follow import Follow
from follow import isColor
from follow import stop
from follow import findAttachedPaths
from follow import wasd
from gyro import Gyro

client = None  # DO NOT EDIT

m1: ev3.LargeMotor = ev3.LargeMotor('outB')
m2: ev3.LargeMotor = ev3.LargeMotor('outC')
cs: ev3.ColorSensor = ev3.ColorSensor()
ts: ev3.TouchSensor = ev3.TouchSensor()
ev3GY: ev3.GyroSensor = ev3.GyroSensor()
gy: Gyro = Gyro(ev3GY)


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


    dist = 25
    try:
        run = True

        print("starting")
        mode = input("mode?")

        if mode == "wasd":
            wasd(m1,m2)
        elif mode == "gyro":
            gy.turnDegree(m1,m2,360)
        follow = Follow(m1, m2, cs, ts)

        # rgbRed, rgbBlue, rgbWhite, rgbBlack, optimal = follow.calibrate()
        rgbRed = (160, 61, 27)
        rgbBlue = (40, 152, 142)
        rgbBlack = (34, 78, 33)
        rgbWhite = (245, 392, 258)
        optimal = 171.5

        while run:
            cs.mode = "RGB-RAW"
            currentColor = cs.bin_data("hhh")
            if isColor(currentColor, rgbRed, dist):
                print("red detected")
                ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.RED)
                ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.RED)
                findAttachedPaths(m1, m2, pos=220, speed=200, gyro=gy)

            elif isColor(currentColor, rgbBlue, dist):
                print("blue detected")
                ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.AMBER)
                ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.AMBER)
                findAttachedPaths(m1, m2, pos=200, speed=100, gyro=gy)


            else:
                follow.follow(optimal, 250)
    except Exception as exc:
        print(exc)
        try:
            m1.stop()
            m2.stop()
            return
        except OSError:
            print("some part is missing")
            return





def CtrlCHandler(signm, frame):
    print("\nCtrl-C pressed")
    m1.stop()
    m2.stop()



# signal.signal(signal.SIGINT, CtrlCHandler)

# DO NOT EDIT
if __name__ == '__main__':
    run()
