# !/usr/bin/env python3
from math import sin, cos


class Odometry:
    def __init__(self, gamma, posX, posY, movement, distBtwWheels=7.5):
        """
        Initializes odometry module
        """

        self.distBtwWheels: float = distBtwWheels
        self.gamma: float = gamma
        self.posX: float = posX
        self.posY: float = posY
        self.movement = movement

    def calculatePart(self, dR: float, dL: float):

        alpha: float = ((dR - dL) / self.distBtwWheels)
        beta: float = alpha / 2
        straightDistance: float = ((dR + dL) / alpha) * sin(beta)
        dX: float = -sin(self.gamma + beta) * straightDistance
        dY: float = cos(self.gamma + beta) * straightDistance
        self.gamma += alpha

        self.posX += dX
        self.posY += dY


    def calculatePosition(self, startingGamma):
        self.gamma = startingGamma
