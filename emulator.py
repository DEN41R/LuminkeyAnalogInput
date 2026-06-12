import vgamepad as vg
import threading
import time
import json
import os
import math
import subprocess
import copy
from keymap import KEYCODES, SCANCODES

try:
    from interception.interception import Interception
    from interception import constants
    INTERCEPTION_AVAILABLE = True
except:
    INTERCEPTION_AVAILABLE = False

def get_config_path():
    appdata = os.environ.get('APPDATA', '')
    dir_path = os.path.join(appdata, 'LuminkeyAnalog')
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return os.path.join(dir_path, 'config.json')

CONFIG_FILE = get_config_path()

class GamepadEmulator:
    def __init__(self, reader):
        self.reader = reader
        self.gamepad = vg.VX360Gamepad()
        self.running = False
        self.thread = None
        self.block_thread = None
        self.block_running = False
        
     
        self.config = {
            "polling_rate_ms": 5,
            "max_distance": 350.0,
            "block_keys": False,
            "axes": {
                "LT": {"key": "S", "start_dz": 0.05, "end_dz": 0.05, "curve": "Linear"},
                "RT": {"key": "W", "start_dz": 0.05, "end_dz": 0.05, "curve": "Linear"},
                "LX_NEG": {"key": "A", "start_dz": 0.05, "end_dz": 0.05, "curve": "Linear"},
                "LX_POS": {"key": "D", "start_dz": 0.05, "end_dz": 0.05, "curve": "Linear"},
                "LY_NEG": {"key": "None", "start_dz": 0.05, "end_dz": 0.05, "curve": "Linear"},
                "LY_POS": {"key": "None", "start_dz": 0.05, "end_dz": 0.05, "curve": "Linear"},
                "RX_NEG": {"key": "None", "start_dz": 0.05, "end_dz": 0.05, "curve": "Linear"},
                "RX_POS": {"key": "None", "start_dz": 0.05, "end_dz": 0.05, "curve": "Linear"},
                "RY_NEG": {"key": "None", "start_dz": 0.05, "end_dz": 0.05, "curve": "Linear"},
                "RY_POS": {"key": "None", "start_dz": 0.05, "end_dz": 0.05, "curve": "Linear"},
            },
            "buttons": {
                "A": {"key": "Space", "actuation": 0.5},
                "B": {"key": "None", "actuation": 0.5},
                "X": {"key": "None", "actuation": 0.5},
                "Y": {"key": "None", "actuation": 0.5},
                "LB": {"key": "None", "actuation": 0.5},
                "RB": {"key": "None", "actuation": 0.5},
                "LSB": {"key": "None", "actuation": 0.5},
                "RSB": {"key": "None", "actuation": 0.5},
                "BACK": {"key": "None", "actuation": 0.5},
                "START": {"key": "None", "actuation": 0.5},
                "GUIDE": {"key": "None", "actuation": 0.5},
                "DPAD_UP": {"key": "None", "actuation": 0.5},
                "DPAD_DOWN": {"key": "None", "actuation": 0.5},
                "DPAD_LEFT": {"key": "None", "actuation": 0.5},
                "DPAD_RIGHT": {"key": "None", "actuation": 0.5},
            }
        }
        
        self.keycodes = KEYCODES
        self.scancodes = SCANCODES
        
        self.vg_buttons = {
            "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            "LSB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            "RSB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            "BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            "START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            "GUIDE": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
            "DPAD_UP": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            "DPAD_DOWN": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
            "DPAD_LEFT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
            "DPAD_RIGHT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        }
        
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    def update_dict(d, u):
                        for k, v in u.items():
                            if isinstance(v, dict):
                                d[k] = update_dict(d.get(k, {}), v)
                            else:
                                d[k] = v
                        return d
                    update_dict(self.config, data)
            except Exception as e:
                print(f"Error loading config: {e}")
                
        self.reader.max_distance = self.config.get("max_distance", 350.0)
        self.update_blocks()

    def update_blocks(self):
      
        if self.config.get("block_keys", False) and self.running:
            if not self.block_thread:
                self.block_running = True
                self.block_thread = threading.Thread(target=self._interception_loop, daemon=True)
                self.block_thread.start()
        else:
            self.block_running = False
            if self.block_thread:
                self.block_thread.join()
                self.block_thread = None

    def _interception_loop(self):
        try:
            from interception.interception import Interception
            from interception import constants
        except ImportError:
            print("Interception package not installed.")
            return

        ctx = Interception()
        

        
        ctx.get_handles()
        ctx.set_filter(Interception.is_keyboard, constants.FilterKeyFlag.FILTER_KEY_ALL)
        
        while self.block_running:
            device_id = ctx.await_input(timeout_milliseconds=50)
            if device_id is None:
                continue
                
            stroke = ctx.devices[device_id].receive()
            if not stroke:
                continue
                
     
            keys_to_block = set()
            for conf in self.config['axes'].values():
                if conf['key'] != "None":
                    sc = self.scancodes.get(conf['key'])
                    if sc: keys_to_block.add(sc)
            for conf in self.config['buttons'].values():
                if conf['key'] != "None":
                    sc = self.scancodes.get(conf['key'])
                    if sc: keys_to_block.add(sc)
                    
            if stroke.code in keys_to_block:
             
                continue
                
            ctx.devices[device_id].send(stroke)
            
        ctx.destroy()

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def start(self):
        self.running = True
        self.update_blocks()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.update_blocks() 
        if self.thread:
            self.thread.join()

    def apply_math(self, value, start_dz, end_dz, curve):
        if value < start_dz:
            return 0.0
        if value > (1.0 - end_dz):
            return 1.0
            
        range_val = 1.0 - start_dz - end_dz
        if range_val <= 0:
            return 1.0
            
        norm = (value - start_dz) / range_val
        
        if curve == "Exponential":
            norm = math.pow(norm, 2.0)
        elif curve == "Logarithmic":
            norm = math.pow(norm, 0.5)
            
        return norm

    def _loop(self):
        while self.running:
            self._update_gamepad()
            time.sleep(self.config.get("polling_rate_ms", 5) / 1000.0)

    def _update_gamepad(self):
        
        axis_vals = {}
        for axis_name, axis_conf in self.config['axes'].items():
            kc = self.keycodes.get(axis_conf['key'], 0)
            raw_val = self.reader.get_key_state(kc)
            val = self.apply_math(raw_val, axis_conf['start_dz'], axis_conf['end_dz'], axis_conf['curve'])
            axis_vals[axis_name] = val
            
        self.gamepad.right_trigger_float(value_float=axis_vals.get('RT', 0.0))
        self.gamepad.left_trigger_float(value_float=axis_vals.get('LT', 0.0))
        
        lx = axis_vals.get('LX_POS', 0.0) - axis_vals.get('LX_NEG', 0.0)
        ly = axis_vals.get('LY_POS', 0.0) - axis_vals.get('LY_NEG', 0.0)
        self.gamepad.left_joystick_float(x_value_float=lx, y_value_float=ly)
        
        rx = axis_vals.get('RX_POS', 0.0) - axis_vals.get('RX_NEG', 0.0)
        ry = axis_vals.get('RY_POS', 0.0) - axis_vals.get('RY_NEG', 0.0)
        self.gamepad.right_joystick_float(x_value_float=rx, y_value_float=ry)
        
      
        for btn_name, btn_conf in self.config['buttons'].items():
            kc = self.keycodes.get(btn_conf['key'], 0)
            raw_val = self.reader.get_key_state(kc)
            vg_btn = self.vg_buttons[btn_name]
            
            if raw_val >= btn_conf['actuation']:
                self.gamepad.press_button(button=vg_btn)
            else:
                self.gamepad.release_button(button=vg_btn)
                
        self.gamepad.update()
