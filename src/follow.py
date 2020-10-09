import math
from time import sleep

import ev3dev.ev3 as ev3

from gyro import Gyro


def isColor(currentColor, matchingColor, distance):
    match = True
    for i in range(3):
        if abs(currentColor[i] - matchingColor[i]) > distance:
            match = False
            break
    return match


def stop(m1: ev3.LargeMotor, m2: ev3.LargeMotor):
    m1.stop_action = "brake"
    m2.stop_action = "brake"
    m1.stop()
    m2.stop()


def findAttachedPaths(m1: ev3.LargeMotor, m2: ev3.LargeMotor, speed: int, pos: int, gyro: Gyro):

    m1.stop(stop_action="brake")
    m2.stop(stop_action="brake")

    m1.run_to_rel_pos(speed_sp=speed, position_sp=pos)
    m2.run_to_rel_pos(speed_sp=speed, position_sp=pos)

    m1.wait_until_not_moving()
    m2.wait_until_not_moving()

    gyro.turnDegree(m1,m2,360)


def wasd(m1: ev3.LargeMotor, m2: ev3.LargeMotor):
    while True:
        direction = input("")
        if direction == "w":
            m1.run_forever(speed_sp=400)
            m2.run_forever(speed_sp=400)
        elif direction == "s":
            m1.run_forever(speed_sp=-400)
            m2.run_forever(speed_sp=-400)
        elif direction == "a":
            m1.run_forever(speed_sp=-100)
            m2.run_forever(speed_sp=100)
        elif direction == "d":
            m1.run_forever(speed_sp=100)
            m2.run_forever(speed_sp=-100)
        elif direction == "exit":
            m1.stop()
            m2.stop()
            break
        else:
            m1.stop()
            m2.stop()


class Follow:
    def __init__(self, m1: ev3.LargeMotor, m2: ev3.LargeMotor, cs: ev3.ColorSensor, ts: ev3.TouchSensor):
        self.m1 = m1
        self.m2 = m2
        self.cs = cs
        self.ts = ts
        self.kp = .8

    def rgbToRefl(self, r, g, b):
        return (r + g + b) / 3

    def calibrate(self):
        self.cs.mode = "RGB-RAW"

        while not self.ts.is_pressed:
            sleep(0.1)

        while self.ts.is_pressed:
            sleep(0.1)

        rgbWhite = self.cs.bin_data("hhh")
        ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.BLACK)
        ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.BLACK)
        print("white set")

        while not self.ts.is_pressed:
            sleep(0.1)

        while self.ts.is_pressed:
            sleep(0.1)

        rgbBlack = self.cs.bin_data("hhh")
        ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.AMBER)
        ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.AMBER)
        print("black set")

        while not self.ts.is_pressed:
            sleep(0.1)

        while self.ts.is_pressed:
            sleep(0.1)

        rgbRed = self.cs.bin_data("hhh")
        ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.RED)
        ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.RED)
        print("red set")

        while not self.ts.is_pressed:
            sleep(0.1)

        while self.ts.is_pressed:
            sleep(0.1)

        rgbBlue = self.cs.bin_data("hhh")
        ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.GREEN)
        ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.GREEN)
        print("blue set")

        reflWhite = self.rgbToRefl(*rgbWhite)
        reflBlack = self.rgbToRefl(*rgbBlack)

        print("Black: " + str(reflBlack))
        print("White: " + str(reflWhite))

        while not self.ts.is_pressed:
            sleep(0.1)

        while self.ts.is_pressed:
            sleep(0.1)

        ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.AMBER)
        ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.AMBER)

        sleep(0.5)

        ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.GREEN)
        ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.GREEN)

        optimal = (reflWhite + reflBlack) / 2
        return rgbRed, rgbBlue, rgbWhite, rgbBlack, optimal

    def follow(self, optimal, baseSpeed):
        error = optimal - self.cs.value()
        output = self.kp * error
        self.m1.run_forever(speed_sp=baseSpeed + output)
        self.m2.run_forever(speed_sp=baseSpeed - output)
