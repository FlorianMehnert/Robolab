#!/usr/bin/env python3
import argparse
import logging
import math
import os
import uuid
from pprint import pprint
from time import sleep, time
from typing import Tuple, List

import ev3dev.ev3 as ev3
import paho.mqtt.client as mqtt

import specials
from communication import Communication
from follow import Follow
from odometry import Odometry
from planet import Planet, Direction
from color import ColorPrint as Color
from specials import star_wars_sound
from robot import Robot

client = None  # DO NOT EDIT



def run(calibrate=False):
    # DO NOT CHANGE THESE VARIABLES
    #
    # The deploy-script uses the variable "client" to stop the mqtt-client after your program stops or crashes.
    # Your script isn't able to close the client after crashing.
    global client

    log_file = os.path.realpath(__file__) + '/../../logs/project.log'
    logging.basicConfig(filename=log_file,  # Define log file
                        level=logging.INFO,  # Define default mode
                        format='%(asctime)s: %(message)s'  # Define default logging format
                        )
    logger = logging.getLogger('RoboLab')

    # THIS IS WHERE PARADISE BEGINS
    start_time = time()
    robot = Robot()
    planet = Planet()
    mqttc = Communication(client, '217', logger, planet)
    movement: List[Tuple[int, int]] = []
    # used to save all movement values gathered while line following for odometry calculations

    follow = Follow(robot, movement)
    odo = Odometry(gamma=0, pos_x=0, pos_y=0, dist_btw_wheels=9.2)
    robot.reset_motor()

    try:
        follow.menu(calibrate, robot.sd)

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

        robot.cs.mode = "RGB-RAW"
        current_color = robot.cs.bin_data("hhh")

        if follow.is_color(current_color, rgb_red, 25) or follow.is_color(current_color, rgb_blue, 30):
            # discovers node
            node_count += 1
            robot.stop_motor()
            robot.stop_motor()
            print(f"{Color.byellow}{node_count}.node{Color.reset}")
            if planet.new_planet:
                # first node discovered
                mqttc.send_ready()
                mqttc.timeout()
                sleep(1)

                # only works because while loops is very fast... the faster the while the slower the less does the robot roll
                # TODO: fix m1 and m2 only getting stopped by follow and wait for m1/m2 to stop
                robot.m1.run_to_rel_pos(speed_sp=1000, position_sp=1000)
                robot.m2.run_to_rel_pos(speed_sp=1000, position_sp=1000)
                # print(
                #     f"serverX = {old_nodeX}, serverY = {old_nodeY}, {Color.red}"
                #     f"serverDirection = {Color.reset} {old_orientation}, "
                #     f"odoX = {odo.posX}, odoY = {odo.pos_y}, {Color.red}"
                #     f"odoDirection ={Color.reset} {odo.gamma}")

            else:
                if follow.path_blocked:
                    # sends blocked path when ultrasonic sensor detected an obstacle (uses old values for target)
                    mqttc.send_path(((old_nodeX, old_nodeY), old_orientation), ((old_nodeX, old_nodeY), old_orientation),
                                    status="blocked")
                    follow.path_blocked = False

                else:
                    # sends just discovered path
                    if planet.is_known_path((old_nodeX, old_nodeY), old_orientation):
                        mqttc.send_path(((old_nodeX, old_nodeY), old_orientation),
                                        planet.get_path_target((old_nodeX, old_nodeY), old_orientation),
                                        "free")
                    else:
                        # any other node discovered
                        odo.calculate_new_position(movement)
                        print(
                            f"{Color.reset}BEFORE: odoX and odoY{odo.posX, odo.posY} aswell as oldNodeX and oldNodeY {old_nodeX, old_nodeY}{Color.reset}")
                        odo.posX += old_nodeX
                        odo.posY += old_nodeY
                        print(
                            f"{Color.reset}AFTER: odoX and odoY{odo.posX, odo.posY}{Color.reset}")
                        # updates odo.poX, odo.pos_y, odo.gamma

                        # prints every position data
                        print(
                            f"serverX = {old_nodeX}, serverY = {old_nodeY}"
                            f"serverDirection = {old_orientation}, "
                            f"odoX = {odo.posX}, odoY = {odo.posY}, "
                            f"odoDirection ={Color.reset} {odo.gamma}")
                        mqttc.send_path(((old_nodeX, old_nodeY), old_orientation),
                                        ((round(odo.posX), round(odo.posY)), odo.gamma_to_direction(odo.gamma + 180)),
                                        "free")

            # Target reached
            if planet.target is not None:
                if planet.target == planet.start[0]:
                    mqttc.send_target_reached()
                    print("Target reached")
                    pprint(planet.paths, indent=2)
                    driving_time = time() - start_time
                    print(f"Robot is {int(driving_time // 60)}:{driving_time % 60}")
                    robot.sd.tone(star_wars_sound)
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
                # print("Node unknown")
                relative_paths = follow.find_attached_paths()
                absolute_paths = follow.gamma_rel_to_abs(relative_paths, old_orientation)
                planet.set_attached_paths((old_nodeX, old_nodeY), absolute_paths)
            else:
                robot.m1.run_to_rel_pos(speed_sp=200, position_sp=280)
                robot.m2.run_to_rel_pos(speed_sp=-200, position_sp=280)
                # print("Node already known")
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
                driving_time = time() - start_time
                print(f"Robot has driven {int(driving_time // 60)}:{driving_time % 60}.")
                robot.sd.tone(star_wars_sound)
                break

            dir_rel: Direction = odo.gamma_to_direction(dir_abs + round(odo.gamma))

            # print(f"{Color.red}selected: {dir_rel}{Color.reset}, "
            #       f"{Color.blue}absolute: {dir_abs}{Color.reset}")

            # sends selected path
            # might cause planet update which leads to us needing to update our internal orientation
            mqttc.send_path_select(((old_nodeX, old_nodeY), dir_abs))

            print(f"dir_abs = {dir_abs}, planetDirection = {planet.start[1]}, dir_rel = {dir_rel}")
            dir_abs = planet.start[1]
            dir_rel = (dir_abs - old_orientation) % 360
            old_orientation = dir_abs
            print("Status of path to be explored: ", planet.paths[planet.start[0]][dir_abs])

            # print(f"Turn right {dir_rel / 90} times")
            follow.turn(dir_rel / 90)
            odo.gamma = math.radians(dir_abs)

            if follow.is_color(current_color, rgb_red, 25):
                print("\u001b[31mRED\u001b[0m")
                robot.set_led(robot.ColorLED.RED)
            elif follow.is_color(current_color, rgb_blue, 25):
                print("\u001b[34mBLUE\u001b[0m")
                robot.set_led(robot.ColorLED.GREEN)

            odo.old_m1 = 0
            odo.old_m2 = 0
            odo.new_m1 = 0
            odo.new_m2 = 0
            robot.m1.position = 0
            robot.m2.position = 0
            movement = []
        else:

            follow.follow(optimal, 200)

            if robot.us.value() < 200:
                robot.stop_motor()
                robot.sd.beep()
                print("\u001b[31mPATH BLOCKED\u001b[0m")
                follow.path_blocked = True
                robot.blink()
                sleep(1)

                robot.m1.run_forever(speed_sp=200)
                robot.m2.run_forever(speed_sp=-200)

                follow.turn(2)

                odo.gamma = odo.gamma_to_direction(odo.gamma + Direction.SOUTH)

                robot.stop_motor()

            odo.old_m1 = odo.new_m1
            odo.old_m2 = odo.new_m2
            odo.new_m1 = robot.m1.position
            odo.new_m2 = robot.m2.position
            movement.append((odo.new_m1 - odo.old_m1, odo.new_m2 - odo.old_m2))

# PLS EDIT

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--calibrate", action="store_true")
    args = parser.parse_args()

    run(calibrate=args.calibrate)
