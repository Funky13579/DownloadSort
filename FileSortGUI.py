import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import tkinter.filedialog as tk_filedialog
import threading
from FileSort import FileSorter

DISABLED_NUMBER = -1
MAX_DAYS = float("inf")
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
        
        # Frame for configuration
        config_frame = tk.LabelFrame(self.root, text="FileSorter Config")
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # Config download folder path
        self.download_folder_var = tk.StringVar()
        self.download_folder_var.trace_add("write", lambda *args: self.on_entry_change(var_name="DOWNLOAD_FOLDER_PATH", value=self.safe_get_tk_var(self.download_folder_var)))
        tk.StringVar.set(self.download_folder_var, self.config.get("DOWNLOAD_FOLDER_PATH", ""))
        tk.Label(config_frame, text="Download Folder Path").pack(padx=10, pady=5)
        tk.Entry(config_frame, textvariable=self.download_folder_var, width=50, state='readonly').pack(fill="x", padx=10, pady=5)
        
        # Button to browse and select folder
        browse_button = tk.Button(config_frame, text="Browse", command=self.browse_folder)
        browse_button.pack(padx=10, pady=5, anchor="w")
        
        # Frame for config options
        config_options_frame = tk.LabelFrame(config_frame, text="Config Options")
        config_options_frame.pack(fill="x", padx=10, pady=5)
        
        # Config allow duplicates and delete logs options
        self.allow_duplicates_var = tk.BooleanVar()
        self.allow_duplicates_var.trace_add("write", lambda *args: self.on_entry_change("ALLOW_DUPLICATES", self.allow_duplicates_var.get()))
        allow_duplicates_chk = tk.Checkbutton(config_options_frame, variable=self.allow_duplicates_var)
        allow_duplicates_chk.grid(row=0, column=0)
        tk.BooleanVar.set(self.allow_duplicates_var, self.config.get("ALLOW_DUPLICATES", False))
        tk.Label(config_options_frame, text="Allow Duplicates").grid(row=0, column=1,sticky="w", padx=5)
        
        #Validation command for days spinbox
        validate_spinbox_days = (self.root.register(self.validate_spinbox_days), '%P')
        
        # Config delete logs after days
        self.delete_logs_var = tk.IntVar()
        self.delete_logs_var.trace_add("write", lambda *args: self.on_entry_change("DELETE_LOGS_AFTER_DAYS", self.safe_get_tk_var(self.delete_logs_var)))
        tk.IntVar.set(self.delete_logs_var, self.config.get("DELETE_LOGS_AFTER_DAYS", -1))
        tk.Spinbox(config_options_frame, from_=DISABLED_NUMBER, to=MAX_DAYS, textvariable=self.delete_logs_var,
                   width=5, validate='key', validatecommand=validate_spinbox_days).grid(row=1, column=0)
        tk.Label(config_options_frame, text="Delete Logs After Days").grid(row=1, column=1, padx=5)
        
        # Config delete files after days
        self.delete_files_var = tk.IntVar()
        self.delete_files_var.trace_add("write", lambda *args: self.on_entry_change("DELETE_FILES_AFTER_DAYS", self.safe_get_tk_var(self.delete_files_var)))
        tk.IntVar.set(self.delete_files_var, self.config.get("DELETE_FILES_AFTER_DAYS", -1))
        tk.Spinbox(config_options_frame, from_=DISABLED_NUMBER, to=MAX_DAYS, textvariable=self.delete_files_var,
                   width=5, validate='key', validatecommand=validate_spinbox_days).grid(row=2, column=0)
        tk.Label(config_options_frame, text="Delete Files After Days").grid(row=2, column=1, padx=5)
        
        # Frame for folder management
        folder_frame = tk.LabelFrame(config_frame, text="Manage Folders")
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
        
        add_btn = tk.Button(btn_frame, text="Add", command=self.add_folder)
        add_btn.pack(fill="x", pady=2)
        
        rename_btn = tk.Button(btn_frame, text="Rename", command=self.rename_folder)
        rename_btn.pack(fill="x", pady=2)
        
        edit_btn = tk.Button(btn_frame, text="Edit Filters", command=self.edit_filters)
        edit_btn.pack(fill="x", pady=2)
        
        remove_btn = tk.Button(btn_frame, text="Remove", command=self.remove_folder)
        remove_btn.pack(fill="x", pady=2)
        
        save_btn = tk.Button(config_frame, text="Save Config", command=self.save_config)
        save_btn.pack(side="left", padx=5)
        
        # Frame for FileSorter options
        options_frame = tk.LabelFrame(self.root, text="FileSorter Options")
        options_frame.pack(fill="x", padx=10, pady=5)
        
        self.rm_duplicates_var = tk.BooleanVar()
        rm_duplicates_chk = tk.Checkbutton(options_frame, text="Remove Duplicates (rm_duplicates)", variable=self.rm_duplicates_var)
        rm_duplicates_chk.pack(side="left", padx=5, pady=5)
        
        # Start button
        action_frame = tk.Frame(self.root)
        action_frame.pack(fill="x", padx=10, pady=10)
        
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
        
        # Create the config preview frame but do not pack it initially
        self.preview_frame = tk.LabelFrame(self.root, text="Current config.json")
        self.config_text = tk.Text(self.preview_frame, height=10, width=80)
        self.config_text.pack(fill="both", expand=True)
        self.config_text.config(state="disabled")
        self.config_visible = False
        
        # Toggle Config button to show/hide config preview
        toggle_btn = tk.Button(self.root, text="Show Config", command=self.toggle_config)
        toggle_btn.pack(pady=5)
    
    def safe_get_tk_var(self, tk_var: tk.Variable):
        try:
            return tk_var.get()
        except Exception:
            return None
        
    def validate_spinbox_days(self, value) -> bool:
        if value in ("", "-"):
            return True
        try:
            value = int(value)
            return value >= -1
        except ValueError:
            return False
    
    def browse_folder(self):
        folder_selected = tk_filedialog.askdirectory(title="Select Download Folder")
        if folder_selected:
            self.download_folder_var.set(folder_selected)
    
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
    
    def add_folder(self, text = None):
        folder_name = simpledialog.askstring(title="Add Folder", prompt="Enter new folder name:", initialvalue=text)
        if not folder_name:
            return
        
        if folder_name in self.config.get("FOLDERS", {}):
            messagebox.showwarning(title="Duplicate", message=f"{folder_name} already exists.")
            self.add_folder(folder_name)
            return
        
        filters = simpledialog.askstring(title="Folder Filters", prompt="Enter filters (comma separated):")
        filters_list = [x.strip() for x in filters.split(",")] if filters else []
        self.config.setdefault("FOLDERS", {})[folder_name] = filters_list
        self.refresh_config_display()
    
    def get_folder_key(self):
        selection = self.folder_listbox.curselection()
        if not selection:
            messagebox.showwarning(title="No selection", message="Please select a folder to edit.")
            return
        index = selection[0]
        folder_key = list(self.config.get("FOLDERS", {}).keys())[index]
        return folder_key
    
    def rename_folder(self):
        folder_key = self.get_folder_key()
        if not folder_key:
            return
        
        filters_list = self.config["FOLDERS"][folder_key]
        new_name = simpledialog.askstring(title="Rename Folder", prompt="Enter new folder name:", initialvalue=folder_key)
        if not new_name:
            return
        
        # Remove old key if name changed
        if new_name != folder_key:
            self.config["FOLDERS"].pop(folder_key)
            self.config["FOLDERS"][new_name] = filters_list
        self.refresh_config_display()
        
    def edit_filters(self):
        folder_key = self.get_folder_key()
        if not folder_key:
            return
        new_filters = simpledialog.askstring(title="Edit Filters", prompt="Enter new filters (comma separated):",
                                             initialvalue=", ".join(self.config["FOLDERS"][folder_key]))
        if new_filters is not None:
            filters_list = [x.strip() for x in new_filters.split(",")] if new_filters else []
            self.config["FOLDERS"][folder_key] = filters_list
            self.refresh_config_display()
            
    def remove_folder(self):
        folder_key = self.get_folder_key()
        if not folder_key:
            return
        confirm = messagebox.askyesno(title="Remove Folder", message=f"Are you sure you want to remove {folder_key}?")
        if confirm:
            self.config["FOLDERS"].pop(folder_key)
            self.refresh_config_display()

    def save_config(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=4)
        messagebox.showinfo(title="Saved", message="config.json has been saved.")
        self.file_sorter.load_config(self.config)
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
        self.start_sorter_progress_widget()
        
    def start_sorter_progress_widget(self):
        
        widget = tk.Toplevel(self.root)
        widget.title("FileSorter Progress")
        
        tk.Label(widget, text="FileSorter Progress", font=("Arial", 14)).pack(pady=10)
        
        progress_bar = ttk.Progressbar(widget, orient="horizontal", length=300, mode="determinate")
        progress_bar.pack(pady=10)
        
        percent_label = tk.Label(widget, text="0%", font=("Arial", 12))
        percent_label.pack(pady=5)
        
        cancel_button = tk.Button(widget, text="Cancel", command=widget.destroy)
        cancel_button.pack(pady=10)
        
        status_label = tk.Label(widget, text="Starting...", font=("Arial", 10))
        status_label.pack(pady=5)
        
        
        def update_progress(progress_bar=progress_bar, percent_label=percent_label, status_label=status_label):
            progress = self.file_sorter.get_progress_percent()
            progress_bar["value"] = progress
            percent_label.config(text=f"{progress}%")
            status_label.config(text=self.file_sorter.get_current_task())
            if progress < 100:
                widget.after(50, update_progress)
            else:
                progress_bar["value"] = 100
                percent_label.config(text="100%")
                status_label.config(text="Sorting complete.")

        # Start periodic progress updates on the main thread
        widget.after(50, update_progress)
        
        widget.mainloop()
    
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
    
    def on_entry_change(self, var_name, value):
        
        if value is None:
            self.delete_logs_var.set(-1)
            return False
        
        if value in ("", "-"):
            self.delete_logs_var.set(-1)
            return False
        
        if var_name in self.config.keys():
            self.config[var_name] = value
        else:
            raise ValueError(f"Invalid config key: {var_name}")

if __name__ == "__main__":
    root = tk.Tk()
    # Set window geometry
    root.geometry(newGeometry="1200x1200")
    app = FileSorterApp(root=root)
    root.mainloop()
