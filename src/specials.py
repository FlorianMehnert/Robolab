from time import sleep
from enum import Enum
import ev3dev.ev3 as ev3
import follow


def blink():
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


def roll(motor, direction):
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


def remoteControl(rc: ev3.RemoteControl, m1: ev3.LargeMotor, m2: ev3.LargeMotor):
    """
    see roll
    """
    rc.on_red_up = roll(m1, 1)
    rc.on_red_down = roll(m1, -1)
    rc.on_blue_up = roll(m2, 1)
    rc.on_blue_down = roll(m2, -1)

    while True:  # replaces previous line so use Ctrl-C to exit
        rc.process()
        sleep(0.01)


def wasd(m1: ev3.LargeMotor, m2: ev3.LargeMotor) -> None:
    """
    very basic implementation of a wasd-control
    """
    speed = 1000
    while True:
        direction = input("")

        if direction == "w":
            m1.run_forever(speed_sp=speed)
            m2.run_forever(speed_sp=speed)
        elif direction == "s":
            m1.run_forever(speed_sp=-speed)
            m2.run_forever(speed_sp=-speed)
        elif direction == "a":
            m1.run_forever(speed_sp=-speed / 5)
            m2.run_forever(speed_sp=speed / 5)
        elif direction == "d":
            m1.run_forever(speed_sp=speed / 5)
            m2.run_forever(speed_sp=-speed / 5)
        elif direction == "exit":
            m1.stop()
            m2.stop()
            break
        else:
            m1.stop()
            m2.stop()


def menu(follow: follow, calibrate):
    if calibrate:
        mode = "calibrate"
    else:
        mode = input("mode?")
    if mode == "wasd":
        wasd(follow.m1, follow.m2)
    elif mode == "paths":
        follow.findAttachedPaths()
    elif mode == "battery":
        print(follow.ps.measured_volts)
    elif mode == "/help":
        print("wasd, paths, battery, calibrate, sop, pid")
    elif mode == "sop":
        while not follow.ts.is_pressed:
            continue
    elif mode == "pid":
        k = input("kp, ki, kp")
        if k == "p":
            follow.kp = float(input("proportional?"))
        elif k == "i":
            follow.ki = float(input("integral?"))
        elif k == "d":
            follow.kd = float(input("derivate?"))
    elif mode == "calibrate":
        with open("/home/robot/src/values.txt", mode="w") as file:
            for i in follow.calibrate():
                file.write(f"{i}\n")
    elif mode == "follow":
        while True:
            follow.follow(optimal=171.5, baseSpeed=200)
    elif mode == "StarWars":
        follow.sd.tone([
            (392, 350, 100), (392, 350, 100), (392, 350, 100), (311.1, 250, 100),
            (466.2, 25, 100), (392, 350, 100), (311.1, 250, 100), (466.2, 25, 100),
            (392, 700, 100), (587.32, 350, 100), (587.32, 350, 100),
            (587.32, 350, 100), (622.26, 250, 100), (466.2, 25, 100),
            (369.99, 350, 100), (311.1, 250, 100), (466.2, 25, 100), (392, 700, 100),
            (784, 350, 100), (392, 250, 100), (392, 25, 100), (784, 350, 100),
            (739.98, 250, 100), (698.46, 25, 100), (659.26, 25, 100),
            (622.26, 25, 100), (659.26, 50, 400), (415.3, 25, 200), (554.36, 350, 100),
            (523.25, 250, 100), (493.88, 25, 100), (466.16, 25, 100), (440, 25, 100),
            (466.16, 50, 400), (311.13, 25, 200), (369.99, 350, 100),
            (311.13, 250, 100), (392, 25, 100), (466.16, 350, 100), (392, 250, 100),
            (466.16, 25, 100), (587.32, 700, 100), (784, 350, 100), (392, 250, 100),
            (392, 25, 100), (784, 350, 100), (739.98, 250, 100), (698.46, 25, 100),
            (659.26, 25, 100), (622.26, 25, 100), (659.26, 50, 400), (415.3, 25, 200),
            (554.36, 350, 100), (523.25, 250, 100), (493.88, 25, 100),
            (466.16, 25, 100), (440, 25, 100), (466.16, 50, 400), (311.13, 25, 200),
            (392, 350, 100), (311.13, 250, 100), (466.16, 25, 100),
            (392.00, 300, 150), (311.13, 250, 100), (466.16, 25, 100), (392, 700)
        ])


class colorCodes(str, Enum):
    black = "\u001b[30m"
    red = "\u001b[31m"
    green = "\u001b[32m"
    yellow = "\u001b[33m"
    blue = "\u001b[34m"
    magenta = "\u001b[35m"
    cyan = "\u001b[36m"
    white = "\u001b[37m"
    reset = "\u001b[0m"
