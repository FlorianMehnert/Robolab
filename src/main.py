#!/usr/bin/env python3
import argparse
import logging
import math
import os
import uuid
from pprint import pprint
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

        follow.menu(calibrate, sd)

        global oldOrientation
        global oldNodeX
        global oldNodeY
        global newNodeX
        global newNodeY

        oldOrientation = Direction.NORTH
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
        nodeCount = 0
        while run:

            cs.mode = "RGB-RAW"
            currentColor = cs.bin_data("hhh")

            if isColor(currentColor, rgbRed, 25) or isColor(currentColor, rgbBlue, 25):
                # discovers node
                nodeCount += 1
                follow.stop()
                follow.stop()
                print(f"{specials.colorCodes.red}{nodeCount}.node{specials.colorCodes.reset}")
                if planet.newPlanet:
                    # first node discovered
                    mqttc.sendReady()
                    mqttc.timeout()
                    sleep(1)

                    # only works because while loops is very fast... the faster the while the slower the less does the robot roll
                    # TODO: fix m1 and m2 only getting stopped by follow and wait for m1/m2 to stop
                    m1.run_to_rel_pos(speed_sp=1000, position_sp=1000)
                    m2.run_to_rel_pos(speed_sp=1000, position_sp=1000)
                    print(
                        f"serverX = {oldNodeX}, serverY = {oldNodeY}, {specials.colorCodes.red}"
                        f"serverDirection = {specials.colorCodes.reset} {oldOrientation}, "
                        f"odoX = {odo.posX}, odoY = {odo.posY}, {specials.colorCodes.red}"
                        f"odoDirection ={specials.colorCodes.reset} {odo.gamma}")

                else:

                    # any other node discovered
                    odo.calculateNewPosition(movement)
                    # updates odo.poX, odo.posY, odo.gamma

                    # prints every position data
                    print(
                        f"serverX = {oldNodeX}, serverY = {oldNodeY}, {specials.colorCodes.red}"
                        f"serverDirection = {specials.colorCodes.reset} {oldOrientation}, "
                        f"odoX = {odo.posX}, odoY = {odo.posY}, {specials.colorCodes.red}"
                        f"odoDirection ={specials.colorCodes.reset} {odo.gamma}")

                    if follow.pathBlocked:
                        # sends blocked path when ultrasonic sensor detected an obstacle (uses old values for target)
                        mqttc.sendPath(((oldNodeX, oldNodeY), oldOrientation), ((oldNodeX, oldNodeY), oldOrientation),
                                       status="blocked")
                        follow.pathBlocked = False

                    else:
                        # sends just discovered path
                        mqttc.sendPath(((oldNodeX, oldNodeY), oldOrientation),
                                       ((round(odo.posX), round(odo.posY)), odo.gammaToDirection(odo.gamma + 180)),
                                       status="free")

                # Target reached
                if planet.target is not None:
                    if planet.target == planet.start[0]:
                        mqttc.sendTargetReached()
                        print("Target reached")
                        pprint(planet.paths, indent=2)
                        sd.beep()
                        break

                # updated planet data: current position + facing
                oldNodeX = planet.start[0][0]
                oldNodeY = planet.start[0][1]
                oldOrientation = planet.start[1]

                # syncing odometry with server data
                odo.posX = planet.start[0][0]
                odo.posY = planet.start[0][1]
                odo.gamma = planet.start[1]

                # scan knots
                relativePaths = follow.findAttachedPaths()
                absolutePaths = follow.gammaRelToAbs(relativePaths, oldOrientation)
                planet.setAttachedPaths((oldNodeX, oldNodeY), absolutePaths)
                # update stack to remove all known weighted paths
                discovered = planet.getPathsWithWrongWeight()
                planet.updateStack(discovered)

                # adds current odo view-angle to dirRel
                dirAbs = planet.getNextDirection()

                # Exploration completed
                if dirAbs is None:
                    mqttc.sendExplorationCompleted()
                    print("Exploration completed")
                    pprint(planet.paths, indent=2)
                    sd.beep()
                    break

                dirRel: Direction = odo.gammaToDirection(dirAbs + odo.gamma)

                print(f"{specials.colorCodes.red}selected: {dirRel}{specials.colorCodes.reset}, "
                      f"{specials.colorCodes.blue}absolute: {dirAbs}{specials.colorCodes.reset}")

                print(f"{specials.colorCodes.cyan}relPaths = {specials.colorCodes.reset}{relativePaths}\n"
                      f"{specials.colorCodes.cyan}absPaths = {specials.colorCodes.reset}{absolutePaths}")
                print(f"{specials.colorCodes.yellow}dirRel = {dirRel}{specials.colorCodes.reset} "
                      f"{specials.colorCodes.yellow}and dirAbs = {dirAbs}{specials.colorCodes.reset}")

                # sends selected path
                # might cause planet update which leads to us needing to update our internal orientation
                mqttc.sendPathSelect(((oldNodeX, oldNodeY), dirAbs))

                print(f"dirAbs = {dirAbs}, planetDirection = {planet.start[1]}")
                dirAbs = planet.start[1]
                dirRel = (dirAbs - oldOrientation) % 360
                oldOrientation = dirAbs
                print("Status of path to be explored: ", planet.paths[planet.start[0]][dirAbs])

                follow.turnRightXTimes(dirRel / 90)
                odo.gamma = math.radians(dirAbs)

                if isColor(currentColor, rgbRed, 25):
                    print("\u001b[31mRED\u001b[0m")
                    follow.leds(ev3.Leds.RED)
                elif isColor(currentColor, rgbBlue, 25):
                    print("\u001b[34mBLUE\u001b[0m")
                    follow.leds(ev3.Leds.GREEN)

                odo.oldM1 = 0
                odo.oldM2 = 0
                odo.newM1 = 0
                odo.newM2 = 0
                m1.position = 0
                m2.position = 0
                movement = []
            else:

                follow.follow(optimal, 250)

                if us.value() < 200:
                    follow.stop()
                    sd.beep()
                    print("\u001b[31mPATH BLOCKED\u001b[0m")
                    follow.pathBlocked = True
                    blink()
                    sleep(1)

                    m1.run_forever(speed_sp=200)
                    m2.run_forever(speed_sp=-200)

                    follow.turnRightXTimes(2)
                    odo.gamma = odo.gammaToDirection(odo.gamma + Direction.SOUTH)

                    follow.stop()
                    follow.stop()

                odo.oldM1 = odo.newM1
                odo.oldM2 = odo.newM2
                odo.newM1 = m1.position
                odo.newM2 = m2.position
                movement.append((odo.newM1 - odo.oldM1, odo.newM2 - odo.oldM2))
    except OSError:
        print("some part is missing")

# PLS EDIT

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--calibrate", action="store_true")
    args = parser.parse_args()

    run(calibrate=args.calibrate)
