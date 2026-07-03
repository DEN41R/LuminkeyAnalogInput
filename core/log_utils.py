import time
import threading

log_messages = []
log_callbacks = []
log_lock = threading.Lock()

def add_log(msg):
    t = time.strftime('%H:%M:%S')
    formatted = f'[{t}] {msg}'
    print(formatted)
    with log_lock:
        log_messages.append(formatted)
        if len(log_messages) > 500:
            log_messages.pop(0)
        for cb in log_callbacks:
            try:
                cb(formatted)
            except:
                pass

def register_log_callback(cb):
    with log_lock:
        if cb not in log_callbacks:
            log_callbacks.append(cb)

def unregister_log_callback(cb):
    with log_lock:
        if cb in log_callbacks:
            log_callbacks.remove(cb)

def get_all_logs():
    with log_lock:
        return list(log_messages)

