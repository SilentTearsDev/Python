import shutil
from pyfiglet import Figlet

# Colors
RED = "\033[91m"
WHITE = "\033[97m"
RESET = "\033[0m"


ASCII_DROP = [
"           ____           ",
"        .-'    `-.        ",
"      .'          `.      ",
"     /              \\     ",
"    /                \\    ",
"   |                  |    ",
"   |                  |    ",
"    \\                /     ",
"     \\              /      ",
"      `.          .'       ",
"        `-.____.-'         "
]


def print_ascii_drop():
    cols = shutil.get_terminal_size().columns
    for line in ASCII_DROP:
        print(WHITE + line.center(cols) + RESET)


def print_red_banner(text: str = "DEAD SILENT STUDIO"):
    cols = shutil.get_terminal_size().columns
    figlet = Figlet(font="slant")
    banner = figlet.renderText(text)

    for line in banner.splitlines():
        print(RED + line.center(cols) + RESET)


if __name__ == "__main__":
    print_ascii_drop()
    print()  # spacing
    print_red_banner("DEAD SILENT STUDIO")
