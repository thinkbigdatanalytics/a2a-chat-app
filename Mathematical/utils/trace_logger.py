from datetime import datetime

def trace(sender, receiver, message):
    with open("math_trace.log", "a") as f:
        f.write(f"[{datetime.now()}] {sender} → {receiver}: {message}\n")
