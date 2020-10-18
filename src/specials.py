from enum import Enum
from time import sleep

import ev3dev.ev3 as ev3


class color_codes(str, Enum):
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

star_wars_sound = [
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
