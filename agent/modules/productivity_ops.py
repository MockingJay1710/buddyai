# agent/modules/productivity_ops.py
import datetime
import threading
# For clipboard, pyperclip is excellent: pip install pyperclip
try:
    import pyperclip
except ImportError:
    pyperclip = None
    print("Warning: pyperclip library not found. Clipboard functions will not work.")

# Simple in-memory store for reminders. Will be lost on agent restart.
REMINDERS: dict = {} # Type hint for REMINDERS
REMINDER_ID_COUNTER: int = 0 # Type hint for counter

def _show_reminder(reminder_id: int, message: str):
    """
    Internal helper function called by a threading.Timer to display a reminder.
    It also cleans up the reminder from the active REMINDERS dictionary.
    This function is not intended to be called directly by the user/LLM.
    """
    print(f"\n🔔 REMINDER (ID: {reminder_id}): {message}\n")
    # Clean up the reminder from the store once shown
    if reminder_id in REMINDERS:
        del REMINDERS[reminder_id]

def set_reminder(time_str: str, message: str):
    """
    Sets a reminder for a future time with a given message.
    
    Time format can be "HH:MM" (24-hour format for today/tomorrow) or 
    "YYYY-MM-DD HH:MM" for a specific date and time. If only "HH:MM" is given
    and that time has passed for today, the reminder is set for the next day.
    Reminders are stored in memory and will be lost if the agent restarts.

    Args:
        time_str (str): The time for the reminder. Formats: "HH:MM" or "YYYY-MM-DD HH:MM".
        message (str): The message content for the reminder.
    """
    global REMINDER_ID_COUNTER
    now = datetime.datetime.now()
    reminder_time = None

    try:
        if len(time_str) == 5 and ':' in time_str: # HH:MM format
            hour, minute = map(int, time_str.split(':'))
            reminder_time_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if reminder_time_today < now:
                reminder_time = reminder_time_today + datetime.timedelta(days=1)
            else:
                reminder_time = reminder_time_today
        elif len(time_str) == 16 and time_str[4] == '-' and time_str[7] == '-' and time_str[10] == ' ' and time_str[13] == ':': # YYYY-MM-DD HH:MM format
            reminder_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        else:
            return {"status": "error", "message": "Invalid time format. Use 'HH:MM' or 'YYYY-MM-DD HH:MM'."}

        if reminder_time < now:
            return {"status": "error", "message": f"Cannot set reminder for a past time: {reminder_time.isoformat()}"}

        delay_seconds = (reminder_time - now).total_seconds()
        REMINDER_ID_COUNTER += 1
        current_id = REMINDER_ID_COUNTER

        timer = threading.Timer(delay_seconds, _show_reminder, args=[current_id, message])
        REMINDERS[current_id] = {
            'time_obj': reminder_time,
            'time_str': reminder_time.isoformat(),
            'message': message,
            'timer': timer
        }
        timer.start()
        
        return {"status": "success", "reminder_id": current_id, "message": f"Reminder (ID: {current_id}) set for {reminder_time.isoformat()} with message: '{message}'."}
    except ValueError: # Catches errors from map(int, ...) or strptime
        return {"status": "error", "message": "Invalid time string or components. Ensure HH, MM, YYYY, etc., are correct numbers and format is valid."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to set reminder: {e}"}

def list_reminders():
    """
    Lists all currently active (pending) reminders.
    
    Returns a list of reminders, each with its ID, scheduled time, and message.
    If no reminders are active, an appropriate message is returned.
    """
    if not REMINDERS:
        return {"status": "success", "reminders": [], "message": "No active reminders."}
    
    active_reminders = []
    for rid, r_info in REMINDERS.items():
        active_reminders.append({
            "id": rid,
            "time": r_info['time_str'],
            "message": r_info['message']
        })
    return {"status": "success", "reminders": active_reminders}

def cancel_reminder(reminder_id: int):
    """
    Cancels an active reminder specified by its unique ID.
    
    If the reminder ID is valid and the reminder is active, it will be cancelled.
    
    Args:
        reminder_id (int): The ID of the reminder to cancel. This ID is returned when a reminder is set.
    """
    try:
        # The type hint already suggests int, but int() conversion makes it robust if LLM sends string "1"
        rid = int(reminder_id) 
        if rid in REMINDERS:
            REMINDERS[rid]['timer'].cancel()
            del REMINDERS[rid]
            return {"status": "success", "message": f"Reminder ID {rid} cancelled."}
        else:
            return {"status": "error", "message": f"Reminder ID {rid} not found or already past."}
    except ValueError: # If reminder_id cannot be converted to int
        return {"status": "error", "message": "Invalid reminder ID format. Reminder ID must be an integer."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to cancel reminder ID {reminder_id}: {e}"}


def get_clipboard_content():
    """
    Gets the current text content from the system clipboard.
    
    This function requires the 'pyperclip' library to be installed.
    Returns the clipboard content as a string.
    """
    if not pyperclip:
        return {"status": "error", "message": "pyperclip library is required for clipboard access but not installed."}
    try:
        content = pyperclip.paste()
        return {"status": "success", "clipboard_content": content}
    except pyperclip.PyperclipException as e: # Catch specific pyperclip errors
        return {"status": "error", "message": f"Failed to get clipboard content (pyperclip error): {e}. Ensure a copy/paste mechanism is available (e.g., xclip or xsel on Linux)."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred while getting clipboard content: {e}"}

def set_clipboard_content(text: str):
    """
    Sets the system clipboard content to the provided text.
    
    This function requires the 'pyperclip' library to be installed.

    Args:
        text (str): The text to be copied to the clipboard.
    """
    if not pyperclip:
        return {"status": "error", "message": "pyperclip library is required for clipboard access but not installed."}
    try:
        pyperclip.copy(text)
        return {"status": "success", "message": "Clipboard content set."}
    except pyperclip.PyperclipException as e: # Catch specific pyperclip errors
        return {"status": "error", "message": f"Failed to set clipboard content (pyperclip error): {e}. Ensure a copy/paste mechanism is available (e.g., xclip or xsel on Linux)."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred while setting clipboard content: {e}"}

COMMANDS = {
    "prod_set_reminder": set_reminder,
    "prod_list_reminders": list_reminders,
    "prod_cancel_reminder": cancel_reminder,
    "prod_get_clipboard": get_clipboard_content,
    "prod_set_clipboard": set_clipboard_content,
}