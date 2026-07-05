from pprint import pprint


def debug(obj, label="DEBUG", color="green"):
    # ANSI Color Codes
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "blue": "\033[94m",
        "yellow": "\033[93m",
        "end": "\033[0m"  # Resets color back to white
    }

    # Pick the color or default to white if not found
    c = colors.get(color.lower(), "")
    reset = colors["end"]
    label = label.upper()

    line_width = 80

    # The Header
    print(f"\n{c}{'=' * line_width}")
    print(f"{label.center(line_width)}")
    print(f"{'=' * line_width}{reset}")

    # The Content
    pprint(obj)

    # The Footer
    print(f"{c}{'=' * line_width}{reset}\n")