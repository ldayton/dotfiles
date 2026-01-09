#!/usr/bin/env python3
"""Display terminal colors with names and ANSI codes."""

COLORS = [
    # Foreground colors
    ("black", "30", "38;5;16", "38;2;0;0;0"),
    ("red", "31", "38;5;160", "38;2;204;0;0"),
    ("green", "32", "38;5;70", "38;2;78;154;6"),
    ("yellow", "33", "38;5;178", "38;2;196;160;0"),
    ("blue", "34", "38;5;26", "38;2;52;101;164"),
    ("magenta", "35", "38;5;96", "38;2;117;80;123"),
    ("cyan", "36", "38;5;30", "38;2;6;152;154"),
    ("white", "37", "38;5;188", "38;2;211;215;207"),
    ("brightBlack", "90", "38;5;59", "38;2;85;87;83"),
    ("brightRed", "91", "38;5;203", "38;2;239;41;41"),
    ("brightGreen", "92", "38;5;155", "38;2;138;226;52"),
    ("brightYellow", "93", "38;5;227", "38;2;252;233;79"),
    ("brightBlue", "94", "38;5;111", "38;2;114;159;207"),
    ("brightMagenta", "95", "38;5;140", "38;2;173;127;168"),
    ("brightCyan", "96", "38;5;80", "38;2;52;226;226"),
    ("brightWhite", "97", "38;5;231", "38;2;238;238;236"),
    # Background colors
    ("bgBlack", "40", "48;5;16", "48;2;0;0;0"),
    ("bgRed", "41", "48;5;160", "48;2;204;0;0"),
    ("bgGreen", "42", "48;5;70", "48;2;78;154;6"),
    ("bgYellow", "43", "48;5;178", "48;2;196;160;0"),
    ("bgBlue", "44", "48;5;26", "48;2;52;101;164"),
    ("bgMagenta", "45", "48;5;96", "48;2;117;80;123"),
    ("bgCyan", "46", "48;5;30", "48;2;6;152;154"),
    ("bgWhite", "47", "48;5;188", "48;2;211;215;207"),
    ("bgBrightBlack", "100", "48;5;59", "48;2;85;87;83"),
    ("bgBrightRed", "101", "48;5;203", "48;2;239;41;41"),
    ("bgBrightGreen", "102", "48;5;155", "48;2;138;226;52"),
    ("bgBrightYellow", "103", "48;5;227", "48;2;252;233;79"),
    ("bgBrightBlue", "104", "48;5;111", "48;2;114;159;207"),
    ("bgBrightMagenta", "105", "48;5;140", "48;2;173;127;168"),
    ("bgBrightCyan", "106", "48;5;80", "48;2;52;226;226"),
    ("bgBrightWhite", "107", "48;5;231", "48;2;238;238;236"),
]

MOLOKAI = [
    ("black", "121212", False),
    ("red", "fa2573", False),
    ("green", "98e123", False),
    ("yellow", "dfd460", False),
    ("blue", "1080d0", False),
    ("magenta", "8700ff", False),
    ("cyan", "43a8d0", False),
    ("white", "bbbbbb", False),
    ("brightBlack", "555555", False),
    ("brightRed", "f6669d", False),
    ("brightGreen", "b1e05f", False),
    ("brightYellow", "fff26d", False),
    ("brightBlue", "00afff", False),
    ("brightMagenta", "af87ff", False),
    ("brightCyan", "51ceff", False),
    ("brightWhite", "ffffff", False),
    ("bgBlack", "121212", True),
    ("bgRed", "fa2573", True),
    ("bgGreen", "98e123", True),
    ("bgYellow", "dfd460", True),
    ("bgBlue", "1080d0", True),
    ("bgMagenta", "8700ff", True),
    ("bgCyan", "43a8d0", True),
    ("bgWhite", "bbbbbb", True),
    ("bgBrightBlack", "555555", True),
    ("bgBrightRed", "f6669d", True),
    ("bgBrightGreen", "b1e05f", True),
    ("bgBrightYellow", "fff26d", True),
    ("bgBrightBlue", "00afff", True),
    ("bgBrightMagenta", "af87ff", True),
    ("bgBrightCyan", "51ceff", True),
    ("bgBrightWhite", "ffffff", True),
]

RST = "\033[0m"

def hex_to_rgb(h: str, is_bg: bool = False) -> str:
    prefix = "48" if is_bg else "38"
    return f"{prefix};2;{int(h[0:2], 16)};{int(h[2:4], 16)};{int(h[4:6], 16)}"

def main():
    print(f"\033[1m{'Standard':^42}\033[0m\n")
    print(f"{'Name':<20} {'Foreground':<10} {'Background':<10}")
    print("─" * 42)
    for name, ansi16, ansi256, truecolor in COLORS:
        is_bg = name.startswith("bg")
        if is_bg:
            # Use white or black foreground for contrast
            light_bgs = ("bgWhite", "bgBrightWhite", "bgBrightYellow", "bgBrightGreen", "bgBrightCyan", "bgYellow")
            fg_code = "30" if name in light_bgs else "97"
            colored_name = f"\033[{fg_code};{ansi16}m{name:<20}{RST}"
            fg_hex = "000000" if name in light_bgs else "ffffff"
            # Extract bg hex from truecolor (48;2;R;G;B)
            parts = truecolor.split(";")
            bg_hex = f"{int(parts[2]):02x}{int(parts[3]):02x}{int(parts[4]):02x}"
            print(f"{colored_name} #{fg_hex:<8} #{bg_hex}")
        else:
            colored_name = f"\033[{ansi16}m{name:<20}{RST}"
            # Extract fg hex from truecolor (38;2;R;G;B)
            parts = truecolor.split(";")
            fg_hex = f"{int(parts[2]):02x}{int(parts[3]):02x}{int(parts[4]):02x}"
            print(f"{colored_name} #{fg_hex}")

    print(f"\n\033[1m{'Molokai':^42}\033[0m\n")
    print(f"{'Name':<20} {'Foreground':<10} {'Background':<10}")
    print("─" * 42)
    for name, hex_val, is_bg in MOLOKAI:
        if is_bg:
            bg_hex = hex_val
            fg_hex = "000000" if hex_val in ("ffffff", "fff26d", "b1e05f", "bbbbbb", "dfd460", "98e123") else "ffffff"
            bg = hex_to_rgb(bg_hex, True)
            fg = hex_to_rgb(fg_hex, False)
            colored_name = f"\033[{fg};{bg}m{name:<20}{RST}"
            print(f"{colored_name} #{fg_hex:<8} #{bg_hex}")
        else:
            rgb = hex_to_rgb(hex_val, False)
            colored_name = f"\033[{rgb}m{name:<20}{RST}"
            print(f"{colored_name} #{hex_val}")

if __name__ == "__main__":
    main()
