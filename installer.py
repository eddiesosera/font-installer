import os
import shutil
import ctypes
import logging

FR_PRIVATE = 0x10  # Constant for adding fonts using Windows API

class FontInstaller:
    def __init__(self, system_fonts_folder):
        self.system_fonts_folder = system_fonts_folder  # Path to the system fonts folder

    def install_font(self, font_path):
        try:
            font_name = os.path.basename(font_path)  # Get the font file name
            temp_font_path = os.path.join(self.system_fonts_folder, font_name)  # Destination path in Fonts folder

            # If the font doesn't already exist in the fonts folder, copy it
            if not os.path.exists(temp_font_path):
                shutil.copy(font_path, temp_font_path)
            
            # Register the font in the system (Windows API)
            font_installed = ctypes.windll.gdi32.AddFontResourceExW(temp_font_path, FR_PRIVATE, None)
            if font_installed:
                logging.info(f"Successfully installed: {font_name}")
            else:
                logging.error(f"Failed to install: {font_name}")
        except Exception as e:
            logging.error(f"Error installing font {font_name}: {e}")

    def install_fonts_from_folder(self, fonts, stop_event, progress_queue):
        """Install fonts from the provided list of font paths."""
        total_fonts = len(fonts)
        for idx, font_path in enumerate(fonts):
            # Check if the user canceled the installation
            if stop_event.is_set():
                progress_queue.put('canceled')
                logging.info("Installation canceled by user")
                break
            
            # Install each font
            self.install_font(font_path)
            
            # Update progress in the queue
            progress_queue.put({
                'idx': idx + 1,
                'total': total_fonts,
                'file_name': os.path.basename(font_path)
            })

        # Notify that the installation is complete
        progress_queue.put('done')
        logging.info("All fonts installed successfully")

    def notify_system_fonts_updated(self):
        """Notify the system that fonts have been updated."""
        try:
            logging.info("Notifying system about font changes")
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x001D, 0, 0)
        except Exception as e:
            logging.error(f"Error while notifying system: {e}")
