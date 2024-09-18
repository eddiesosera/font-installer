from utils import process_zip_file, scan_for_fonts_recursively
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
import os
import logging

logging.basicConfig(level=logging.DEBUG)

class FontInstallerUI:
    def __init__(self, root, installer):
        self.root = root
        self.installer = installer
        self.stop_event = threading.Event()
        self.progress_queue = queue.Queue()
        self.include_zips = tk.BooleanVar()
        self.executor = ThreadPoolExecutor(max_workers=5)

        # Create UI elements
        self.label = tk.Label(root, text="Select a folder to install fonts", font=("Arial", 12))
        self.label.pack(pady=10)

        self.zip_checkbox = tk.Checkbutton(root, text="Include zip files", variable=self.include_zips)
        self.zip_checkbox.pack(pady=5)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress_bar.pack(pady=10)

        # Loading indicator
        self.loading_label = tk.Label(root, text="", font=("Arial", 10), fg="blue")
        self.loading_label.pack(pady=5)

        # Font count label
        self.font_count_label = tk.Label(root, text="", font=("Arial", 10))
        self.font_count_label.pack(pady=5)

        # Scanning label
        self.scanning_label = tk.Label(root, text="", font=("Arial", 10), fg="green")
        self.scanning_label.pack(pady=5)

        # Create the button frame
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=20)

        # Add the buttons to the frame
        self.button_browse = tk.Button(self.button_frame, text="Browse Folders", command=self.select_folder, width=15, height=2)
        self.button_browse.pack(side=tk.LEFT, padx=5)

        self.button_browse_zip = tk.Button(self.button_frame, text="Scan Single Zip", command=self.select_single_zip, width=15, height=2)
        self.button_browse_zip.pack(side=tk.LEFT, padx=5)

        self.button_cancel = tk.Button(self.button_frame, text="Cancel", command=self.cancel_installation, width=15, height=2, state=tk.DISABLED)
        self.button_cancel.pack(side=tk.LEFT, padx=5)

        self.preview_frame = None

    def select_folder(self):
        folder_selected = filedialog.askdirectory(title="Select a folder containing fonts")
        if not folder_selected:
            return

        include_zip_files = self.include_zips.get()
        self.start_scanning([folder_selected], include_zip_files)

    def select_single_zip(self):
        zip_selected = filedialog.askopenfilename(title="Select a zip file", filetypes=[("Zip files", "*.zip")])
        if not zip_selected:
            return

        self.start_scanning([zip_selected], include_zip_files=True)

    def start_scanning(self, folders_or_zips, include_zip_files):
        # Disable buttons and show loading message
        logging.debug("Starting font scanning...")
        self.button_browse.config(state=tk.DISABLED)
        self.button_browse_zip.config(state=tk.DISABLED)
        self.button_cancel.config(state=tk.NORMAL)
        self.label.config(text="Scanning for fonts...")
        self.loading_label.config(text="Scanning fonts, please wait...")
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()

        # Submit scanning tasks to ThreadPoolExecutor
        self.executor.submit(self.scan_fonts, folders_or_zips, include_zip_files)

        # Start updating the progress bar based on the queue
        self.update_progress()

    def scan_fonts(self, folders_or_zips, include_zip_files):
        all_fonts = []
        logging.debug("Scanning for fonts...")

        for item in folders_or_zips:
            if self.stop_event.is_set():
                logging.debug("Scanning canceled by user.")
                self.progress_queue.put('canceled')
                return

            if os.path.isdir(item):
                fonts = scan_for_fonts_recursively(item, include_zip_files)
            elif item.lower().endswith('.zip'):
                fonts = process_zip_file(item)
            else:
                fonts = []
            all_fonts.extend(fonts)
            logging.debug(f"Found {len(fonts)} fonts in {item}")

        total_fonts = len(all_fonts)

        if not all_fonts:
            logging.debug("No fonts found.")
            self.progress_queue.put("no_fonts")
            return

        # Once scanning is done, pass fonts for installation
        logging.debug(f"Scanning complete. Found {total_fonts} fonts.")
        self.progress_queue.put(('set_max', total_fonts))
        self.progress_queue.put(('scanning_complete', all_fonts))

    def install_fonts(self, fonts):
        logging.debug("Starting font installation...")
        for idx, font in enumerate(fonts, start=1):
            if self.stop_event.is_set():
                logging.debug("Installation canceled by user.")
                self.progress_queue.put('canceled')
                return

            # Install font and update progress
            self.installer.install_font(font)
            logging.debug(f"Installing font {font} ({idx}/{len(fonts)}).")
            self.progress_queue.put(('progress', idx, len(fonts), font))

        # Notify that installation is done
        logging.debug("Installation complete.")
        self.progress_queue.put('done')

    def update_progress(self):
        try:
            # Keep updating the progress and checking for new messages from the queue
            message = self.progress_queue.get_nowait()

            if message == 'done':
                logging.debug("Update: Installation done.")
                self.label.config(text="Fonts installed successfully.")
                self.loading_label.config(text="")
                self.font_count_label.config(text="")
                self.scanning_label.config(text="")
                self.button_browse.config(state=tk.NORMAL)
                self.button_browse_zip.config(state=tk.NORMAL)
                self.button_cancel.config(state=tk.DISABLED)
                self.progress_bar['value'] = 0  # Reset progress bar
                self.progress_bar.stop()
                return

            if message == 'canceled':
                logging.debug("Update: Operation canceled.")
                self.label.config(text="Operation canceled by user.")
                self.loading_label.config(text="")
                self.font_count_label.config(text="")
                self.scanning_label.config(text="")
                self.button_browse.config(state=tk.NORMAL)
                self.button_browse_zip.config(state=tk.NORMAL)
                self.button_cancel.config(state=tk.DISABLED)
                self.progress_bar['value'] = 0
                self.progress_bar.stop()
                return

            if message == 'no_fonts':
                logging.debug("Update: No fonts found.")
                self.label.config(text="No fonts found.")
                self.loading_label.config(text="")
                self.font_count_label.config(text="")
                self.scanning_label.config(text="")
                self.button_browse.config(state=tk.NORMAL)
                self.button_browse_zip.config(state=tk.NORMAL)
                self.button_cancel.config(state=tk.DISABLED)
                self.progress_bar.stop()
                return

            if isinstance(message, tuple):
                if message[0] == 'set_max':
                    # Set the maximum value for the progress bar after scanning
                    total_fonts = message[1]
                    logging.debug(f"Update: Setting max fonts to {total_fonts}.")
                    self.progress_bar.stop()
                    self.progress_bar.config(mode='determinate', maximum=total_fonts)
                    self.progress_bar['value'] = 0
                    self.font_count_label.config(text=f"Total fonts to install: {total_fonts}")
                    self.loading_label.config(text="Installing fonts, please wait...")
                    self.label.config(text="Installing fonts...")

                elif message[0] == 'scanning_complete':
                    # Start installation
                    fonts = message[1]
                    logging.debug("Update: Starting font installation.")
                    self.executor.submit(self.install_fonts, fonts)

                elif message[0] == 'progress':
                    # Update progress bar and label with X out of Y fonts installed
                    idx, total_fonts, font = message[1], message[2], message[3]
                    logging.debug(f"Update: Installing font {font} ({idx}/{total_fonts}).")
                    self.progress_bar['value'] = idx
                    self.label.config(text=f"Installing {os.path.basename(font)}")
                    self.font_count_label.config(text=f"{idx} of {total_fonts} fonts installed")

        except queue.Empty:
            pass  # No message, nothing to do

        # Always schedule the next update
        self.root.after(100, self.update_progress)

    def cancel_installation(self):
        if messagebox.askyesno("Cancel", "Are you sure you want to cancel the operation?"):
            self.stop_event.set()
            logging.debug("User requested cancellation.")
