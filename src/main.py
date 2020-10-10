#!/usr/bin/env python3

import logging
import os
import uuid
import signal
from time import sleep

import ev3dev.ev3 as ev3
import paho.mqtt.client as mqtt
from ev3dev.core import PowerSupply

import specials
from follow import Follow
from follow import isColor
from specials import blink

client = None  # DO NOT EDIT

m1: ev3.LargeMotor = ev3.LargeMotor('outB')
m2: ev3.LargeMotor = ev3.LargeMotor('outC')
cs: ev3.ColorSensor = ev3.ColorSensor()
ts: ev3.TouchSensor = ev3.TouchSensor()
gy: ev3.GyroSensor = ev3.GyroSensor()
ps: PowerSupply = PowerSupply()
rc: ev3.RemoteControl = ev3.RemoteControl()
us: ev3.UltrasonicSensor = ev3.UltrasonicSensor()

follow = Follow(m1, m2, cs, ts, gy, rc)

print(f"current battery is {ps.measured_volts}")


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
                        level=logging.INFO,  # Define default mode
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
            specials.wasd(m1, m2)
        elif mode == "paths":
            follow.findAttachedPaths()
        elif mode == "ir":
            specials.remoteControl(rc, m1, m2)
        elif mode == "test":
            for i in range(4):
                follow.turnRightXTimes(1)
                m1.stop()
                m2.stop()
                sleep(2)

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
                # finding a red node
                print("red detected")
                ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.RED)
                ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.RED)
                dirDict = follow.findAttachedPaths()
                # do some calculation stuff

            elif isColor(currentColor, rgbBlue, dist):
                # finding a blue node
                print("blue detected")
                ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.AMBER)
                ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.AMBER)
                follow.findAttachedPaths()

            else:
                # default line follow
                follow.follow(optimal, 250)
                if us.value() < 200:
                    m1.run_forever(speed_sp=200)
                    m2.run_forever(speed_sp=-200)
                    m1.position = 0
                    blink()
                    while m1.position < 550:
                        sleep(.2)
                    m1.stop()
                    m2.stop()

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


signal.signal(signal.SIGINT, CtrlCHandler)

# DO NOT EDIT
if __name__ == '__main__':
    #
    run()
