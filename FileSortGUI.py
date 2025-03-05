import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from FileSort import FileSorter

CONFIG_PATH = os.path.join(os.getcwd(), "config.json")
DEFAULT_CONFIG = {
    "DOWNLOAD_FOLDER_PATH": "path/to/downloadfolder",
    "ALLOW_DUPLICATES": False,
    "DELETE_LOGS_AFTER_DAYS": -1,
    "DELETE_FILES_AFTER_DAYS": -1,
    "FOLDERS": {
        "FOLDER_NAME": ["FILE_SUFFIX_1", "FILE_SUFFIX_2"],
        "FOLDER_NAME2": ["FILE_SUFFIX_1", "FILE_SUFFIX_2"]
    }
}

class FileSorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FileSorter GUI")
        
        self.load_config()

        self.file_sorter = FileSorter(config_layout=self.config)
        
        # UI Layout
        self.create_widgets()
        self.refresh_config_display()
        
        # Start console refresh loop
        self.refresh_console()
        
        self.root_dir = os.getcwd()
    
    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                self.config = json.load(f)
        else:
            self.config = DEFAULT_CONFIG.copy()
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.config, f, indent=4)
    
    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="FileSorter GUI", font=("Arial", 16))
        title.pack(pady=10)
        
        # Create the config preview frame but do not pack it initially
        self.preview_frame = tk.LabelFrame(self.root, text="Current config.json")
        self.config_text = tk.Text(self.preview_frame, height=10, width=80)
        self.config_text.pack(fill="both", expand=True)
        self.config_text.config(state="disabled")
        self.config_visible = False
        
        # Frame for folder management
        folder_frame = tk.LabelFrame(self.root, text="Manage Folders")
        folder_frame.pack(fill="x", padx=10, pady=5)
        
        # Scrollbar and dynamic Listbox for folders
        self.folder_scrollbar = tk.Scrollbar(folder_frame, orient="vertical")
        self.folder_listbox = tk.Listbox(folder_frame, yscrollcommand=self.folder_scrollbar.set)
        self.folder_scrollbar.config(command=self.folder_listbox.yview)
        self.folder_listbox.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.folder_scrollbar.pack(side="right", fill="y")
        self.folder_listbox.bind("<<ListboxSelect>>", self.on_folder_select)
        
        btn_frame = tk.Frame(folder_frame)
        btn_frame.pack(side="right", padx=5, pady=5)
        
        add_btn = tk.Button(btn_frame, text="Add Folder", command=self.add_folder)
        add_btn.pack(fill="x", pady=2)
        rename_btn = tk.Button(btn_frame, text="Rename/Edit", command=self.rename_folder)
        rename_btn.pack(fill="x", pady=2)
        
        # Frame for FileSorter options
        options_frame = tk.LabelFrame(self.root, text="FileSorter Options")
        options_frame.pack(fill="x", padx=10, pady=5)
        
        self.rm_duplicates_var = tk.BooleanVar()
        rm_duplicates_chk = tk.Checkbutton(options_frame, text="Remove Duplicates (rm_duplicates)", variable=self.rm_duplicates_var)
        rm_duplicates_chk.pack(side="left", padx=5, pady=5)
        
        # Save and Start buttons
        action_frame = tk.Frame(self.root)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        save_btn = tk.Button(action_frame, text="Save Config", command=self.save_config)
        save_btn.pack(side="left", padx=5)
        start_btn = tk.Button(action_frame, text="Start FileSorter", command=self.start_filesorter)
        start_btn.pack(side="right", padx=5)
        
        # "View Logs" button
        view_logs_btn = tk.Button(action_frame, text="View Logs", command=self.view_logs)
        view_logs_btn.pack(side="left", padx=5)
        
        # Console frame to display FileSorter global variables
        console_frame = tk.LabelFrame(self.root, text="Console")
        console_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.console_text = tk.Text(console_frame, height=8, width=100)
        self.console_text.pack(fill="both", expand=True)
        self.console_text.config(state="disabled")
        
        # Toggle Config button to show/hide config preview
        toggle_btn = tk.Button(self.root, text="Show Config", command=self.toggle_config)
        toggle_btn.pack(pady=5)
    
    def toggle_config(self):
        if self.config_visible:
            self.preview_frame.pack_forget()
            self.config_visible = False
        else:
            self.preview_frame.pack(fill="both", expand=True, padx=10, pady=5)
            self.config_visible = True
            self.refresh_config_display()
    
    def refresh_config_display(self):
        # Refresh text preview and folder listbox
        self.config_text.config(state="normal")
        self.config_text.delete("1.0", tk.END)
        self.config_text.insert(tk.END, json.dumps(self.config, indent=4))
        self.config_text.config(state="disabled")
        
        self.folder_listbox.delete(0, tk.END)
        for folder, filters in self.config.get("FOLDERS", {}).items():
            self.folder_listbox.insert(tk.END, f"{folder}: {', '.join(filters)}")
        
        # Dynamically adjust listbox height: max rows = 25
        folder_count = len(self.config.get("FOLDERS", {}))
        new_height = folder_count if folder_count <= 25 else 25
        self.folder_listbox.config(height=new_height)
    
    def add_folder(self):
        folder_name = simpledialog.askstring(title="Add Folder", prompt="Enter new folder name:")
        if not folder_name:
            return
        filters = simpledialog.askstring(title="Folder Filters", prompt="Enter filters (comma separated):")
        filters_list = [x.strip() for x in filters.split(",")] if filters else []
        self.config.setdefault("FOLDERS", {})[folder_name] = filters_list
        self.refresh_config_display()
    
    def rename_folder(self):
        selection = self.folder_listbox.curselection()
        if not selection:
            messagebox.showwarning(title="No selection", message="Please select a folder to edit.")
            return
        index = selection[0]
        folder_key = list(self.config.get("FOLDERS", {}).keys())[index]
        new_name = simpledialog.askstring(title="Rename Folder", prompt="Enter new folder name:", initialvalue=folder_key)
        if not new_name:
            return
        new_filters = simpledialog.askstring(title="Edit Filters", prompt="Enter new filters (comma separated):",
                                             initialvalue=", ".join(self.config["FOLDERS"][folder_key]))
        filters_list = [x.strip() for x in new_filters.split(",")] if new_filters else []
        # Remove old key if name changed
        if new_name != folder_key:
            self.config["FOLDERS"].pop(folder_key)
        self.config["FOLDERS"][new_name] = filters_list
        self.refresh_config_display()
    
    def save_config(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=4)
        messagebox.showinfo(title="Saved", message="config.json has been saved.")
        self.refresh_config_display()
    
    def start_filesorter(self):
        # Build args based on GUI options
        args = []
        if self.rm_duplicates_var.get():
            args.append("rm_duplicates")
        # Run sorting in a separate thread so GUI remains responsive
        def run_sorter():
            self.file_sorter.start_sorting(*args)
        threading.Thread(target=run_sorter, daemon=True).start()
        messagebox.showinfo(title="Started", message="FileSorter was started in background.")
    
    def refresh_console(self):
        # Refresh the console every second with FileSorter stats and progress
        stats = (
            f"Files Found: {self.file_sorter.get_files_found()}\n"
            f"Files Removed: {self.file_sorter.get_files_removed()}\n"
            f"File Duplicates: {self.file_sorter.get_file_duplicates()}\n"
            f"Files Moved: {self.file_sorter.get_files_moved()}\n"
            f"Files Renamed: {self.file_sorter.get_files_renamed()}\n"
            f"Files Ignored: {self.file_sorter.get_files_ignored()}\n"
            f"Progress: {self.file_sorter.get_progress_bar()}\n"
        )
        self.console_text.config(state="normal")
        self.console_text.delete("1.0", tk.END)
        self.console_text.insert(tk.END, stats)
        self.console_text.config(state="disabled")
        self.root.after(1000, self.refresh_console)
    
    def view_logs(self):
        logs_dir = os.path.join(self.root_dir, "logs")
        if not os.path.isdir(logs_dir):
            messagebox.showinfo(title="Logs", message="No logs directory found.")
            return
        log_files = [f for f in os.listdir(logs_dir) if f.endswith(".log")]
        if not log_files:
            messagebox.showinfo(title="Logs", message="No log files found.")
            return
        # Get the most recent log file
        log_files.sort(key=lambda f: os.path.getmtime(os.path.join(logs_dir, f)), reverse=True)
        latest_log = os.path.join(logs_dir, log_files[0])
        try:
            with open(latest_log, "r") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror(title="Error", message=f"Failed to read log file: {str(e)}")
            return
        
        # Create a new window to display the log content
        log_win = tk.Toplevel(self.root)
        log_win.title("Log Viewer - " + os.path.basename(latest_log))
        text_widget = tk.Text(log_win, wrap="word")
        text_widget.insert(tk.END, content)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True)

    def on_folder_select(self, event):
        # Placeholder for selection event if needed
        pass

if __name__ == "__main__":
    root = tk.Tk()
    # Set window geometry
    root.geometry(newGeometry="1200x800")
    app = FileSorterApp(root=root)
    root.mainloop()
