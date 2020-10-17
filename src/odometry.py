# !/usr/bin/env python3
import math

import follow
from planet import Direction
from specials import colorCodes
from typing import List, Tuple


class Odometry:
    def __init__(self, gamma: float, posX: float, posY: float, movement: list, distBtwWheels):
        """
        Initializes odometry module
        """

        self.distBtwWheels: float = distBtwWheels
        self.gamma: float = gamma
        self.posX: float = posX
        self.posY: float = posY
        self.newM1 = 0
        self.newM2 = 0
        self.oldM1 = 0
        self.oldM2 = 0

    def gammaToDirection(self, gamma) -> Direction:
        """
        converts given gamma to a Direction using round and in range
        gamma -- angle in degree
        """
        gamma = (gamma + 3600) % 360
        gamma = round(gamma)
        if gamma in range(316, 360) or gamma in range(-45, 45):
            return Direction.NORTH
        elif gamma in range(46, 135):
            return Direction.EAST
        elif gamma in range(136, 225):
            return Direction.SOUTH
        elif gamma in range(226, 315):
            return Direction.WEST
        else:
            return self.gammaToDirection(gamma)

    def calculatePart(self, dR: int, dL: int):
        """
        iterates through movement array and calculates final position
        dL -- distance travelled by left wheel
        dR -- distance travelled by right wheel
        """
        dist = True

        if dist:
            dR = self.ditancePerTick(dR)
            dL = self.ditancePerTick(dL)
            alpha: float = ((dR - dL) / self.distBtwWheels)
            beta: float = alpha / 2
            if alpha != 0:
                straightDistance: float = ((dR + dL) / alpha) * math.sin(beta)
            else:
                straightDistance = dR
            dX = math.sin(self.gamma - beta) * straightDistance
            dY = math.cos(self.gamma - beta) * straightDistance
            if (self.gamma - alpha) % 2 * math.pi < 0:
                self.gamma = ((2 * math.pi) + self.gamma - alpha) % (2 * math.pi)
            else:
                self.gamma = (self.gamma - alpha) % (2 * math.pi)

            self.posX += dX
            self.posY += dY
        else:
            alpha: float = ((dR - dL) / self.distBtwWheels)
            beta: float = alpha / 2
            if alpha != 0:
                straightDistance: float = ((dR + dL) / alpha) * math.sin(beta)
            else:
                straightDistance = dR
            dX = math.sin(self.gamma - beta) * straightDistance
            dY = math.cos(self.gamma - beta) * straightDistance
            if (self.gamma - alpha) % 2 * math.pi < 0:
                self.gamma = ((2 * math.pi) + self.gamma - alpha) % (2 * math.pi)
            else:
                self.gamma = (self.gamma - alpha) % (2 * math.pi)

            self.posX += dX
            self.posY += dY

    def ditancePerTick(self, degree: int) -> int:
        """
        converts motordegree to centimeters
        """
        # 360° = 3*math.pi/360
        return round((3 * math.pi) / 360 * degree)

    def calculateNewPosition(self, moves: List[Tuple[int, int]]):
        """
        calculates all parts of the odometry movement array together
        """

        for i in moves:
            self.calculatePart(i[0], i[1])
        self.gamma = self.gammaToDirection(self.gamma * 180 / math.pi)
        print(f"not rounded X,Y = {self.posX}, {self.posY}")
        self.posX = round(self.posX / 50)
        self.posY = round(self.posY / 50)

        print(f"{colorCodes.green}X = {self.posX}, Y = {self.posY}, gamma = {self.gamma}{colorCodes.reset}")

        # for i in moves:
        #     self.calculatePart(i[0] / 360 * 9.424, i[1] / 360 * 9.424)
        # self.gamma = Direction(self.gammaToDirection(self.gamma * 180 / math.pi))
        # print(f"not rounded X,Y = {self.posX}, {self.posY}")
        # self.posX = round(self.posX / 50)
        # self.posY = round(self.posY / 50)
        #
        # print(f"{colorCodes.green}X = {self.posX}, Y = {self.posY}, gamma = {self.gamma}{colorCodes.reset}")
