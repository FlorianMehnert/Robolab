#!/usr/bin/env python3

import logging
import os
import uuid
from time import sleep
from typing import Tuple, List

import ev3dev.ev3 as ev3
import paho.mqtt.client as mqtt
from ev3dev.core import PowerSupply

import specials
from communication import Communication
from follow import Follow
from follow import isColor
from odometry import Odometry
from planet import Planet, Direction
from specials import blink

client = None  # DO NOT EDIT

m1: ev3.LargeMotor = ev3.LargeMotor('outB')
m2: ev3.LargeMotor = ev3.LargeMotor('outC')
cs: ev3.ColorSensor = ev3.ColorSensor()
ts: ev3.TouchSensor = ev3.TouchSensor()
gy: ev3.GyroSensor = ev3.GyroSensor()
ps: PowerSupply = PowerSupply()
us: ev3.UltrasonicSensor = ev3.UltrasonicSensor()

print(f"current battery is {ps.measured_volts}")


def run():
    # DO NOT CHANGE THESE VARIABLES
    #
    # The deploy-script uses the variable "client" to stop the mqtt-client after your program stops or crashes.
    # Your script isn't able to close the client after crashing.
    global client, updatedColorValues

    client_id = '217' + str(uuid.uuid4())  # Replace YOURGROUPID with your group ID
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

    planet = Planet()
    mqttc = Communication(client, logger, planet)
    movement: List[
        Tuple[int, int]] = []
    # used to save all movement values gathered while line following for odometry calculations

    follow = Follow(m1, m2, cs, ts, gy, movement)
    odo = Odometry(gamma=0, posX=0, posY=0, movement=movement, distBtwWheels=9.2)
    follow.reset()

    oldM1: int = m1.position
    oldM2: int = m2.position
    newM1 = 0
    newM2 = 0

    try:
        mode = True

        global oldGamma
        global newGamma
        global oldNodeX
        global oldNodeY
        global newNodeX
        global newNodeY

        oldGamma = Direction.NORTH
        newGamma = Direction.NORTH
        oldNodeX = 0
        oldNodeY = 0
        newNodeX = 0
        newNodeY = 0

        print("starting")

        while mode:
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
            elif mode == "/help":
                print("wasd, paths, battery, calibrate, sop, pid")
            elif mode == "":
                mode = False
            elif mode == "sop":
                while not ts.is_pressed:
                    continue
                mode = False
            elif mode == "pid":
                k = input("kp, ki, kp")
                if k == "p":
                    follow.kp = float(input("proportional?"))
                elif k == "i":
                    follow.ki = float(input("integral?"))
                elif k == "d":
                    follow.kd = float(input("derivate?"))
            elif mode == "calibrate":
                with open("/home/robot/src/values.txt", mode="w") as file:
                    for i in follow.calibrate():
                        file.write(f"{i}\n")
            elif mode == "follow":
                while True:
                    follow.follow(optimal=171.5,baseSpeed=200)

        run = True
        while run:
            colorValues = []
            with open("/home/robot/src/values.txt", mode="r") as file:
                for line in file:
                    if line == "\n":
                        continue
                    else:
                        try:
                            colorValues.append(float(line.replace("\n", "")))
                        except Exception:
                            colorValues.append(follow.convStrToRGB(line.replace("\n", "")))

            rgbRed, rgbBlue, rgbWhite, rgbBlack, optimal = colorValues

            # rgbRed = (160, 61, 27)
            # rgbBlue = (40, 152, 142)
            # rgbBlack = (34, 78, 33)
            # rgbWhite = (245, 392, 258)
            # optimal = 171.5

            cs.mode = "RGB-RAW"
            currentColor = cs.bin_data("hhh")

            if isColor(currentColor, rgbRed, 25) or isColor(currentColor, rgbBlue, 25):
                follow.stop()

                if planet.newPlanet:
                    mqttc.sendReady()
                    mqttc.timeout()
                    m1.run_to_rel_pos(speed_sp=1000, position_sp=1000)
                    m2.run_to_rel_pos(speed_sp=1000, position_sp=1000)

                else:
                    odo.calculateNewPosition(movement)
                    newNodeX = int(odo.posX / 15)
                    newNodeY = int(odo.posY / 15)
                    newGamma = follow.gammaToDirection(odo.gamma)
                    print(oldNodeX, oldNodeY, oldGamma, newNodeX, newNodeY, newGamma, "main else all node values")
                    if follow.pathBlocked:
                        mqttc.sendPath(((oldNodeX, oldNodeY), oldGamma), ((newNodeX, newNodeY), newGamma),
                                       status="blocked")
                    else:
                        mqttc.sendPath(((oldNodeX, oldNodeY), oldGamma), ((newNodeX, newNodeY), newGamma),
                                       status="free")
                        follow.pathBlocked = False

                oldNodeX = planet.start[0][0]
                oldNodeY = planet.start[0][1]
                oldGamma = planet.start[1]
                odo.posX = oldNodeX
                odo.posY = oldNodeY
                odo.gamma = oldGamma

                paths = follow.findAttachedPaths()
                print("oldGamma and paths", oldGamma, paths)
                dirList = follow.gammaRelToAbs(paths, oldGamma)
                print("randDirRel")
                randDirRel = follow.selectPath(paths)
                print("randDirAbs")
                randDirAbs = follow.selectPath(dirList)
                sleep(1)
                print("\u001b[31mrandDirRel, randDirAbs, oldGamma\u001b[0m", randDirRel, randDirAbs, oldGamma)
                print("dirList", dirList)
                print("paths", paths)
                follow.turnRightXTimes(randDirRel.value / 90)
                planet.setAttachedPaths((oldNodeX, oldNodeY), dirList)

                mqttc.sendPathSelect(((oldNodeX, oldNodeY), randDirAbs))

                # select one path
                # send to server
                # apply server changes to gamma from start
                # (turn to direction of server)

                if isColor(currentColor, rgbRed, 25):
                    print("\u001b[31mRED\u001b[0m")
                    follow.leds(ev3.Leds.RED)
                elif isColor(currentColor, rgbBlue, 25):
                    print("\u001b[34mBLUE\u001b[0m")
                    follow.leds(ev3.Leds.GREEN)

            else:

                follow.follow(optimal, 300)

                if us.value() < 200:
                    print("\u001b[31mPATH BLOCKED\u001b[0m")
                    follow.pathBlocked = True
                    m1.run_forever(speed_sp=200)
                    m2.run_forever(speed_sp=-200)
                    m1.position = 0
                    blink()
                    while m1.position < 550:
                        oldM1 = newM1
                        oldM2 = newM2
                        newM1 = m1.position
                        newM2 = m2.position
                        movement.append((newM1 - oldM1, newM2 - oldM2))
                    follow.stop()

                oldM1 = newM1
                oldM2 = newM2
                newM1 = m1.position
                newM2 = m2.position
                movement.append((newM1 - oldM1, newM2 - oldM2))

    except NotADirectoryError as exc:
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
