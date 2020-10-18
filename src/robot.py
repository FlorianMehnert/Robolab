from enum import Enum
from time import sleep

import ev3dev.ev3 as ev3

class Robot:
    def __init__(self):
        self.m1: ev3.LargeMotor = ev3.LargeMotor('outB')
        self.m2: ev3.LargeMotor = ev3.LargeMotor('outC')
        self.cs: ev3.ColorSensor = ev3.ColorSensor()
        self.ts: ev3.TouchSensor = ev3.TouchSensor()
        self.gy: ev3.GyroSensor = ev3.GyroSensor()
        self.us: ev3.UltrasonicSensor = ev3.UltrasonicSensor()
        self.sd: ev3.Sound = ev3.Sound()
        self.rc: ev3.RemoteControl = ev3.RemoteControl()
        self.ps: ev3.PowerSupply = ev3.PowerSupply()
        print(f"Current battery is {self.ps.measured_volts}V")

    def stop_motor(self) -> None:
        """ stops both given Motors """
        self.m1.stop_action = "brake"
        self.m2.stop_action = "brake"
        self.m1.stop()
        self.m2.stop()

    def reset_motor(self):
        self.m1.position = 0
        self.m2.position = 0

    class ColorLED(tuple, Enum):
        BLACK = ev3.Leds.BLACK
        RED = ev3.Leds.RED
        GREEN = ev3.Leds.GREEN
        AMBER = ev3.Leds.AMBER
        ORANGE = ev3.Leds.ORANGE
        YELLOW = ev3.Leds.YELLOW

    def set_led(self, color: ColorLED):
        """
        sets both LED to the given color
        """

        ev3.Leds.set_color(ev3.Leds.LEFT, color)
        ev3.Leds.set_color(ev3.Leds.RIGHT, color)

    def blink(self):
        for i in range(2):
            ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.AMBER)
            ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.AMBER)
            sleep(0.1)
            ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.RED)
            ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.RED)
            sleep(0.1)
            ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.GREEN)
            ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.GREEN)
            sleep(0.1)
            ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.RED)
            ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.RED)
            sleep(0.1)
            ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.AMBER)
            ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.AMBER)

    def roll(self, motor: ev3.LargeMotor, direction):
        """
        used with remote control to relocate to robot faster during testing phase
        directly copied from https://sites.google.com/site/ev3python/learn_ev3_python/remote-control
        not used in exam
        """

        def on_press(state):
            if state:
                # Roll when button is pressed
                motor.run_forever(speed_sp=500 * direction)
            else:
                # Stop otherwise
                motor.stop(stop_action='brake')

        return on_press

    def remoteControl(self):
        """
        only used with Infrared Sensor
        see roll
        """
        self.rc.on_red_up = self.roll(self.m1, 1)
        self.rc.on_red_down = self.roll(self.m1, -1)
        self.rc.on_blue_up = self.roll(self.m2, 1)
        self.rc.on_blue_down = self.roll(self.m2, -1)

        while True:
            self.rc.process()
            sleep(0.01)

