from colorama import Style, Fore

"""Logging stuff"""


def Info(text):
    print(
        Style.RESET_ALL
        + Fore.LIGHTWHITE_EX
        + "["
        + Fore.LIGHTCYAN_EX
        + "INFO"
        + Fore.LIGHTWHITE_EX
        + "]"
        + Fore.WHITE
        + ": "
        + Fore.LIGHTCYAN_EX
        + text
        + Style.RESET_ALL
    )


def Debug(text):
    print(
        Style.RESET_ALL
        + Fore.LIGHTWHITE_EX
        + "["
        + Fore.BLUE
        + "DEBUG"
        + Fore.LIGHTWHITE_EX
        + "]"
        + Fore.WHITE
        + ": "
        + Fore.BLUE
        + text
        + Style.RESET_ALL
    )


def Warning(text):
    print(
        Style.RESET_ALL
        + Fore.LIGHTWHITE_EX
        + "["
        + Fore.YELLOW
        + "WARNING"
        + Fore.LIGHTWHITE_EX
        + "]"
        + Fore.WHITE
        + ": "
        + Fore.YELLOW
        + text
        + Style.RESET_ALL
    )


def Error(text):
    print(
        Style.RESET_ALL
        + Fore.LIGHTWHITE_EX
        + "["
        + Fore.RED
        + "ERROR"
        + Fore.LIGHTWHITE_EX
        + "]"
        + Fore.WHITE
        + ": "
        + Fore.RED
        + text
        + Style.RESET_ALL
    )


def Critical(text):
    print(
        Style.RESET_ALL
        + Fore.LIGHTWHITE_EX
        + "["
        + Fore.MAGENTA
        + "CRITICAL"
        + Fore.LIGHTWHITE_EX
        + "]"
        + Fore.WHITE
        + ": "
        + Fore.MAGENTA
        + text
        + Style.RESET_ALL
    )
