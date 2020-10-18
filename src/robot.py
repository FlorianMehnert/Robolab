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
        self.ps: ev3.PowerSupply = ev3.PowerSupply()
        print(f"Current battery is {robot.ps.measured_volts}V")
