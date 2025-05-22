# agent/modules/application_control.py
import subprocess
import platform
import os
# For closing applications, psutil is highly recommended for cross-platform PID finding.
# You'll need to install it: pip install psutil
try:
    import psutil
except ImportError:
    psutil = None
    print("Warning: psutil library not found. 'app_close' functionality will be limited or may not work.")


# A simple mapping for common applications. Expand as needed.
# Keys are friendly names, values are system commands or paths.
APP_MAP = {
    "windows": {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "explorer": "explorer.exe",
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "vscode": "code.exe", # Example
        "word": "WINWORD.EXE",
        "excel": "EXCEL.EXE",
    },
    "linux": {
        "text editor": "gedit", # GNOME
        "kate": "kate", # KDE
        "calculator": "gnome-calculator", # GNOME
        "kcalc": "kcalc", # KDE
        "files": "nautilus", # GNOME
        "dolphin": "dolphin", # KDE
        "terminal": "gnome-terminal", # GNOME
        "konsole": "konsole", # KDE
        "chrome": "google-chrome",
        "firefox": "firefox",
        "vscode": "code",
    },
    "darwin": { # macOS
        "textedit": "TextEdit",
        "calculator": "Calculator",
        "finder": "Finder",
        "terminal": "Terminal",
        "chrome": "Google Chrome",
        "firefox": "Firefox",
        "vscode": "Visual Studio Code", # App name for 'open -a'
        "word": "Microsoft Word",
        "excel": "Microsoft Excel",
    }
}

def open_application(app_name_or_path: str):
    """
    Opens a specified application using its friendly name or direct executable path.
    
    This function attempts to map common friendly application names (e.g., "notepad", 
    "chrome", "vscode") to their system-specific commands or application names.
    If a path is provided, it attempts to execute it directly.
    Behavior is OS-dependent.

    Args:
        app_name_or_path (str): The friendly name of the application (e.g., "calculator") 
                                or the full path to its executable.
    """
    system = platform.system().lower()
    command_to_run_list = [] # Use a list for Popen for better argument handling

    # Determine the actual command
    final_command_description = app_name_or_path # For logging/messaging
    
    if os.path.exists(app_name_or_path) and (os.path.isfile(app_name_or_path) or app_name_or_path.endswith(".app")): # If it's an existing file/app bundle
        if system == "darwin" and app_name_or_path.endswith(".app"):
            command_to_run_list = ["open", app_name_or_path]
        else:
            command_to_run_list = [app_name_or_path]
        final_command_description = app_name_or_path
    elif system in APP_MAP and app_name_or_path.lower() in APP_MAP[system]:
        mapped_command = APP_MAP[system][app_name_or_path.lower()]
        if system == "darwin" and not mapped_command.startswith("/"): # macOS app names
            command_to_run_list = ["open", "-a", mapped_command]
        elif system == "windows" and " " in mapped_command and not mapped_command.lower().endswith((".exe", ".bat", ".com", ".cmd")) : # Heuristic for Windows start for app names
             command_to_run_list = ["start", "", mapped_command] # Use start for app names with spaces
        else: # Direct command or path from map
            command_to_run_list = [mapped_command] # Wrap in list for Popen
        final_command_description = mapped_command
    else: # Fallback to trying the name directly as a command
        command_to_run_list = [app_name_or_path] # Wrap in list
        final_command_description = app_name_or_path
    
    try:
        use_shell = False
        if system == "windows" and command_to_run_list[0].lower() == "start":
            use_shell = True # 'start' command often requires shell=True
        elif system == "linux" and len(command_to_run_list) == 1 and not os.path.isabs(command_to_run_list[0]) and not command_to_run_list[0].startswith("./"):
            # For simple commands on Linux that are in PATH and not paths themselves, shell=True might be okay,
            # but Popen with a list of args is generally safer.
            # Let's prefer no shell if possible.
            # If it's a single command like 'gedit', Popen(['gedit']) works.
            pass


        print(f"Attempting to run: {command_to_run_list} with shell={use_shell}")
        # Using Popen for non-blocking execution
        if system == "linux":
             # Detach the process on Linux so it doesn't die with the agent if agent is in a terminal
            subprocess.Popen(command_to_run_list, shell=use_shell, preexec_fn=os.setpgrp)
        else:
            subprocess.Popen(command_to_run_list, shell=use_shell)
        
        return {"status": "success", "message": f"Attempted to open '{final_command_description}'."}
    except FileNotFoundError:
        return {"status": "error", "message": f"Command or application '{final_command_description}' not found. Ensure it's in PATH or provide the full path."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to open application '{app_name_or_path}' (command: {' '.join(command_to_run_list)}): {e}"}

def close_application(app_name: str):
    """
    Attempts to close all running instances of an application matching the given name.
    
    This function uses the 'psutil' library (if installed) to find processes by name 
    or executable path. It then attempts to terminate them gracefully, followed by a 
    force kill if necessary. This operation is OS-dependent and success can vary.
    Be cautious, as it might close unintended processes if the name is too generic.

    Args:
        app_name (str): The name of the application to close (e.g., "notepad", "chrome"). 
                        The match is case-insensitive and can be partial.
    """
    if not psutil:
        return {"status": "error", "message": "psutil library is required to close applications by name but not installed."}

    pids_to_terminate = []
    app_name_lower = app_name.lower()
    closed_app_names = set() # To report what was targeted

    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']): # Added cmdline for more info
            try:
                proc_info = proc.info
                proc_name_lower = proc_info.get('name', "").lower()
                proc_exe_lower = os.path.basename(proc_info.get('exe', "")).lower() if proc_info.get('exe') else ""
                
                # More specific matching:
                # 1. Exact match on common executable names (e.g., "notepad.exe")
                # 2. Substring match for process name or app name from map
                # 3. For macOS, .app names might appear in cmdline for some apps
                
                # Refine APP_MAP for executable names for better matching
                system_app_map = APP_MAP.get(platform.system().lower(), {})
                mapped_exe_lower = ""
                if app_name_lower in system_app_map:
                    mapped_command = system_app_map[app_name_lower]
                    if platform.system().lower() == "darwin" and not mapped_command.startswith("/"):
                        # For macOS, app names in map are often just the .app name without path
                        mapped_exe_lower = mapped_command.lower() + ".app" # Heuristic
                    else:
                        mapped_exe_lower = os.path.basename(mapped_command).lower()

                match = False
                if app_name_lower == proc_name_lower: # chrome == chrome
                    match = True
                    closed_app_names.add(proc_info.get('name'))
                elif app_name_lower == proc_exe_lower: # chrome == chrome.exe
                    match = True
                    closed_app_names.add(proc_info.get('exe'))
                elif mapped_exe_lower and mapped_exe_lower == proc_exe_lower: # notepad -> notepad.exe == notepad.exe
                    match = True
                    closed_app_names.add(proc_info.get('exe'))
                elif app_name_lower in proc_name_lower: # "note" in "notepad.exe"
                    match = True
                    closed_app_names.add(proc_info.get('name'))
                elif mapped_exe_lower and app_name_lower in mapped_exe_lower and mapped_exe_lower in proc_exe_lower: # vscode -> visual studio code in code.exe
                     match = True
                     closed_app_names.add(proc_info.get('exe'))

                if match:
                    # Avoid terminating self or critical system processes
                    if proc.pid == os.getpid():
                        continue
                    if "python" in proc_name_lower and proc_info.get('cmdline') and __file__ in proc_info.get('cmdline', []):
                        continue
                    pids_to_terminate.append(proc.pid)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue # Process might have ended or we don't have permission
        
        if not pids_to_terminate:
            return {"status": "error", "message": f"No running process found clearly matching name '{app_name}'. Be more specific or check running processes."}

        terminated_count = 0
        unique_pids = list(set(pids_to_terminate)) # Remove duplicates

        for pid in unique_pids:
            try:
                process = psutil.Process(pid)
                process_name_for_log = process.name() # Get name before it's potentially gone
                process.terminate()
                process.wait(timeout=0.5) # Shorter wait
                if process.is_running():
                    process.kill()
                    process.wait(timeout=0.5) # Wait after kill too
                if not process.is_running():
                    terminated_count += 1
                    print(f"Terminated PID {pid} ({process_name_for_log})")
            except psutil.NoSuchProcess:
                terminated_count +=1 # Count it if it disappeared after we found it
                print(f"PID {pid} already exited.")
            except psutil.AccessDenied:
                 print(f"Access denied terminating PID {pid} for '{app_name}'.")
            except Exception as e_term:
                print(f"Error during termination of PID {pid} for '{app_name}': {e_term}")
        
        if terminated_count > 0:
            targeted_apps_str = ", ".join(filter(None, closed_app_names)) or app_name
            return {"status": "success", "message": f"Attempted to terminate {terminated_count} process(es) related to '{targeted_apps_str}'."}
        else:
            return {"status": "error", "message": f"Found PIDs for '{app_name}' but failed to terminate them. Check permissions or if the processes are critical."}

    except Exception as e:
        return {"status": "error", "message": f"General error while trying to close application '{app_name}': {e}"}


COMMANDS = {
    "app_open": open_application,
    "app_close": close_application,
}