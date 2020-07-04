# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Simple helper for colored terminal output.

Examples:
    from stylish import colored as _c

    print
"""
import os
import sys


# Foreground ANSI codes using SGR format:
_SGR_FG_COLOR_MAP = {
    "reset_all": 0,
    "reset_fg": 39,
    # These are well supported.
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    # These are less good supported.
    "li_black": 90,
    "li_red": 91,
    "li_green": 92,
    "li_yellow": 93,
    "li_blue": 94,
    "li_magenta": 95,
    "li_cyan": 96,
    "li_white": 97,
}

FG_MAP = {color: "\033[{}m".format(num) for color, num in _SGR_FG_COLOR_MAP.items()}

# Background ANSI codes using SGR format:
_SGR_BG_COLOR_MAP = {
    "reset_bg": 49,
    # These are well supported.
    "black": 40,
    "red": 41,
    "green": 42,
    "yellow": 43,
    "blue": 44,
    "magenta": 45,
    "cyan": 46,
    "white": 47,
    # These are less good supported.
    "li_black": 100,
    "li_red": 101,
    "li_green": 102,
    "li_yellow": 103,
    "li_blue": 104,
    "li_magenta": 105,
    "li_cyan": 106,
    "li_white": 107,
}

BG_MAP = {color: "\033[{}m".format(num) for color, num in _SGR_BG_COLOR_MAP.items()}

# ANSI codes using 8-bit format (used for fore- and background)

_BIT_COLOR_MAP = {
    # These are less supported.
    "da_black": 0,
    "da_red": 88,
    "da_green": 22,
    "da_yellow": 58,
    "da_blue": 18,
    "da_magenta": 89,
    "da_cyan": 23,
    "da_white": 249,
}

FG_MAP.update(
    {color: "\033[38;5;{}m".format(num) for color, num in _BIT_COLOR_MAP.items()}
)
BG_MAP.update(
    {color: "\033[48;5;{}m".format(num) for color, num in _BIT_COLOR_MAP.items()}
)


_SGR_EFFECT__MAP = {
    # Reset distinct effects
    "reset_all": 0,
    "reset_fg": 39,
    "reset_bg": 49,
    "reset_bold_dim": 22,
    "reset_dim_bold": 22,
    "reset_i": 23,
    "reset_italic": 23,
    "reset_u": 24,
    "reset_underline": 24,
    "reset_blink": 25,
    "reset_inverse": 27,
    "reset_hidden": 28,
    "reset_strike": 29,
    # Effects
    "b": 1,
    "bold": 1,
    "dim": 2,
    "i": 3,
    "italic": 3,
    "u": 4,
    "underline": 4,
    "blink": 5,
    "inverse": 7,
    "hidden": 8,
    "strike": 9,
}
EFFECT_MAP = {color: "\033[{}m".format(num) for color, num in _SGR_EFFECT__MAP.items()}


# In 2016, Microsoft released the Windows 10 Version 1511 update which unexpectedly
# implemented support for ANSI escape sequences.[13] The change was designed to
# complement the Windows Subsystem for Linux, adding to the Windows Console Host
# used by Command Prompt support for character escape codes used by terminal-based
# software for Unix-like systems.
# This is not the default behavior and must be enabled programmatically with the
#  Win32 API via SetConsoleMode(handle, ENABLE_VIRTUAL_TERMINAL_PROCESSING).[14]
# This was enabled by CMD.EXE but not initially by PowerShell;[15] however,
# Windows PowerShell 5.1 now enables this by default. The ability to make a
# string constant containing ESC was added in PowerShell 6 with (for example)
# "`e[32m";[16] for PowerShell 5 you had to use [char]0x1B+"[32m".


class Stylish:
    """
    """

    _initialized = False

    def __init__(self, enable_color=True):
        self.enable_color(enable_color)

    @classmethod
    def _initialize(cls):
        if cls._initialized:
            return
        cls._initialized = True
        # Shim to make colors work on Windows
        if sys.platform == "win32":
            os.system("color")

    @classmethod
    def enable_color(cls, flag):
        if flag:
            cls._initialize()
        cls.use_colors = flag

    @classmethod
    def reset_all(cls):
        return EFFECT_MAP.get("reset_all")

    @classmethod
    def reset(cls, fg=True, bg=True, bold=True, underline=True, italic=True):
        if not cls.use_colors:
            return ""
        if fg and bg and bold and underline and italic:
            return cls.reset_all()

        sl = []
        if fg:
            sl.append(EFFECT_MAP.get("reset_fg"))
        if bg:
            sl.append(EFFECT_MAP.get("reset_bg"))
        if bold:
            sl.append(EFFECT_MAP.get("reset_bold"))
        if underline:
            sl.append(EFFECT_MAP.get("reset_underline"))
        if italic:
            sl.append(EFFECT_MAP.get("reset_italic"))
        res = "".join(sl)
        return res

    @classmethod
    def set(cls, fg, bg=None, bold=False, underline=False, italic=False):
        if not cls.use_colors:
            return ""
        sl = []
        if fg is not None:
            sl.append(FG_MAP[fg])
        if bg is not None:
            sl.append(BG_MAP[bg])
        if bold:
            sl.append(EFFECT_MAP["bold"])
        if underline:
            sl.append(EFFECT_MAP["underline"])
        if italic:
            sl.append(EFFECT_MAP["italic"])
        return "".join(sl)

    @classmethod
    def wrap(cls, text, fg, bg=None, bold=False, underline=False, italic=False):
        """Return a colorized text using ANSI escape codes.

        See also: https://en.wikipedia.org/wiki/ANSI_escape_code

        When
        Examples:
            print("Hello " + color("beautiful", "green") + " world.")
        """
        sl = []
        sl.append(cls.set(fg=fg, bg=bg, bold=bold, underline=underline, italic=italic))
        if text is not None:
            sl.append(text)
            # Only reset what we have set before
            sl.append(
                cls.reset(fg=fg, bg=bg, bold=bold, underline=underline, italic=italic)
            )

        text = "".join(str(s) for s in sl)
        return text

    @classmethod
    def red(cls, text):
        return cls.wrap(text, "li_red")

    @classmethod
    def yellow(cls, text):
        return cls.wrap(text, "yellow")

    @classmethod
    def green(cls, text):
        return cls.wrap(text, "green")

    @classmethod
    def gray(cls, text):
        return cls.wrap(text, "li_black")


stylish = Stylish()


def enable_color(flag):
    return Stylish.enable_color(flag)


def colors_enabled(flag):
    return Stylish.use_colors


def rgb_fg(r, g, b):
    return "\x1b[38;2;{};{};{}m".format(r, g, b)


def rgb_bg(r, g, b):
    return "\x1b[48;2;{};{};{}m".format(r, g, b)


def red(text):
    return stylish.wrap(text, "li_red")


def yellow(text):
    return stylish.wrap(text, "yellow")


def green(text):
    return stylish.wrap(text, "green")


def gray(text):
    return stylish.wrap(text, "li_black")


if __name__ == "__main__":
    print(Stylish.red("rötlich"))
    print(Stylish.wrap("rötlich2", "red", "yellow", underline=True) + "more")
