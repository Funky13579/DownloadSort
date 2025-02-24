import hashlib
import json
import logging
import os
import shutil
import sys
from datetime import date, timedelta

class FileSorter:
    def __init__(self, config_layout):
        self.filesFound: int = 0
        self.filesRemoved: int = 0
        self.fileDuplicates: int = 0
        self.filesMoved: int = 0
        self.filesRenamed: int = 0
        self.filesIgnored: int = 0
        
        try:
            self.config: dict = self.load_config(config_layout=config_layout)
        except FileNotFoundError:
            logging.error("No config.json file found!")
            quit()
        
    def load_config(self, config_layout: dict):
        try:
            with open('./config.json', 'r') as config_File:
                config = json.load(config_File)    

            if all(element in list(config.keys()) for element in config_layout.keys()):
                return config
            else:
                logging.error("config.json is missing keys please check!\n" + \
                              f"Missing keys: {list(set(config_layout.keys()) - set(config.keys()))}\n" + \
                              "Default config layout:\n " + json.dumps(config_layout))
                quit()
        
        except FileNotFoundError:
            
            logging.error("No config.json file found!")
            open(file="config.json",mode="w").write(json.dumps(config_layout))
            logging.info("Config file was created, please change!")

    def calculate_hash(self, file_path, hash_func=hashlib.sha256):
        """Calculate the hash of a file."""
        with open(file=file_path, mode='rb') as f:
            file_hash = hash_func()
            while chunk := f.read(8192):  # Read in 8KB chunks
                file_hash.update(chunk)
            return file_hash.hexdigest()
    
    def compare_filebytes(self, file1, file2):
        """Compare two files byte-by-byte."""
        with open(file=file1, mode='rb') as f1, open(file=file2, mode='rb') as f2:
            while True:
                chunk1 = f1.read(8192)
                chunk2 = f2.read(8192)
                if chunk1 != chunk2:
                    return False
                if not chunk1:  # EOF reached
                    break
            return True
        
    def are_files_same(self,file1, file2, size_threshold=1 * 1024 * 1024 * 1024) -> bool:
        """
        Check if two files are the same.
        - Use hashing for small files.
        - Use byte-by-byte comparison for large files. (file >= 1Gb)
        """
        
        # Step 1: Compare file sizes
        size1 = os.path.getsize(file1)
        size2 = os.path.getsize(file2)
        if size1 != size2:
            return False

        # Step 2: Decide method based on size
        if size1 > size_threshold:  # If file size exceeds threshold, use byte-by-byte
            if not self.compare_filebytes(file1, file2):
                return False
        else:  # Use hashing for smaller files
            hash1 = self.calculate_hash(file1)
            hash2 = self.calculate_hash(file2)
            if hash1 != hash2:
                return False

        self.fileDuplicates += 1
        return True
    
    def move_file(self, file, folder):
        filename, suffix = os.path.splitext(file)
    
        #Check if filename already exists
        if os.path.exists(f"{folder}/{file}"):
            
            #Check if files are the same when duplicates are not allowed
            if not self.config.get("ALLOW_DUPLICATES"):
                if self.are_files_same(file1=file, file2=f"{folder}/{file}"):
                    os.remove(file)
                    self.filesRemoved += 1
                    logging.info(f"{file} was a duplicate and was removed")
                    return
            
            #When filename already exists, but duplicates are allowed or files are not the same
            counter = 1
            while True:
                if os.path.exists(f"{folder}/{filename}_{counter}{suffix}"): 
                    counter += 1
                else:
                    break
            
            newFilename = f"{filename}_{counter}{suffix}"
            os.rename(file,newFilename)
            self.filesRenamed += 1
            logging.info(f"{file} was renamed to {newFilename}")
            file = newFilename

        shutil.move(src=f"{os.getcwd()}/{file}", dst=f"{os.getcwd()}/{folder}/{file}")
        self.filesMoved += 1
        logging.info(f"{file} was moved to {folder}")
    
    def remove_file_after_time(self, file, days) -> None:
        remove_date: date = (date.today() - timedelta(days=days))
        file_date: date = date.fromtimestamp(os.path.getmtime(file))
        
        if file_date < remove_date:
            os.remove(file)
            self.filesRemoved += 1
            logging.info(f"{file} was removed because it was older than {days} days")

    def check_directories(self):
        """ Check if Directories exist """
        for folder in self.config.get("FOLDERS"):
            if not os.path.isdir(folder):
                os.mkdir(folder)
                logging.info(f"Folder {folder} was created!")
            else:
                logging.info(f"Folder {folder} was found.")
        
    def check_file(self, file):
        """ Check if file is in the config and move it to the correct folder """
        
        self.filesFound += 1
    
        for folder in self.config.get("FOLDERS"):
            if(file.endswith(tuple(self.config.get("FOLDERS").get(folder)))):
                self.move_file(folder=folder,file=file)
                return
        logging.warning(f"No folder for {file}")
        self.filesIgnored += 1

    def clean_logs(self):
        for file in os.listdir("./logs"):
            if file.endswith(".log"):
                self.remove_file_after_time(f"./logs/{file}", self.config.get("DELETE_LOGS_AFTER_DAYS"))
        
    def sort_files(self) -> None:
        """ Sort files in the download folder """
        
        # Go to Downloads folder
        os.chdir(self.config.get("DOWNLOAD_FOLDER_PATH"))
        logging.info("Moved to download directory")

        # Check if Directories are in Config
        self.check_directories()

        # Move Files in Directories
        for file in os.listdir():
            if os.path.isfile(file):
                logging.info(f"File {file} was found.")
                self.check_file(file)

        logging.info("All files were sorted!")

        if self.config.get("DELETE_FILES_AFTER_DAYS") > 0:
            for file in os.listdir():
                if os.path.isfile(file):
                    self.remove_file_after_time(file, self.config.get("DELETE_FILES_AFTER_DAYS"))
                elif os.path.isdir(file):
                    for subfile in os.listdir(file):
                        self.remove_file_after_time(os.path.join(file, subfile), self.config.get("DELETE_FILES_AFTER_DAYS"))
                        
    def remove_duplicates(self, path=None) -> None:
        """ Remove duplicates in the download folder
            Needs to be called with cmd argument "rm_duplicates"
            Takes a long time for large folders
        """
        
        if path is None:
            path = self.config.get("DOWNLOAD_FOLDER_PATH")
            logging.info(f"Using download directory: {path}")
        
        logging.debug(f"Directory listing for {path}: {os.listdir(path)}")
        
        for file in os.listdir(path):
            full_file = os.path.join(path, file)
            logging.debug(f"    Checking {full_file}")
            if os.path.isfile(full_file):
                for file2 in os.listdir(path):
                    full_file2 = os.path.join(path, file2)
                    logging.debug(f"        Checking {full_file2}")
                    if os.path.isfile(full_file2) and full_file != full_file2:
                        if self.are_files_same(file1=full_file, file2=full_file2):
                            os.remove(full_file2)
                            self.filesRemoved += 1
                            logging.info(f"{file2} was a duplicate of {file} and was removed")
            elif os.path.isdir(full_file):
                self.remove_duplicates(path=full_file)
                
    def print_stats(self):
        logging.info(f"Files found: {self.filesFound}")
        logging.info(f"Files removed: {self.filesRemoved}")
        logging.info(f"File duplicates: {self.fileDuplicates}")
        logging.info(f"Files moved: {self.filesMoved}")
        logging.info(f"Files renamed: {self.filesRenamed}")
        logging.info(f"Files ignored: {self.filesIgnored}")
    
CONFIG_LAYOUT = {
            "DOWNLOAD_FOLDER_PATH" : "path/to/downloadfolder",
            "ALLOW_DUPLICATES" : False,
            "DELETE_LOGS_AFTER_DAYS" : -1,
            "DELETE_FILES_AFTER_DAYS" : -1,
            "FOLDERS" : { "FOLDER_NAME": ["FILE_SUFFIX_1","FILE_SUFFIX_2"], "FOLDER_NAME2": ["FILE_SUFFIX_1","FILE_SUFFIX_2"] }
        }

if not os.path.isdir("logs"):
    os.mkdir("logs")

logging.basicConfig(filename=f"./logs/OutputLog_{date.today().strftime("%d_%m_%Y")}.log", level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

file_sorter = FileSorter(config_layout=CONFIG_LAYOUT)
file_sorter.clean_logs()
file_sorter.sort_files()

if sys.argv[1] == "rm_duplicates":
    logging.info("Removing duplicates")
    file_sorter.remove_duplicates()
    logging.info("All duplicates were removed!")

    
file_sorter.print_stats()