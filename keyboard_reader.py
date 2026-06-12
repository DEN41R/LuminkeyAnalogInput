import hid
import time
import threading

TARGET_VID = 0x19f5
TARGET_PID = 0xfc66

class KeyboardReader:
    def __init__(self):
        self.device = None
        self.running = False
        self.key_states = {} 
        self.thread = None
        self.listen_callback = None
        
       
        self.max_distance = 350.0 

    def set_listen_callback(self, callback):
        self.listen_callback = callback

    def connect(self):
        devices = hid.enumerate(TARGET_VID, TARGET_PID)
        target_path = None
        for d in devices:
            try:
                path_str = d['path'].decode('utf-8', errors='ignore')
            except:
                path_str = str(d['path'])
            if 'MI_01' in path_str:
                target_path = d['path']
                break
        
        if not target_path:
            raise Exception("Luminkey Magger 68 HE (MI_01) не найдена! Проверьте подключение.")
            
        self.device = hid.device()
        self.device.open_path(target_path)
        self.device.set_nonblocking(True)

    def start(self):
        if not self.device:
            self.connect()
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.device:
            self.device.close()
            self.device = None

    def _read_loop(self):
        while self.running:
            try:
                data = self.device.read(64)
                if data and len(data) >= 8 and data[0] == 0xa0 and data[1] == 0x10 and data[2] == 0x00:
                    keycode = data[3]
                    
                    distance_raw = (data[6] << 8) | data[7]
                    
                  
                    normalized = distance_raw / self.max_distance
                    normalized = min(1.0, max(0.0, normalized))
                    
                    self.key_states[keycode] = normalized
                    
                    if normalized > 0.3 and self.listen_callback:
                        cb = self.listen_callback
                        self.listen_callback = None
                        cb(keycode)
                else:
                    time.sleep(0.001)
            except:
                time.sleep(0.01)

    def get_key_state(self, keycode):
        return self.key_states.get(keycode, 0.0)
