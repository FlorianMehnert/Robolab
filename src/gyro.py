from time import sleep

import ev3dev.ev3 as ev3


class Gyro:
    def __init__(self, gyro: ev3.GyroSensor):
        self.gyro = gyro
        self.angle = gyro.angle

    def turnDegree(self, m1: ev3.LargeMotor, m2: ev3.LargeMotor, degree):
        m1.run_forever(speed_sp=100)
        m2.run_forever(speed_sp=-100)

        while abs(self.gyro.angle - self.angle) < degree:
            sleep(0.1)

        m1.stop()
        m2.stop()