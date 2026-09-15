#!/usr/bin/env python3
"""Application entry point."""

import sys

from PyQt6.QtWidgets import QApplication

from gui import LyricsSearchApp


def main() -> None:
    application = QApplication(sys.argv)
    window = LyricsSearchApp()
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()