import datetime

def get_server_time():
    now = datetime.datetime.now()
    return {"status": "success", "current_time": now.isoformat()}

def greet_user(name="Guest"):
    return {"status": "success", "message": f"Hello, {name}!"}

COMMANDS = {
    "tell_time": get_server_time,
    "greet": greet_user
}