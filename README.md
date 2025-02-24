# DownloadSort

DownloadSort is a Python script designed to help you organize and manage your downloaded files. It can move files to specific folders based on their extensions, remove old files, and eliminate duplicate files.

## Features

- Move files to designated folders based on their extensions.
- Remove files older than a specified number of days.
- Remove duplicate files.
- Clean up old log files.

## Configuration

The script uses a `config.json` file to determine its behavior. If the file does not exist, it will be created with a default configuration layout.

### Default Configuration Layout

```json
{
  "DOWNLOAD_FOLDER_PATH": "path/to/downloadfolder",
  "ALLOW_DUPLICATES": false,
  "DELETE_LOGS_AFTER_DAYS": -1,
  "DELETE_FILES_AFTER_DAYS": -1,
  "FOLDERS": {
    "FOLDER_NAME": ["FILE_SUFFIX_1", "FILE_SUFFIX_2"],
    "FOLDER_NAME2": ["FILE_SUFFIX_1", "FILE_SUFFIX_2"]
  }
}
```

- `DOWNLOAD_FOLDER_PATH`: Path to the download folder.
- `ALLOW_DUPLICATES`: Whether to allow duplicate files.
- `DELETE_LOGS_AFTER_DAYS`: Number of days after which log files should be deleted. Set to `-1` to disable.
- `DELETE_FILES_AFTER_DAYS`: Number of days after which files should be deleted. Set to `-1` to disable.
- `FOLDERS`: Dictionary where keys are folder names and values are lists of file extensions.

## Usage

1. Ensure you have Python installed on your system.
2. Place the script and `config.json` in the same directory.
3. Run the script using the command:
   ```sh
   python FileSort.py
   ```
4. To remove duplicates, run the script with the `rm_duplicates` argument:
   ```sh
   python FileSort.py rm_duplicates
   ```

## Logging

Logs are stored in the `logs` directory with filenames in the format `OutputLog_DD_MM_YYYY.log`.
