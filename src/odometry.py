# !/usr/bin/env python3
import math
from typing import List, Tuple

from planet import Direction
from specials import color_codes


class Odometry:
    def __init__(self, gamma: float, posX: float, posY: float, movement: list, distBtwWheels):
        """
        Initializes odometry module
        """

        self.dist_btw_wheels: float = distBtwWheels
        self.gamma: float = gamma
        self.posX: float = posX
        self.posY: float = posY
        self.new_m1 = 0
        self.new_m2 = 0
        self.old_m1 = 0
        self.old_m2 = 0

    def gamma_to_direction(self, gamma) -> Direction:
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
            return self.gamma_to_direction(gamma)

    def calculate_part(self, dR: int, dL: int):
        """
        iterates through movement array and calculates final position
        dL -- distance travelled by left wheel
        dR -- distance travelled by right wheel
        """
        dist = True

        if dist:
            dR = self.ditance_per_tick(dR)
            dL = self.ditance_per_tick(dL)
            alpha: float = ((dL - dR) / self.dist_btw_wheels)  # gesamtes coord umrechnen mit -
            beta: float = alpha / 2
            if alpha != 0:
                straightDistance: float = ((dR + dL) / alpha) * math.sin(beta)
            else:
                straightDistance = dR
            dX = math.sin(self.gamma + beta) * straightDistance  # X spiegeln ohne -
            dY = math.cos(self.gamma + beta) * straightDistance
            if (self.gamma - alpha) % 2 * math.pi < 0:
                self.gamma = ((2 * math.pi) + self.gamma - alpha) % (2 * math.pi)
            else:
                self.gamma = (self.gamma - alpha) % (2 * math.pi)

            self.posX += dX
            self.posY += dY

    def ditance_per_tick(self, degree: int) -> float:
        """
        converts motordegree to centimeters
        """
        return (3 * math.pi) / 360 * degree

    def calculate_new_position(self, moves: List[Tuple[int, int]]):
        """
        calculates all parts of the odometry movement array together
        """

        for i in moves:
            self.calculate_part(i[0], i[1])
        self.gamma = self.gamma_to_direction(self.gamma * 180 / math.pi)
        print(f"not rounded X,Y = {self.posX}, {self.posY}")
        self.posX = round(self.posX / 50)
        self.posY = round(self.posY / 50)

        print(f"{color_codes.green}X = {self.posX}, Y = {self.posY}, gamma = {self.gamma}{color_codes.reset}")
