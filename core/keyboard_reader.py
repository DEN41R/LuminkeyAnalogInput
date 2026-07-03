import hid
import time
import threading
from .log_utils import add_log

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
        add_log("Starting keyboard auto-discovery...")
        devices = hid.enumerate()
        target_paths = []
        for d in devices:
            try:
                path_str = d['path'].decode('utf-8', errors='ignore').lower()
            except:
                path_str = str(d['path']).lower()
                
            mfr = d.get('manufacturer_string', '')
            prod = d.get('product_string', '')
            if not mfr: mfr = ""
            if not prod: prod = ""
            
            is_luminkey = 'luminkey' in mfr.lower() or 'g-come' in mfr.lower() or 'magger' in prod.lower() or 'luminkey' in prod.lower()
            is_receiver = 'compx' in mfr.lower() or 'rdmctmzt' in mfr.lower()
            
            if is_luminkey or is_receiver:
                if 'mi_01' in path_str or (d['usage_page'] == 0x0001 and d['usage'] == 0x0000) or d['usage_page'] >= 0xFF00:
                    if d['path'] not in target_paths:
                        target_paths.append(d['path'])
                        add_log(f"Candidate found: VID={d['vendor_id']:04x} PID={d['product_id']:04x} UP={d['usage_page']:04x} Usage={d['usage']:04x} Path={path_str}")
        
        if not target_paths:
            add_log("ERROR: No candidate endpoints found at all!")
            raise Exception("Luminkey keyboard not found! Check connection.")
            
        self.candidate_devices = []
        for path in target_paths:
            try:
                dev = hid.device()
                dev.open_path(path)
                dev.set_nonblocking(True)
                self.candidate_devices.append(dev)
            except Exception as e:
                add_log(f"Failed to open {path}: {e}")
                
        if not self.candidate_devices:
            add_log("ERROR: Found candidates, but could not open ANY of them. Run as admin?")
            raise Exception("Found Luminkey endpoints, but failed to open them (access denied?).")
        
        add_log(f"Opened {len(self.candidate_devices)} candidate endpoints. Awaiting keypress to lock on...")
        self.device = None

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
        if hasattr(self, 'candidate_devices'):
            for d in self.candidate_devices:
                try: d.close()
                except: pass
            self.candidate_devices = []

    def _read_loop(self):
        while self.running:
            try:
                if self.device is None:
                   
                    found = False
                    for dev in self.candidate_devices:
                        try:
                            data = dev.read(256)
                            if data:
                                if len(data) >= 8 and data[0] == 0xa0 and data[1] == 0x10 and data[2] == 0x00:
                                    self.device = dev
                                    found = True
                                    add_log("SUCCESS: Locked onto active analog stream!")
                                  
                                    for other in self.candidate_devices:
                                        if other != dev:
                                            try: other.close()
                                            except: pass
                                    self.candidate_devices = []
                                    break
                        except Exception as inner_e:
                            
                            pass
                            
                    if not found:
                        time.sleep(0.01)
                        continue

                data = self.device.read(256)
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
            except Exception as e:
                time.sleep(0.01)

    def get_key_state(self, keycode):
        return self.key_states.get(keycode, 0.0)
