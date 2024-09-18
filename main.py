import tkinter as tk
from installer import FontInstaller  # Make sure this imports the correct FontInstaller class
from ui import FontInstallerUI
import sys
import ctypes

def main():
    try:
        # Initialize root window
        root = tk.Tk()
        root.title("Font Installer")

        # Set window size and position
        window_width = 500
        window_height = 250
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_coordinate = int((screen_width / 2) - (window_width / 2))
        y_coordinate = int((screen_height / 2) - (window_height / 2))
        root.geometry(f"{window_width}x{window_height}+{x_coordinate}+{y_coordinate}")

        # Initialize installer and UI
        system_fonts_folder = r"C:\Windows\Fonts"
        font_installer = FontInstaller(system_fonts_folder)  # Correctly pass the folder path to FontInstaller
        ui = FontInstallerUI(root, font_installer)  # Correctly pass the root window and installer to FontInstallerUI

        # Start the Tkinter main event loop
        root.mainloop()

    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to close...")

if __name__ == "__main__":
    main()
