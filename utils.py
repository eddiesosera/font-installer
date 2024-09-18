import ctypes
import logging
import os
import zipfile
import tempfile

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def setup_logging():
    logging.basicConfig(filename='font_installer.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Logging initialized")

def scan_for_fonts_recursively(folder, include_zips=True):
    valid_fonts = []
    if os.path.isdir(folder):
        for root, dirs, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                if file.lower().endswith(('.otf', '.ttf')):
                    valid_fonts.append(full_path)
                elif include_zips and file.lower().endswith('.zip'):
                    valid_fonts.extend(process_zip_file(full_path))
    elif include_zips and folder.lower().endswith('.zip'):
        valid_fonts.extend(process_zip_file(folder))
    return valid_fonts

def process_zip_file(zip_path):
    fonts_found = []
    logging.info(f"Processing zip file: {zip_path}")
    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdirname)
                logging.info(f"Extracted zip file to {tmpdirname}")
                for root, dirs, files in os.walk(tmpdirname):
                    for file in files:
                        if file.lower().endswith(('.otf', '.ttf')):
                            fonts_found.append(os.path.join(root, file))
                        elif file.lower().endswith('.zip'):
                            fonts_found.extend(process_zip_file(os.path.join(root, file)))
    except Exception as e:
        logging.error(f"Error processing zip file {zip_path}: {e}")
    return fonts_found
