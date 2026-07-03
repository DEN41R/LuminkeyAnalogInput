import time
import threading
import math
import os
import json
import vgamepad as vg
from .keyboard_reader import KeyboardReader
from .keymap import KEYCODES, SCANCODES
from .log_utils import add_log

import ctypes
from ctypes import wintypes
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [('wVk', ctypes.c_ushort), ('wScan', ctypes.c_ushort), ('dwFlags', ctypes.c_ulong), ('time', ctypes.c_ulong), ('dwExtraInfo', PUL)]
class HardwareInput(ctypes.Structure):
    _fields_ = [('uMsg', ctypes.c_ulong), ('wParamL', ctypes.c_short), ('wParamH', ctypes.c_ushort)]
class MouseInput(ctypes.Structure):
    _fields_ = [('dx', ctypes.c_long), ('dy', ctypes.c_long), ('mouseData', ctypes.c_ulong), ('dwFlags', ctypes.c_ulong), ('time', ctypes.c_ulong), ('dwExtraInfo', PUL)]
class Input_I(ctypes.Union):
    _fields_ = [('ki', KeyBdInput), ('mi', MouseInput), ('hi', HardwareInput)]
class Input(ctypes.Structure):
    _fields_ = [('type', ctypes.c_ulong), ('ii', Input_I)]

def press_virtual_key(key_name, is_press):
    scan_code = SCANCODES.get(key_name, 0)
    if scan_code == 0: return
    extra = ctypes.c_ulong(0)
    flags = 0x0008 
    if not is_press:
        flags |= 0x0002 
  
    if key_name in ["Up", "Down", "Left", "Right", "PgUp", "PgDn", "Home", "End", "Insert", "Delete", "RAlt", "RCtrl"]:
        flags |= 0x0001
    ii = Input_I()
    ii.ki = KeyBdInput(0, scan_code, flags, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

try:
    import win32gui
except ImportError:
    win32gui = None

CONFIG_FILE = "config.json"

class GamepadEmulator:
    def __init__(self):
        self.reader = KeyboardReader()
        self.dks_items = []
        
        self.drivers_ok = True
        try:
            self.gamepad = vg.VX360Gamepad()
        except Exception as e:
            add_log(f"ViGEmBus not found: {e}")
            self.drivers_ok = False
            self.gamepad = None
        self.running = False
        self.loop_thread = None
        
        self.block_running = False
        self.block_thread = None
        
        
        self.enabled = True
        self.gamepad_mode = False
        self.square_vector = False
        self.angle_snapping = 0
        self.language = "ru"
        self.snap_tap_items = []
        self.rt_items = []
        self.dks_items = []
        self.deadzone = 0.1
        self.max_distance = 4.0
        self.bindings = {}
        
        self.keycodes = KEYCODES
        
        self.vg_buttons = {
            "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            "LSB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            "RSB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            "Back": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            "Start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            "Guide": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
            "DPad_Up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            "DPad_Down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
            "DPad_Left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
            "DPad_Right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        }
        self.btn_state = {}
        self.st_state = {} 
        self.rt_state = {} 
        self.dks_state = {} 
        self.current_state = {
            'lx': 0, 'ly': 0, 'rx': 0, 'ry': 0,
            'lt': 0, 'rt': 0, 'buttons': []
        }

    def start(self):
        self.running = True
        self.reader.start()
        self.loop_thread = threading.Thread(target=self._loop, daemon=True)
        self.loop_thread.start()
        self.update_blocks()
        
    def stop(self):
        self.running = False
        self.reader.stop()
        if self.loop_thread:
            self.loop_thread.join()
        self.update_blocks()

    def update_blocks(self):
        if self.gamepad_mode and self.running:
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
        if not self.drivers_ok:
            return
            
        try:
            from interception.interception import Interception
            from interception import constants
        except ImportError:
            return

        ctx = None
        try:
            ctx = Interception()
            ctx.get_handles()
            ctx.set_filter(Interception.is_keyboard, constants.FilterKeyFlag.FILTER_KEY_ALL)
            
            while self.block_running:
                device_id = ctx.await_input(timeout_milliseconds=100)
                if device_id is None:
                    continue
                    
                stroke = ctx.devices[device_id].receive()
                if not stroke:
                    continue
                    
                if self.gamepad_mode:
                    pass 
                else:
                    ctx.devices[device_id].send(stroke)
        except Exception as e:
            add_log(f"Interception error: {e}")
        finally:
            if ctx:
                try:
                    ctx.destroy()
                except:
                    pass

    def apply_math(self, value):
        
        v_mm = value * 4.0
        
        pts = getattr(self, 'curve_points', None)
        if not pts or len(pts) < 4:
            dz = self.deadzone
            max_dist = self.max_distance
            if v_mm < dz: return 0.0
            if v_mm > max_dist: return 1.0
            rng = max_dist - dz
            if rng <= 0: return 1.0
            return (v_mm - dz) / rng
            
     
        if v_mm < pts[0]['x']: return 0.0
        if v_mm == pts[0]['x']: return pts[0]['y']
        if v_mm >= pts[-1]['x']: return pts[-1]['y']
        
        for i in range(len(pts) - 1):
            p1 = pts[i]
            p2 = pts[i+1]
            if p1['x'] <= v_mm <= p2['x']:
                rng = p2['x'] - p1['x']
                if rng <= 0: return p2['y']
                t = (v_mm - p1['x']) / rng
                return p1['y'] + t * (p2['y'] - p1['y'])
                
        return pts[-1]['y']

    def apply_angle_snapping(self, x, y):
        if self.angle_snapping <= 0:
            return x, y
        
        
        r = math.sqrt(x*x + y*y)
        if r == 0: return 0, 0
        
        theta = math.atan2(y, x)
        angle_rad = math.radians(self.angle_snapping)
        
        
        theta -= angle_rad * (1 if x > 0 else -1) * (1 if y > 0 else -1)
        
        return r * math.cos(theta), r * math.sin(theta)

    def apply_square_vector(self, x, y):
        if not self.square_vector:
            
            r = math.sqrt(x*x + y*y)
            if r > 1.0:
                x /= r
                y /= r
            return x, y
            
        
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        return x, y

    def _update_snaptap(self):
        if not self.snap_tap_items or self.gamepad_mode: return
        
        for idx, item in enumerate(self.snap_tap_items):
            k1 = item.get('key1', 'None')
            k2 = item.get('key2', 'None')
            if k1 == 'None' or k2 == 'None': continue
            
            if idx not in self.st_state:
                self.st_state[idx] = {'stack': [], 'active': None}
                
            state = self.st_state[idx]
            
           
            act = self.deadzone / 4.0
            
            v1 = self.reader.get_key_state(self.keycodes.get(k1, 0)) >= act
            v2 = self.reader.get_key_state(self.keycodes.get(k2, 0)) >= act
            
            pressed = []
            if v1: pressed.append(k1)
            if v2: pressed.append(k2)
            
            for k in list(state['stack']):
                if k not in pressed:
                    state['stack'].remove(k)
                    
            for k in pressed:
                if k not in state['stack']:
                    state['stack'].append(k)
                    
            target_active = state['stack'][-1] if state['stack'] else None
            
            if state['active'] != target_active:
                if state['active'] is not None:
                    press_virtual_key(state['active'], False)
                if target_active is not None:
                    press_virtual_key(target_active, True)
                state['active'] = target_active

    def _update_rapid_trigger(self):
        if not self.rt_items or self.gamepad_mode: return
        
        for idx, item in enumerate(self.rt_items):
            k = item.get('key', 'None')
            out_k = item.get('out_key', k)
            if k == 'None' or out_k == 'None': continue
            
            sens = float(item.get('rt_sens', 0.15)) / 4.0
            act = self.deadzone / 4.0
            
            kc = self.keycodes.get(k, 0)
            raw = self.reader.get_key_state(kc)
            
            if idx not in self.rt_state:
                self.rt_state[idx] = {'active': False, 'max': raw, 'min': raw}
                
            state = self.rt_state[idx]
            
            if not state['active']:
                state['min'] = min(state['min'], raw)
                if raw >= act or (raw - state['min']) >= sens:
                    state['active'] = True
                    state['max'] = raw
                    press_virtual_key(out_k, True)
            else:
                state['max'] = max(state['max'], raw)
                if (state['max'] - raw) >= sens or raw <= 0.01:
                    state['active'] = False
                    state['min'] = raw
                    press_virtual_key(out_k, False)

    def _update_dks(self):
        if not self.dks_items or self.gamepad_mode: return
        
        for idx, item in enumerate(self.dks_items):
            k = item.get('key', 'None')
            if k == 'None': continue
            
            kc = self.keycodes.get(k, 0)
            raw = self.reader.get_key_state(kc)
            
            if idx not in self.dks_state:
                self.dks_state[idx] = {'stage': 0}
                
            state = self.dks_state[idx]
            stage = state['stage']
            
           
            dz = self.deadzone / 4.0
            md = self.max_distance / 4.0
            mid = dz + (md - dz) / 2.0
            
            new_stage = 0
            if raw >= md: new_stage = 2
            elif raw >= dz: new_stage = 1
            
            if new_stage > stage:
              
                if new_stage == 1 and item.get('out1', 'None') != 'None':
                    press_virtual_key(item['out1'], True)
                    press_virtual_key(item['out1'], False)
                elif new_stage == 2 and item.get('out2', 'None') != 'None':
                    press_virtual_key(item['out2'], True)
                    press_virtual_key(item['out2'], False)
            elif new_stage < stage:
               
                if new_stage == 1 and item.get('out3', 'None') != 'None':
                    press_virtual_key(item['out3'], True)
                    press_virtual_key(item['out3'], False)
                elif new_stage == 0 and item.get('out4', 'None') != 'None':
                    press_virtual_key(item['out4'], True)
                    press_virtual_key(item['out4'], False)
                    
            state['stage'] = new_stage

    def _loop(self):
        if not self.drivers_ok:
            add_log("Drivers missing, gamepad emulator loop disabled.")
            return
            
        while self.running:
            t0 = time.perf_counter()
            
            self.reader.max_distance = 350.0
            
            if self.enabled:
                self._update_gamepad()
                self._update_snaptap()
                self._update_rapid_trigger()
                self._update_dks()
            
      
            elapsed = time.perf_counter() - t0
            sleep_time = 0.001 - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _update_gamepad(self):
  
        axes = {'LS_X': 0.0, 'LS_Y': 0.0, 'RS_X': 0.0, 'RS_Y': 0.0, 'LT': 0.0, 'RT': 0.0}
        
    
        btn_map = {}
        for k, v in self.bindings.items():
            if v not in btn_map: btn_map[v] = []
            btn_map[v].append(k)
            
        def get_val(action):
            val = 0.0
            for k in btn_map.get(action, []):
                kc = self.keycodes.get(k, 0)
                raw = self.reader.get_key_state(kc)
                val = max(val, self.apply_math(raw))
            return val
            
       
        lx_pos = get_val("LS_Right")
        lx_neg = get_val("LS_Left")
        ly_pos = get_val("LS_Up")
        ly_neg = get_val("LS_Down")
        lx = lx_pos - lx_neg
        ly = ly_pos - ly_neg
        
       
        rx_pos = get_val("RS_Right")
        rx_neg = get_val("RS_Left")
        ry_pos = get_val("RS_Up")
        ry_neg = get_val("RS_Down")
        rx = rx_pos - rx_neg
        ry = ry_pos - ry_neg
        
      
        lx, ly = self.apply_angle_snapping(lx, ly)
        lx, ly = self.apply_square_vector(lx, ly)
        rx, ry = self.apply_square_vector(rx, ry)
        
        self.gamepad.left_joystick_float(x_value_float=lx, y_value_float=ly)
        self.gamepad.right_joystick_float(x_value_float=rx, y_value_float=ry)
        
        self.gamepad.left_trigger_float(value_float=get_val("LT"))
        self.gamepad.right_trigger_float(value_float=get_val("RT"))
        
        
        pressed_buttons = []
        for b_name, vg_code in self.vg_buttons.items():
            val = get_val(b_name)
            is_pressed = self.btn_state.get(b_name, False)
            threshold = 0.01 if is_pressed else 0.05
            
            if val >= threshold:
                self.gamepad.press_button(button=vg_code)
                self.btn_state[b_name] = True
                pressed_buttons.append(b_name)
            else:
                self.gamepad.release_button(button=vg_code)
                self.btn_state[b_name] = False
                
       
        raw_pressed = {}
        for k, kc in self.keycodes.items():
            r = self.reader.get_key_state(kc)
            if r > 0.02:
                raw_pressed[k] = r
                
        self.current_state = {
            'lx': lx, 'ly': ly, 'rx': rx, 'ry': ry,
            'lt': get_val("LT"), 'rt': get_val("RT"),
            'buttons': pressed_buttons,
            'raw_keys': raw_pressed
        }
                
        try:
            self.gamepad.update()
        except Exception as e:
            add_log(f"vgamepad update error: {e}")
