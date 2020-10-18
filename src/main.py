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
from follow import is_color
from odometry import Odometry
from planet import Planet, Direction
from specials import blink, star_wars_sound

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

    follow = Follow(m1=m1, m2=m2, cs=cs, ts=ts, gy=gy, movement=movement, ps=ps, sd=sd)
    odo = Odometry(gamma=0, posX=0, posY=0, movement=movement, distBtwWheels=9.2)
    follow.reset()

    try:

        follow.menu(calibrate, sd)

        global old_orientation
        global old_nodeX
        global old_nodeY
        global new_nodeX
        global new_nodeY

        old_orientation = Direction.NORTH
        old_nodeX = 0
        old_nodeY = 0
        new_nodeX = 0
        new_nodeY = 0

        # extracting colorvalues from values.txt
        color_values = []
        with open("/home/robot/src/values.txt", mode="r") as file:
            for line in file:
                if line == "\n":
                    continue
                else:
                    try:
                        color_values.append(float(line.replace("\n", "")))
                    except Exception:
                        color_values.append(follow.conv_str_to_rgb(line.replace("\n", "")))

        try:
            rgb_red, rgb_blue, rgb_white, rgb_black, optimal = color_values
        except ValueError:
            rgb_red = (160, 61, 27)
            rgb_blue = (40, 152, 142)
            rgb_black = (34, 78, 33)
            rgb_white = (245, 392, 258)
            optimal = 171.5

        run = True
        node_count = 0
        while run:

            cs.mode = "RGB-RAW"
            current_color = cs.bin_data("hhh")

            if is_color(current_color, rgb_red, 25) or is_color(current_color, rgb_blue, 25):
                # discovers node
                node_count += 1
                follow.stop()
                follow.stop()
                print(f"{specials.color_codes.red}{node_count}.node{specials.color_codes.reset}")
                if planet.new_planet:
                    # first node discovered
                    mqttc.send_ready()
                    mqttc.timeout()
                    sleep(1)

                    # only works because while loops is very fast... the faster the while the slower the less does the robot roll
                    # TODO: fix m1 and m2 only getting stopped by follow and wait for m1/m2 to stop
                    m1.run_to_rel_pos(speed_sp=1000, position_sp=1000)
                    m2.run_to_rel_pos(speed_sp=1000, position_sp=1000)
                    print(
                        f"serverX = {old_nodeX}, serverY = {old_nodeY}, {specials.color_codes.red}"
                        f"serverDirection = {specials.color_codes.reset} {old_orientation}, "
                        f"odoX = {odo.posX}, odoY = {odo.posY}, {specials.color_codes.red}"
                        f"odoDirection ={specials.color_codes.reset} {odo.gamma}")

                else:

                    # any other node discovered
                    odo.calculate_new_position(movement)
                    print(
                        f"{specials.color_codes.red}BEFORE: odoX and odoY{odo.posX, odo.posY} aswell as oldNodeX and oldNodeY {old_nodeX, old_nodeY}{specials.color_codes.reset}")
                    odo.posX += old_nodeX
                    odo.posY += old_nodeY
                    print(
                        f"{specials.color_codes.red}AFTER: odoX and odoY{odo.posX, odo.posY}{specials.color_codes.reset}")
                    # updates odo.poX, odo.posY, odo.gamma

                    # prints every position data
                    print(
                        f"serverX = {old_nodeX}, serverY = {old_nodeY}, {specials.color_codes.red}"
                        f"serverDirection = {specials.color_codes.reset} {old_orientation}, "
                        f"odoX = {odo.posX}, odoY = {odo.posY}, {specials.color_codes.red}"
                        f"odoDirection ={specials.color_codes.reset} {odo.gamma}")

                    if follow.path_blocked:
                        # sends blocked path when ultrasonic sensor detected an obstacle (uses old values for target)
                        mqttc.send_path(((old_nodeX, old_nodeY), old_orientation), ((old_nodeX, old_nodeY), old_orientation),
                                        status="blocked")
                        follow.path_blocked = False

                    else:
                        # sends just discovered path
                        mqttc.send_path(((old_nodeX, old_nodeY), old_orientation),
                                        ((round(odo.posX), round(odo.posY)), odo.gamma_to_direction(odo.gamma + 180)),
                                        status="free")

                # Target reached
                if planet.target is not None:
                    if planet.target == planet.start[0]:
                        mqttc.send_target_reached()
                        print("Target reached")
                        pprint(planet.paths, indent=2)
                        sd.tone(star_wars_sound)
                        break

                # updated planet data: current position + facing
                old_nodeX = planet.start[0][0]
                old_nodeY = planet.start[0][1]
                old_orientation = planet.start[1]

                # syncing odometry with server data
                odo.posX = planet.start[0][0] / 50
                odo.posY = planet.start[0][1] / 50
                odo.gamma = planet.start[1]

                # scan knots
                if not planet.is_known_node(planet.start[0]):
                    print("Node unknown")
                    relative_paths = follow.find_attached_paths()
                    absolute_paths = follow.gamma_rel_to_abs(relative_paths, old_orientation)
                    planet.set_attached_paths((old_nodeX, old_nodeY), absolute_paths)
                else:
                    m1.run_to_rel_pos(speed_sp=200, position_sp=280)
                    m2.run_to_rel_pos(speed_sp=-200, position_sp=280)
                    print("Node already known")
                    sleep(.4)
                # update stack to remove all known weighted paths
                # discovered = planet.getPathsWithWrongWeight()
                # planet.updateStack(discovered)

                # adds current odo view-angle to dir_rel
                dir_abs = planet.get_next_direction()

                # Exploration completed
                if dir_abs is None:
                    mqttc.send_exploration_completed()
                    print("Exploration completed")
                    pprint(planet.paths, indent=2)
                    # sd.beep()
                    sd.tone(star_wars_sound)
                    break

                dir_rel: Direction = odo.gamma_to_direction(dir_abs + round(odo.gamma))

                print(f"{specials.color_codes.red}selected: {dir_rel}{specials.color_codes.reset}, "
                      f"{specials.color_codes.blue}absolute: {dir_abs}{specials.color_codes.reset}")

                # sends selected path
                # might cause planet update which leads to us needing to update our internal orientation
                mqttc.send_path_select(((old_nodeX, old_nodeY), dir_abs))

                print(f"dir_abs = {dir_abs}, planetDirection = {planet.start[1]}, dir_rel = {dir_rel}")
                dir_abs = planet.start[1]
                dir_rel = (dir_abs - old_orientation) % 360
                old_orientation = dir_abs
                print("Status of path to be explored: ", planet.paths[planet.start[0]][dir_abs])

                print(f"Turn right {dir_rel / 90} times")
                follow.turn_right_x_times(dir_rel / 90)
                odo.gamma = math.radians(dir_abs)

                if is_color(current_color, rgb_red, 25):
                    print("\u001b[31mRED\u001b[0m")
                    follow.leds(ev3.Leds.RED)
                elif is_color(current_color, rgb_blue, 25):
                    print("\u001b[34mBLUE\u001b[0m")
                    follow.leds(ev3.Leds.GREEN)

                odo.old_m1 = 0
                odo.old_m2 = 0
                odo.new_m1 = 0
                odo.new_m2 = 0
                m1.position = 0
                m2.position = 0
                movement = []
            else:

                follow.follow(optimal, 250)

                if us.value() < 200:
                    follow.stop()
                    sd.beep()
                    print("\u001b[31mPATH BLOCKED\u001b[0m")
                    follow.path_blocked = True
                    blink()
                    sleep(1)

                    m1.run_forever(speed_sp=200)
                    m2.run_forever(speed_sp=-200)

                    follow.turn_right_x_times(2)
                    odo.gamma = odo.gamma_to_direction(odo.gamma + Direction.SOUTH)

                    follow.stop()
                    follow.stop()

                odo.old_m1 = odo.new_m1
                odo.old_m2 = odo.new_m2
                odo.new_m1 = m1.position
                odo.new_m2 = m2.position
                movement.append((odo.new_m1 - odo.old_m1, odo.new_m2 - odo.old_m2))
    except:
        try:
            print(gy.value())
        except OSError:
            print("gyro_sensor is broken")


# PLS EDIT

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--calibrate", action="store_true")
    args = parser.parse_args()

    run(calibrate=args.calibrate)
