from enum import Enum


class ColorPrint(str, Enum):
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
