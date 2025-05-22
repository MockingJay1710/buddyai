# agent/modules/system_info_control.py
import os
import platform
import shutil # For disk_usage
# For system load, psutil is highly recommended: pip install psutil
# For screenshots, Pillow is needed: pip install Pillow
# For volume control, it's OS-specific. Example for Windows using pycaw: pip install pycaw
# For macOS: osascript commands. For Linux: amixer/pactl commands.

try:
    import psutil
except ImportError:
    psutil = None
    print("Warning: psutil library not found. 'sys_get_load' functionality will be limited or may not work.")

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None
    print("Warning: Pillow (PIL) library not found. 'sys_take_screenshot' functionality will not work.")

# --- Volume Control (OS Specific - Example for Windows with pycaw) ---
WINDOWS_VOLUME_INTERFACE = None # Initialize
if platform.system() == "Windows":
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        WINDOWS_VOLUME_INTERFACE = AudioUtilities.CoCreateInstance(interface, IAudioEndpointVolume) # Corrected assignment
    except Exception as e: # Catch specific exception if possible, or general Exception
        WINDOWS_VOLUME_INTERFACE = None # Ensure it's None on failure
        print(f"Warning: pycaw library or Windows audio setup issue: {e}. Windows volume control may not work.")
# --- End Volume Control Example ---


def get_system_load():
    """
    Gets the current CPU and Memory load percentages of the system.
    
    This function requires the 'psutil' library to be installed.
    Returns CPU load over a 1-second interval and current memory usage details.
    """
    if not psutil:
        return {"status": "error", "message": "psutil library is required for system load but not installed."}
    try:
        cpu_load = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        return {
            "status": "success",
            "cpu_percent": cpu_load,
            "memory_percent": memory_info.percent,
            "memory_total_gb": round(memory_info.total / (1024**3), 2),
            "memory_used_gb": round(memory_info.used / (1024**3), 2),
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get system load: {e}"}

def get_disk_space(path: str = "/"):
    """
    Gets disk space information (total, used, free) for a given file system path.
    
    Defaults to the root directory ("/") for Linux/macOS, or "C:\\" for Windows if "/" is given.
    
    Args:
        path (str, optional): The file system path to check (e.g., "/", "/mnt/data", "D:\\"). 
                              Defaults to "/" (which is adjusted for Windows).
    """
    current_system = platform.system()
    effective_path = path
    if current_system == "Windows" and path == "/":
        effective_path = "C:\\"
    elif current_system == "Windows" and not (":" in path and os.path.exists(os.path.splitdrive(path)[0] + os.sep)): # check if it's a valid drive like D:
        # If a single letter is given without ':', assume it's a drive letter.
        if len(path) == 1 and path.isalpha():
            effective_path = f"{path.upper()}:\\"
        # Could add more robust path validation for Windows here if needed
        
    try:
        total, used, free = shutil.disk_usage(effective_path)
        return {
            "status": "success",
            "path_checked": effective_path,
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent_used": round((used / total) * 100, 2)
        }
    except FileNotFoundError:
        return {"status": "error", "message": f"Path '{effective_path}' not found or not accessible for disk usage."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get disk space for '{effective_path}': {e}"}

def set_system_volume(level: int):
    """
    Sets the system's master audio output volume to a specified percentage.
    
    The volume level should be an integer between 0 (mute) and 100 (max).
    Implementation is OS-dependent. Current support includes Windows (via pycaw),
    macOS (via osascript), and Linux (via pactl/amixer).

    Args:
        level (int): The desired volume level (0-100).
    """
    if not (0 <= level <= 100):
        return {"status": "error", "message": "Volume level must be an integer between 0 and 100."}

    system = platform.system()
    try:
        if system == "Windows":
            if WINDOWS_VOLUME_INTERFACE:
                WINDOWS_VOLUME_INTERFACE.SetMasterVolumeLevelScalar(level / 100.0, None)
                return {"status": "success", "message": f"Windows volume set to {level}%."}
            else:
                return {"status": "error", "message": "Windows volume control (pycaw) not available or not initialized."}
        elif system == "Darwin": # macOS
            import subprocess
            subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True, capture_output=True)
            return {"status": "success", "message": f"macOS volume set to {level}%."}
        elif system == "Linux":
            import subprocess
            try:
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"], check=True, capture_output=True)
                return {"status": "success", "message": f"Linux volume (pactl) set to {level}%."}
            except (FileNotFoundError, subprocess.CalledProcessError):
                try:
                    subprocess.run(["amixer", "-q", "-D", "pulse", "sset", "Master", f"{level}%"], check=True, capture_output=True) # -q for quiet
                    return {"status": "success", "message": f"Linux volume (amixer) set to {level}%."}
                except Exception as linux_e:
                     return {"status": "error", "message": f"Linux volume control failed: {linux_e}. Ensure amixer or pactl is installed and configured."}
        else:
            return {"status": "error", "message": f"Volume control not implemented for OS: {system}"}
    except subprocess.CalledProcessError as cpe:
        return {"status": "error", "message": f"Failed to set volume on {system}. Command '{cpe.cmd}' failed with code {cpe.returncode}. Output: {cpe.stderr.decode() if cpe.stderr else cpe.stdout.decode() if cpe.stdout else 'No output'}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to set volume to {level}% on {system}: {e}"}


def take_screenshot(output_path: str = "screenshot.png"):
    """
    Takes a screenshot of the entire screen and saves it to the specified file path.
    
    Requires the 'Pillow' (PIL) library to be installed.
    If no valid image extension is provided in output_path, defaults to ".png".

    Args:
        output_path (str, optional): The file path where the screenshot will be saved. 
                                     Defaults to "screenshot.png" in the agent's current working directory.
    """
    if not ImageGrab:
        return {"status": "error", "message": "Pillow (PIL) library is required for screenshots but not installed."}
    try:
        # Ensure output_path has a valid image extension
        file_name, file_ext = os.path.splitext(output_path)
        if not file_ext.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
            output_path = file_name + ".png"

        abs_output_path = os.path.abspath(output_path) # Get absolute path for clarity in message
        # Ensure directory exists if a path is specified
        output_dir = os.path.dirname(abs_output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)


        screenshot = ImageGrab.grab()
        screenshot.save(abs_output_path)
        return {"status": "success", "message": f"Screenshot saved to '{abs_output_path}'."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to take screenshot: {e}"}

COMMANDS = {
    "sys_get_load": get_system_load,
    "sys_get_disk": get_disk_space,
    "sys_set_volume": set_system_volume,
    "sys_take_screenshot": take_screenshot,
}