from time import sleep

import ev3dev.ev3 as ev3


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
    def __init__(self, m1: ev3.LargeMotor, m2: ev3.LargeMotor, cs: ev3.ColorSensor, ts: ev3.TouchSensor, gy: ev3.GyroSensor, rc: ev3.RemoteControl = None):
        self.m1 = m1
        self.m2 = m2
        self.cs = cs
        self.ts = ts
        self.gy = gy
        self.kp = .8
        self.rgbBlack = (34, 78, 33)
        self.rc = rc


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

    def isBlack(self, rgb:(int,int,int)):
        val = (rgb[0] + rgb[1] + rgb[2])/3
        if val > 100:
            return False
        else:
            return True

    def findAttachedPaths(self):
        dirDict = {"North": False, "East": False, "South": False, "West": False}
        self.m1.stop(stop_action="brake")
        self.m2.stop(stop_action="brake")

        self.m1.run_to_rel_pos(speed_sp=200, position_sp=230)
        self.m2.run_to_rel_pos(speed_sp=-200, position_sp=230)

        self.m1.wait_until_not_moving()

        self.m1.run_forever(speed_sp=150)
        self.m2.run_forever(speed_sp=-150)


        startingAngle = self.gy.angle
        currentAngle = 0
        while currentAngle < 370:
            if (currentAngle in range(316, 360) or currentAngle in range(0, 45)) and self.isBlack(self.cs.bin_data("hhh")):
                dirDict["North"] = True
            elif currentAngle in range(46, 135) and self.isBlack(self.cs.bin_data("hhh")):
                dirDict["East"] = True
            elif (currentAngle in range(136, 225)) and self.isBlack(self.cs.bin_data("hhh")):
                dirDict["South"] = True
            elif (currentAngle in range(226, 315)) and self.isBlack(self.cs.bin_data("hhh")):
                dirDict["West"] = True
            sleep(0.15)
            currentAngle = abs(self.gy.angle - startingAngle)

        print(dirDict)

    def roll(self, motor, direction):
        def on_press(state):
            if state:
                # Roll when button is pressed
                motor.run_forever(speed_sp=500 * direction)
            else:
                # Stop otherwise
                motor.stop(stop_action='brake')

        return on_press

    def remoteControl(self):
        self.rc.on_red_up = self.roll(self.m1, 1)
        self.rc.on_red_down = self.roll(self.m1, -1)
        self.rc.on_blue_up = self.roll(self.m2, 1)
        self.rc.on_blue_down = self.roll(self.m2, -1)

        while True:  # replaces previous line so use Ctrl-C to exit
            self.rc.process()
            sleep(0.01)

        # Press Ctrl-C to exit