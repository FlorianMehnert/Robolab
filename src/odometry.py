# !/usr/bin/env python3
import math

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

    def calculatePart(self, dR: float, dL: float):
        """
        iterates through movement array and calculates final position
        dL -- distance travelled by left wheel
        dR -- distance travelled by right wheel
        """

        alpha: float = ((dR - dL) / self.distBtwWheels)
        beta: float = alpha / 2
        if alpha != 0:
            straightDistance: float = ((dR + dL) / alpha) * math.sin(beta)
        else:
            straightDistance = dR
        dX = math.sin(self.gamma + beta) * straightDistance
        dY = math.cos(self.gamma + beta) * straightDistance
        self.gamma -= alpha

        self.posX += dX
        self.posY += dY

    def calculateNewPosition(self, moves: List[Tuple[int, int]]):
        for i in moves:
            self.calculatePart(i[0]*9.424/360, i[1]*9.424/360)
        print(self.posX, self.posY, self.gamma*180/math.pi, "odometry calculated new position")

