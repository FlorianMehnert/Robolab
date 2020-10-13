from time import sleep
from typing import Dict, Tuple

import ev3dev.ev3 as ev3

from odometry import Odometry


def isColor(currentColor: tuple, matchingColor: tuple, distance: int) -> bool:
    """
    currentColor -- rgb Tuple of the current color
    matchingColor -- rgb Tuple of the given Color
    distance -- maximum value difference between both colors the return true
    compares the color the color-sensor detects at the moment with another given color and returns whether the current color matches the given color
    """

    match = True
    for i in range(3):
        if abs(currentColor[i] - matchingColor[i]) > distance:
            match = False
            break

    return match


def convPathsToDirection(dircts: Dict) -> int:
    """
    dircts -- directions dictionary with following structure: {North: bool, East: bool, South: bool, West:bool}
    conversion function used in findAttachedPaths
    """
    if dircts["North"]:
        return 0
    elif dircts["East"]:
        return 1
    elif dircts["West"]:
        return -1
    else:
        return 2


def isBlack(rgb: (int, int, int)):
    val = (rgb[0] + rgb[1] + rgb[2]) / 3
    if val > 100:
        return False
    else:
        return True


class Follow:
    def __init__(self, m1: ev3.LargeMotor, m2: ev3.LargeMotor, cs: ev3.ColorSensor, ts: ev3.TouchSensor,
                 gy: ev3.GyroSensor, movement: list, rc: ev3.RemoteControl = None) -> None:
        self.m1 = m1
        self.m2 = m2
        self.cs = cs
        self.ts = ts
        self.gy = gy
        self.kp = .8
        self.rgbBlack = (34, 78, 33)
        self.rc = rc
        self.movement = movement

    def stop(self) -> None:
        """
        stops both given Motors
        """
        self.m1.stop_action = "brake"
        self.m2.stop_action = "brake"
        self.m1.stop()
        self.m2.stop()

    def reset(self):
        self.m1.position = 0
        self.m2.position = 0

    def touchPause(self):
        """
        uses touch-sensor to simulate a pause
        """
        while not self.ts.is_pressed:
            sleep(0.1)

        while self.ts.is_pressed:
            sleep(0.1)

    def leds(self, color: ev3.Leds):
        """
        sets both LED to the given color
        """

        ev3.Leds.set_color(ev3.Leds.LEFT, color)
        ev3.Leds.set_color(ev3.Leds.RIGHT, color)

    def rgbToRefl(self, r: int, g: int, b: int) -> float:
        return (r + g + b) / 3

    def calibrate(self) -> Tuple[tuple, tuple, tuple, tuple, float]:
        """
        lets the user manually calibrate the color-sensor by measuring the rgb-values from white, black, red, and blue
        returns rgbRed, rgbBlue, rgbWhite, rgbBlack and the median of white and black
        """
        self.cs.mode = "RGB-RAW"

        self.leds(ev3.Leds.YELLOW)
        self.touchPause()
        print("white")
        rgbWhite = self.cs.bin_data("hhh")

        self.leds(ev3.Leds.BLACK)
        self.touchPause()
        print("black")
        rgbBlack = self.cs.bin_data("hhh")

        self.leds(ev3.Leds.RED)
        self.touchPause()
        print("red")
        rgbRed = self.cs.bin_data("hhh")

        self.leds(ev3.Leds.GREEN)
        self.touchPause()
        print("blue")
        rgbBlue = self.cs.bin_data("hhh")

        refWhite = self.rgbToRefl(*rgbWhite)
        refBlack = self.rgbToRefl(*rgbBlack)

        self.touchPause()
        optimal = (refWhite + refBlack) / 2
        sleep(1)

        return rgbRed, rgbBlue, rgbWhite, rgbBlack, optimal

    def follow(self, optimal, baseSpeed, odo: Odometry):
        """
        currently p-Controller
        optimal -- medium value between calibrated white and black
        baseSpeed -- how fast should the robot go
        """

        error = optimal - self.cs.value()
        output = self.kp * error
        self.m1.run_forever(speed_sp=baseSpeed + output)
        self.m2.run_forever(speed_sp=baseSpeed - output)

    def turnRightXTimes(self, x=0):
        """
        x -- how often should the robot rotate (default 0)
        used for turning the robot after it reaches a crossing to a path
        """

        if x == 0:
            return

        degreeFor90 = 272
        speed = 200

        if x in (1, -1):
            self.m1.run_forever(speed_sp=speed * x)
            self.m2.run_forever(speed_sp=-speed * x)
        else:
            self.m1.run_forever(speed_sp=speed)
            self.m2.run_forever(speed_sp=-speed)

        self.m1.position = 0

        while self.m1.position < abs(x) * degreeFor90:
            sleep(0.1)

    def findAttachedPaths(self) -> Dict[str, bool]:
        """
        finds attached paths to discovered knots by turning 360° and repositions the robot to the next viable path
        """

        dirDict = {"North": False, "East": False, "South": False, "West": False}

        self.m1.stop(stop_action="brake")
        self.m2.stop(stop_action="brake")

        self.m1.run_to_rel_pos(speed_sp=200, position_sp=230)
        self.m2.run_to_rel_pos(speed_sp=-200, position_sp=230)

        self.m1.wait_until_not_moving()

        self.m1.run_forever(speed_sp=250)
        self.m2.run_forever(speed_sp=-250)

        self.m1.position = 0
        self.m2.position = 0

        while self.m1.position < 1115:
            binData = self.cs.bin_data("hhh")
            if (self.m1.position in range(0, 135) or self.m1.position in range(980, 1200)) and isBlack(binData):
                dirDict["North"] = True
            elif self.m1.position in range(143, 413) and isBlack(binData):
                dirDict["East"] = True
            elif self.m1.position in range(422, 692) and isBlack(binData):
                dirDict["South"] = True
            elif self.m1.position in range(701, 971) and isBlack(binData):
                dirDict["West"] = True
            sleep(0.05)

        print(dirDict)
        return dirDict
