#!/usr/bin/env python3

import logging
import os
import uuid
# import signal
from time import sleep
from typing import Tuple, List

import ev3dev.ev3 as ev3
import paho.mqtt.client as mqtt
from ev3dev.core import PowerSupply

import specials
from follow import Follow, convPathsToDirection
from follow import isColor
from odometry import Odometry
from specials import blink

client = None  # DO NOT EDIT

m1: ev3.LargeMotor = ev3.LargeMotor('outB')
m2: ev3.LargeMotor = ev3.LargeMotor('outC')
cs: ev3.ColorSensor = ev3.ColorSensor()
ts: ev3.TouchSensor = ev3.TouchSensor()
gy: ev3.GyroSensor = ev3.GyroSensor()
ps: PowerSupply = PowerSupply()
# rc: ev3.RemoteControl = ev3.RemoteControl()
us: ev3.UltrasonicSensor = ev3.UltrasonicSensor()



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

    # THIS IS WHERE PARADISE BEGINS
    # CODe
    movement: List[
        Tuple[int, int]] = []  # used to save all movement values gathered while line following for odometry calculations

    oldGamma = 0
    newGamma = 0
    oldNodeX = 0
    oldNodeY = 0
    newNodeX = 0
    newNodeY = 0

    follow = Follow(m1, m2, cs, ts, gy, movement)
    odo = Odometry(gamma=0, posX=0, posY=0, movement=movement, distBtwWheels=9.2)
    follow.reset()

    oldM1: int = m1.position
    oldM2: int = m2.position
    newM1 = 0
    newM2 = 0


    try:
        run = True

        rgbRed = (160, 61, 27)
        rgbBlue = (40, 152, 142)
        rgbBlack = (34, 78, 33)
        rgbWhite = (245, 392, 258)
        optimal = 171.5

        print("starting")

        while run:
            mode = input("mode?")
            if mode == "wasd":
                specials.wasd(m1, m2)
            elif mode == "paths":
                follow.findAttachedPaths()
            # elif mode == "ir":
            #     if rc:
            #         specials.remoteControl(rc, m1, m2)
            elif mode == "battery":
                print(ps.measured_volts)
            elif mode == "calibrate":
                rgbRed, rgbBlue, rgbWhite, rgbBlack, optimal = follow.calibrate()
            elif mode == "/help":
                print("wasd, paths, battery, calibrate, ")
            elif mode == "":
                run = False
            elif mode == "pid":
                k = input("kp, ki, kp")
                if k == "p":
                    follow.kp = float(input("proportional?"))
                elif k == "i":
                    follow.ki = float(input("integral?"))
                elif k == "d":
                    follow.kd = float(input("derivate?"))
            elif mode == "test":
                with open("/home/src/values.txt") as file:
                    for line in file:
                        print(line)
        run = True
        while run:
            cs.mode = "RGB-RAW"
            currentColor = cs.bin_data("hhh")

            if isColor(currentColor, rgbRed, 25) or isColor(currentColor, rgbBlue , 25):

                # finding a node
                print("red detected")
                ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.RED)
                ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.RED)
                dirDict = follow.findAttachedPaths()
                follow.stop()
                odo.calculateNewPosition(movement)
                follow.turnRightXTimes(convPathsToDirection(dirDict))  # only needed as long dfs isn't implemented

            elif isColor(currentColor, rgbBlue, 25):
                # finding a blue node
                print("blue detected")
                ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.AMBER)
                ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.AMBER)
                dirDict = follow.findAttachedPaths()
                follow.stop()
                odo.calculateNewPosition(movement)
                follow.turnRightXTimes(convPathsToDirection(dirDict))  # only needed as long dfs isn't implemented


            else:
                # default line follow

                follow.follow(optimal, 350, odo)

                if us.value() < 200:
                    m1.run_forever(speed_sp=200)
                    m2.run_forever(speed_sp=-200)
                    m1.position = 0
                    blink()
                    while m1.position < 550:
                        sleep(.2)
                    follow.stop()

                oldM1 = newM1
                oldM2 = newM2
                newM1 = m1.position
                newM2 = m2.position
                movement.append((newM1 - oldM1, newM2 - oldM2))

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
    exit(0)


# signal.signal(signal.SIGINT, CtrlCHandler) #only useful when starting robot per ssh

# DO NOT EDIT
if __name__ == '__main__':
    #
    run()
