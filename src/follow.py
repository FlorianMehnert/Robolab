from time import sleep
from typing import Tuple, List
from planet import Direction
from robot import Robot
from specials import star_wars_sound
import ev3dev.ev3 as ev3


def is_color(current_color: tuple, matching_color: tuple, distance: int) -> bool:
    """
    currentColor -- rgb Tuple of the current color
    matchingColor -- rgb Tuple of the given Color
    distance -- maximum value difference between both colors the return true
    compares the color the color-sensor detects at the moment with another given color and returns whether the current color matches the given color
    """

    match = True
    for i in range(3):
        if abs(current_color[i] - matching_color[i]) > distance:
            match = False
            break

    return match


def is_black(rgb: (int, int, int)) -> bool:
    """
    returns weather any
    """
    val = (rgb[0] + rgb[1] + rgb[2]) / 3
    if val > 100:
        return False
    else:
        return True


class Follow:
    def __init__(self, robot: Robot, movement: list) -> None:
        self.robot = robot
        self.movement = movement

        self.rgb_black = (34, 78, 33)
        self.path_blocked = False
        self.integral = 0
        self.previous_error = 0

        self.kp = 1
        self.ki = 0.01
        self.kd = 0.03
        self.increase = 0

    def conv_str_to_rgb(self, s: str):
        """
        used to interpret strings as rgb
        """
        val_temp = ""
        rgb_temp = []
        rgb: Tuple[float, float, float]
        s.replace("\n", "")

        for character in s:
            if character == "," or character == ")":
                val = float(val_temp)
                rgb_temp.append(val)
                val_temp = ""
            elif character == "(" or character == " ":
                pass
            else:
                val_temp += character
        rgb = (rgb_temp[0], rgb_temp[1], rgb_temp[2])
        return rgb

    def stop(self) -> None:
        """
        stops both given Motors
        """
        self.robot.m1.stop_action = "brake"
        self.robot.m2.stop_action = "brake"
        self.robot.m1.stop()
        self.robot.m2.stop()

    def reset(self):
        self.robot.m1.position = 0
        self.robot.m2.position = 0

    def touch_pause(self):
        """
        uses touch-sensor to simulate a pause
        """
        while not self.robot.ts.is_pressed:
            sleep(0.1)

        while self.robot.ts.is_pressed:
            sleep(0.1)

    def leds(self, color: ev3.Leds):
        """
        sets both LED to the given color
        """

        ev3.Leds.set_color(ev3.Leds.LEFT, color)
        ev3.Leds.set_color(ev3.Leds.RIGHT, color)

    def rgb_to_refl(self, r: int, g: int, b: int) -> float:
        """
        convert rgb values to reflective values
        """
        return (r + g + b) / 3

    def calibrate(self) -> Tuple[tuple, tuple, tuple, tuple, float]:
        """
        lets the user manually calibrate the color-sensor by measuring the rgb-values from white, black, red, and blue
        returns rgb_red, rgb_blue, rgb_white, rgb_black and the median of white and black
        """
        self.robot.cs.mode = "RGB-RAW"

        self.leds(ev3.Leds.YELLOW)
        self.touch_pause()
        print("white")
        rgb_white = self.robot.cs.bin_data("hhh")

        self.leds(ev3.Leds.BLACK)
        self.touch_pause()
        print("black")
        rgb_black = self.robot.cs.bin_data("hhh")

        self.leds(ev3.Leds.RED)
        self.touch_pause()
        print("red")
        rgb_red = self.robot.cs.bin_data("hhh")

        self.leds(ev3.Leds.GREEN)
        self.touch_pause()
        print("blue")
        rgb_blue = self.robot.cs.bin_data("hhh")

        ref_white = self.rgb_to_refl(*rgb_white)
        ref_black = self.rgb_to_refl(*rgb_black)

        self.touch_pause()
        optimal = (ref_white + ref_black) / 2
        sleep(1)

        return rgb_red, rgb_blue, rgb_white, rgb_black, optimal

    def follow(self, optimal, baseSpeed):
        """
        currently p-Controller
        optimal -- medium value between calibrated white and black
        baseSpeed -- how fast should the robot go
        """

        error = optimal - self.robot.cs.value()
        # if self.integral != 0:
        #     baseSpeed += abs(5000 / self.integral)
        #     if baseSpeed > 500:
        #         baseSpeed = 500
        #     print(baseSpeed, self.integral)
        if self.integral + error > 6000:
            pass
        else:
            self.integral += error
        derivate = error - self.previous_error
        output = self.kp * error + self.ki * self.integral + self.kd * derivate
        self.previous_error = error

        self.robot.m1.run_forever(speed_sp=output + baseSpeed)
        self.robot.m2.run_forever(speed_sp=-output + baseSpeed)

    def turn(self, x=0):
        """
        x -- how often should the robot rotate (default 0)
        used for turning the robot after it reaches a crossing to a path
        """

        degree_for90 = 280
        speed = 200

        if x in (1, -1):
            self.robot.m1.run_forever(speed_sp=speed * x)
            self.robot.m2.run_forever(speed_sp=-speed * x)
        else:
            self.robot.m1.run_forever(speed_sp=speed)
            self.robot.m2.run_forever(speed_sp=-speed)

        self.robot.m1.position = 0
        while abs(self.robot.m1.position) < abs(x * degree_for90):
            sleep(0.1)
        self.stop()

    def find_attached_paths(self) -> List[Direction]:
        """
        finds attached paths to discovered knots by turning 360° and repositions the robot to the next viable path
        """

        self.stop()
        self.robot.m1.run_to_rel_pos(speed_sp=200, position_sp=300)
        self.robot.m2.run_to_rel_pos(speed_sp=-200, position_sp=300)
        self.robot.m1.wait_until_not_moving()
        self.robot.m1.position = 0
        self.robot.m2.position = 0
        self.robot.m1.run_forever(speed_sp=270)
        self.robot.m2.run_forever(speed_sp=-270)

        dir_list: List[Direction] = []
        path_array: List[int] = []

        while self.robot.m1.position < 1100:
            bin_data = self.robot.cs.bin_data("hhh")
            if is_black(bin_data):
                path_array.append(self.robot.m1.position)

        for i in path_array:
            if (i in range(0, 100) or i in range(1000, 1100)) and Direction.NORTH not in dir_list:
                dir_list.append(Direction.NORTH)
            elif i in range(175, 375) and Direction.EAST not in dir_list:
                dir_list.append(Direction.EAST)
            elif i in range(450, 650) and Direction.SOUTH not in dir_list:
                dir_list.append(Direction.SOUTH)
            elif i in range(725, 925) and Direction.WEST not in dir_list:
                dir_list.append(Direction.WEST)

        self.stop()
        self.robot.m1.wait_until_not_moving()
        print(f"in findAttachedPaths =  {dir_list}")
        return dir_list

    def gamma_rel_to_abs(self, dir_list: List[Direction], gamma: int):
        d_list = dir_list[:]
        cnt = 0
        for dir in d_list:
            d_list[cnt] = Direction((dir + gamma)%360)
            cnt += 1
        return d_list

    def wasd(self):
        """
        very basic implementation of a wasd-control
        """
        speed = 1000
        while True:
            direction = input("")

            if direction == "w":
                #self.gyro_straight(s1=speed, s2=speed, kp=10)
                self.robot.m1.run_forever(speed_sp=speed)
                self.robot.m2.run_forever(speed_sp=speed)
            elif direction == "s":
                #self.gyro_straight(s1=-speed, s2=-speed, kp=10)
                self.robot.m1.run_forever(speed_sp=-speed)
                self.robot.m2.run_forever(speed_sp=-speed)
            elif direction == "a":
                self.robot.m1.run_forever(speed_sp=-speed / 5)
                self.robot.m2.run_forever(speed_sp=speed / 5)
            elif direction == "d":
                self.robot.m1.run_forever(speed_sp=speed / 5)
                self.robot.m2.run_forever(speed_sp=-speed / 5)
            elif direction == "exit":
                self.stop()
                self.stop()
                break
            else:
                self.stop()

    def gyro_straight(self, s1, s2, kp):
        self.robot.gy.mode = 'GYRO-CAL'
        sleep(2)
        self.robot.gy.mode = 'GYRO-ANG'
        print(self.robot.gy.value())
        while True:
            error = self.robot.gy.value()
            print(error)
            output = kp * error
            self.robot.m1.run_forever(speed_sp=s1 + output)
            self.robot.m2.run_forever(speed_sp=s2 - output)
            sleep(.2)

    def menu(self, calibrate: bool, sound: ev3.Sound, mode: str = "NOCALIBRATE"):
        if calibrate:
            mode = "calibrate"
        while True:
            if mode == "NOCALIBRATE":
                pass
            elif mode == "dre":
                self.robot.m1.run_to_rel_pos(speed_sp=100, position_sp=360)
                self.robot.m2.run_to_rel_pos(speed_sp=100, position_sp=360)
            elif mode == "turn":
                self.turn(1)
                self.turn(-1)
                self.turn(-1)
                self.turn(2)
                while True:
                    self.follow(baseSpeed=200, optimal=175.2)
            elif mode == "":
                break
            elif mode == "wasd":
                self.wasd()
            elif mode == "gs":
                self.gyro_straight(800, 800, 10)
            elif mode == "follow":
                    self.follow(optimal=171.5, baseSpeed=350)
            elif mode == "battery":
                print(self.robot.ps.measured_volts)
            elif mode == "calibrate":
                with open("/home/robot/src/values.txt", mode="w") as file:
                    for i in self.calibrate():
                        file.write(f"{i}\n")
            elif mode == "beep":
                sound.beep()
            elif mode == "StarWars":
                self.robot.sd.tone(star_wars_sound)
            mode = input("mode?")
