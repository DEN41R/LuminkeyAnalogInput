import sys
import os
import json
import webview
from core.emulator import GamepadEmulator
from core import log_utils

CONFIG_FILE = "config.json"

def check_drivers():
    missing = []
    

    try:
        import vgamepad as vg
        test = vg.VX360Gamepad()
        test.reset()
        test.update()
        del test
    except Exception as e:
        missing.append("ViGEmBus")
        
  
    try:
        from interception.interception import Interception
        ctx = Interception()
    except Exception:
        missing.append("Interception")
        
   
    if not os.path.exists(r"C:\Program Files\Nefarius Software Solutions\HidHide"):
        missing.append("HidHide")
        
    return missing

class WebAPI:
    def __init__(self):
        self.emulator = GamepadEmulator()
        self.emulator.start()
        
    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                
      
            self.emulator.bindings = config.get("bindings", {})
            self.emulator.gamepad_mode = config.get("gamepad_mode", False)
            self.emulator.curve_points = config.get("curve_points", None)
            if self.emulator.curve_points is None:
                dz = float(config.get("deadzone", 0.1))
                mx = float(config.get("max_distance", 4.0))
                self.emulator.curve_points = [
                    {"x": dz, "y": 0.0},
                    {"x": dz + 0.5, "y": 0.25},
                    {"x": mx - 0.5, "y": 0.75},
                    {"x": mx, "y": 1.0}
                ]
            
            
            self.emulator.deadzone = self.emulator.curve_points[0]['x']
            self.emulator.max_distance = self.emulator.curve_points[-1]['x']
            
            self.emulator.square_vector = config.get("square_vector", False)
            self.emulator.angle_snapping = int(config.get("angle_snapping", 0))
            self.emulator.language = config.get("language", "ru")
            self.emulator.snap_tap_items = config.get("snap_tap_items", [])
            self.emulator.rt_items = config.get("rt_items", [])
            self.emulator.dks_items = config.get("dks_items", [])
            self.emulator.enabled = config.get("enabled", True)
            
            self.emulator.update_blocks()
            
            return config
        except Exception as e:
            print("Failed to load config:", e)
            return {
                "enabled": True,
                "gamepad_mode": False,
                "square_vector": False,
                "angle_snapping": 0,
                "snap_tap_items": [],
                "rt_items": [],
                "dks_items": [],
                "deadzone": 0.1,
                "max_distance": 4.0,
                "bindings": {}
            }

    def save_config(self, config_data):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
                
            
            self.emulator.bindings = config_data.get("bindings", {})
            self.emulator.gamepad_mode = config_data.get("gamepad_mode", False)
            self.emulator.deadzone = float(config_data.get("deadzone", 0.1))
            self.emulator.max_distance = float(config_data.get("max_distance", 4.0))
            self.emulator.square_vector = config_data.get("square_vector", False)
            self.emulator.angle_snapping = int(config_data.get("angle_snapping", 0))
            self.emulator.snap_tap_items = config_data.get("snap_tap_items", [])
            self.emulator.rt_items = config_data.get("rt_items", [])
            self.emulator.dks_items = config_data.get("dks_items", [])
            self.emulator.enabled = config_data.get("enabled", True)
            
            self.emulator.update_blocks()
            
            return True
        except Exception as e:
            print("Failed to save config:", e)
            return False

    def get_logs(self):
        return log_utils.get_logs()

    def get_missing_drivers(self):
        return check_drivers()

    def get_live_data(self):
        return self.emulator.current_state

def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    if not is_admin():
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    api = WebAPI()
    
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_path, 'web', 'index.html')
    
    window = webview.create_window(
        'Luminkey Controller',
        html_path,
        js_api=api,
        width=1100,
        height=800,
        min_size=(900, 600),
        background_color='#141414',
        frameless=False
    )
    
    webview.start(debug=False)

if __name__ == '__main__':
    main()
