from enum import Enum
from time import sleep

import ev3dev.ev3 as ev3


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
    only used with Infrared Sensor
    see roll
    """
    rc.on_red_up = roll(m1, 1)
    rc.on_red_down = roll(m1, -1)
    rc.on_blue_up = roll(m2, 1)
    rc.on_blue_down = roll(m2, -1)

    while True:  # replaces previous line so use Ctrl-C to exit
        rc.process()
        sleep(0.01)




class colorCodes(str, Enum):
    """
    Ansi Escapesequences for better debugging experience ;)
    """
    black = "\u001b[30m"
    red = "\u001b[31m"
    green = "\u001b[32m"
    yellow = "\u001b[33m"
    blue = "\u001b[34m"
    magenta = "\u001b[35m"
    cyan = "\u001b[36m"
    white = "\u001b[37m"
    reset = "\u001b[0m"
    bblack = "\u001b[40m"
    bred = "\u001b[41m"
    bgreen = "\u001b[42m"
    byellow = "\u001b[43m"
    bblue = "\u001b[44m"
    bmagenta = "\u001b[45m"
    bcyan = "\u001b[46m"
    bwhite = "\u001b[47m"

class Sound(str, Enum):
    """
    Sound snippets
    """
    starWars = [
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
                ]
    