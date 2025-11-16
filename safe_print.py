import sys

def safe_print(text):
    """Avoid Unicode crashes in PyInstaller by stripping unsupported characters."""
    if getattr(sys, "frozen", False):  # Running inside EXE
        text = text.encode("ascii", "ignore").decode()
    print(text)