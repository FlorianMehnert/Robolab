from time import sleep

import ev3dev.ev3 as ev3
import follow

m1 = ev3.LargeMotor("outB")
m2 = ev3.LargeMotor("outC")
cs = ev3.ColorSensor()
ty = ev3.TouchSensor()
gy = ev3.GyroSensor()
movement = []

follow = follow.Follow(m1, m2, cs, ty, gy, movement)
print(follow.findAttachedPaths())