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