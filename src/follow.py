from time import sleep
from typing import Dict, Tuple, List
from planet import Direction
import random
import ev3dev.ev3 as ev3


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


def isBlack(rgb: (int, int, int)):
    val = (rgb[0] + rgb[1] + rgb[2]) / 3
    if val > 100:
        return False
    else:
        return True


class Follow:
    def __init__(self, m1: ev3.LargeMotor, m2: ev3.LargeMotor, cs: ev3.ColorSensor, ts: ev3.TouchSensor,
                 gy: ev3.GyroSensor, movement: list, ps: ev3.PowerSupply, sd: ev3.Sound,
                 rc: ev3.RemoteControl = None) -> None:
        self.m1 = m1
        self.m2 = m2
        self.cs = cs
        self.ts = ts
        self.gy = gy
        self.rc = rc
        self.ps = ps
        self.sd = sd
        self.movement = movement

        self.rgbBlack = (34, 78, 33)
        self.pathBlocked = False
        self.integral = 0
        self.previousError = 0

        self.kp = 0.8
        self.ki = 0.01
        self.kd = 0.03

    def convStrToRGB(self, s: str):
        valTemp = ""
        rgbTemp = []
        rgb: Tuple[float, float, float]
        s.replace("\n", "")

        for character in s:
            if character == "," or character == ")":
                val = float(valTemp)
                rgbTemp.append(val)
                valTemp = ""
            elif character == "(" or character == " ":
                pass
            else:
                valTemp += character
        rgb = (rgbTemp[0], rgbTemp[1], rgbTemp[2])
        return rgb

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

    def follow(self, optimal, baseSpeed):
        """
        currently p-Controller
        optimal -- medium value between calibrated white and black
        baseSpeed -- how fast should the robot go
        """
        error = optimal - self.cs.value()
        self.integral += error
        derivate = error - self.previousError
        output = self.kp * error + self.ki * self.integral + self.kd * derivate
        previousError = error
        self.m1.run_forever(speed_sp=baseSpeed + output)
        self.m2.run_forever(speed_sp=baseSpeed - output)

    def turnRightXTimes(self, x=0):
        """
        x -- how often should the robot rotate (default 0)
        used for turning the robot after it reaches a crossing to a path
        """

        if x == 0:
            return

        degreeFor90 = 280
        speed = 200

        if x in (1, -1):
            self.m1.run_forever(speed_sp=speed * x)
            self.m2.run_forever(speed_sp=-speed * x)
        else:
            self.m1.run_forever(speed_sp=speed)
            self.m2.run_forever(speed_sp=-speed)

        self.m1.position = 0
        while abs(self.m1.position) < abs(x * degreeFor90):
            sleep(0.1)
        self.stop()

    def findAttachedPaths(self) -> List[Direction]:
        """
        finds attached paths to discovered knots by turning 360° and repositions the robot to the next viable path
        """

        self.stop()
        self.m1.run_to_rel_pos(speed_sp=200, position_sp=270)
        self.m2.run_to_rel_pos(speed_sp=-200, position_sp=270)
        self.m1.wait_until_not_moving()
        self.m1.position = 0
        self.m2.position = 0
        self.m1.run_forever(speed_sp=270)
        self.m2.run_forever(speed_sp=-270)

        dirList: List[Direction] = []
        pathArray: List[int] = []

        while self.m1.position < 1100:
            binData = self.cs.bin_data("hhh")
            if isBlack(binData):
                pathArray.append(self.m1.position)

        for i in pathArray:
            if (i in range(0,100) or i in range(1000,1100)) and Direction.NORTH not in dirList:
                dirList.append(Direction.NORTH)
            elif i in range(175,375) and Direction.EAST not in dirList:
                dirList.append(Direction.EAST)
            elif i in range(450,650) and Direction.SOUTH not in dirList:
                dirList.append(Direction.SOUTH)
            elif i in range(725, 925) and Direction.WEST not in dirList:
                dirList.append(Direction.WEST)

        self.stop()
        self.m1.wait_until_not_moving()
        print(f"in findAttachedPaths =  {dirList}")
        return dirList

    def gammaRelToAbs(self, dirList: List[Direction], gamma: int):
        dList = dirList[:]
        cnt = 0
        for dir in dList:
            dList[cnt] = Direction((dir + gamma)%360)
            cnt += 1
        return dList

    def removeDoubles(self, dirList: List[Direction]):
        doubles = []
        for i in dirList:
            if i in doubles:
                continue
            else:
                doubles.append(i)
        return doubles

    def selectPath(self, dirList: List[Direction]) -> Direction:
        """
        selects one path from all discovered paths for one knot
        """
        dirList1 = dirList

        print(f"in selectPath dirList is: {dirList1}")
        if len(dirList1) == 1 and Direction.SOUTH in dirList1:
            path = Direction.SOUTH
        elif len(dirList1) == 0:
            # should never happen
            print("some path was not detected!")
            path = Direction.SOUTH
        else:
            try:
                dirList1.remove(Direction.SOUTH)
            except ValueError:
                pass
            path = random.choice(dirList1)
        return path

