#!/usr/bin/env python3
import argparse
import logging
import os
import uuid
from time import sleep
from typing import Tuple, List

import ev3dev.ev3 as ev3
import paho.mqtt.client as mqtt

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
us: ev3.UltrasonicSensor = ev3.UltrasonicSensor()
sd: ev3.Sound = ev3.Sound()
ps: ev3.PowerSupply = ev3.PowerSupply()

print(f"current battery is {ps.measured_volts}")


def run(calibrate=False):
    # DO NOT CHANGE THESE VARIABLES
    #
    # The deploy-script uses the variable "client" to stop the mqtt-client after your program stops or crashes.
    # Your script isn't able to close the client after crashing.
    global client

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

    planet = Planet()
    mqttc = Communication(client, logger, planet)
    movement: List[Tuple[int, int]] = []
    # used to save all movement values gathered while line following for odometry calculations

    gy.mode = 'GYRO-CAL'
    gy.mode = 'GYRO-CAL'
    gy.mode = 'GYRO-ANG'
    follow = Follow(m1=m1, m2=m2, cs=cs, ts=ts, gy=gy, movement=movement, ps=ps, sd=sd)
    odo = Odometry(gamma=0, posX=0, posY=0, movement=movement, distBtwWheels=9.2)
    follow.reset()


    try:

        specials.menu(follow, calibrate)

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

        # extracting colorvalues from values.txt
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

        try:
            rgbRed, rgbBlue, rgbWhite, rgbBlack, optimal = colorValues
        except ValueError:
            rgbRed = (160, 61, 27)
            rgbBlue = (40, 152, 142)
            rgbBlack = (34, 78, 33)
            rgbWhite = (245, 392, 258)
            optimal = 171.5

        run = True
        while run:

            cs.mode = "RGB-RAW"
            currentColor = cs.bin_data("hhh")

            if isColor(currentColor, rgbRed, 25) or isColor(currentColor, rgbBlue, 25):
                # discovers node
                follow.stop()
                follow.stop()
                print(odo.gamma)
                if planet.newPlanet:
                    # first node discovered
                    mqttc.sendReady()
                    mqttc.timeout()

                    # TODO sleep?, 1000, 1000 seems a bit much
                    m1.run_to_rel_pos(speed_sp=1000, position_sp=1000)
                    m2.run_to_rel_pos(speed_sp=1000, position_sp=1000)


                else:
                    # any other node discovered

                    # odometry calculation
                    odo.calculateNewPosition(movement)
                    # setting odometry X and Y to nodeX and nodeY
                    newNodeX = int(odo.posX / 50)
                    newNodeY = int(odo.posY / 50)
                    newGamma = follow.gammaToDirection(odo.gamma)

                    # prints every position data
                    print(f"serverX = {oldNodeX}, serverY = {oldNodeY}, {specials.colorCodes.magenta}serverDirection ={specials.colorCodes.reset} {oldGamma}, odoX = {newNodeX}, odoY = {newNodeY}, {specials.colorCodes.magenta}odoDirection ={specials.colorCodes.reset} {newGamma}")

                    if follow.pathBlocked:
                        # sends blocked path when ultrasonic sensor detected an obstacle (uses old values for target)
                        mqttc.sendPath(((oldNodeX, oldNodeY), oldGamma), ((oldNodeX, oldNodeY), oldGamma),
                                       status="blocked")
                        follow.pathBlocked = False

                    else:
                        # sends just discovered path
                        mqttc.sendPath(((oldNodeX, oldNodeY), oldGamma),
                                       ((newNodeX, newNodeY), Direction((newGamma.value + 180) % 360)),
                                       status="free")

                # applying server data to old position and odometry
                oldNodeX = planet.start[0][0]
                oldNodeY = planet.start[0][1]
                oldGamma = planet.start[1]  # direction already gets turned
                odo.posX = oldNodeX
                odo.posY = oldNodeY
                odo.gamma = oldGamma

                paths = follow.findAttachedPaths()
                paths = follow.removeDoubles(paths)

                dirList = follow.gammaRelToAbs(paths, newGamma)  # new gamma needs to be correctly calculated by odo
                dirList = follow.removeDoubles(dirList)

                randDirRel: Direction = follow.selectPath(paths)
                randDirAbs: Direction = Direction((randDirRel.value + int(newGamma.value))%360)  # randDirRel + current absolute angle
                oldGamma = Direction((oldGamma + randDirAbs)%360)
                print("paths, dirList", paths, dirList)
                print("randomDirection Rel and Abs", randDirRel, randDirAbs)

                sleep(1)

                follow.turnRightXTimes(randDirRel.value / 90)
                odo.gamma = randDirAbs
                print(dirList)
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

                follow.follow(optimal, 250)

                if us.value() < 200:
                    print("\u001b[31mPATH BLOCKED\u001b[0m")
                    follow.pathBlocked = True
                    blink()
                    sleep(1)

                    m1.run_forever(speed_sp=200)
                    m2.run_forever(speed_sp=-200)
                    m1.position = 0

                    while m1.position < 550:
                        odo.oldM1 = odo.newM1
                        odo.oldM2 = odo.newM2
                        odo.newM1 = m1.position
                        odo.newM2 = m2.position
                        movement.append((odo.newM1 - odo.oldM1, odo.newM2 - odo.oldM2))
                    follow.stop()
                    follow.stop()

                odo.oldM1 = odo.newM1
                odo.oldM2 = odo.newM2
                odo.newM1 = m1.position
                odo.newM2 = m2.position
                movement.append((odo.newM1 - odo.oldM1, odo.newM2 - odo.oldM2))

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

# PLS EDIT
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--calibrate", action="store_true")
    args = parser.parse_args()

    if args.calibrate:
        run(calibrate=True)
    else:
        run(calibrate=False)
