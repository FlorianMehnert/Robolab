from specials import color_codes
class Debug:
    def __init__(self, debug_lvl = 3):
        self.debug_lvl = debug_lvl

    def cprint(self, text:str, color: color_codes):
        """
        prints a colored text when debug_lvl > 2
        """
        if self.debug_lvl > 2:
            print(f"{color}{text}{color_codes.reset}")

    def bprint(self, text):
        """
        prints normally when debug_lvl > 1
        """
        if self.debug_lvl > 1:
            print(f"{text}")