import sys
import os
import ctypes
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QMessageBox
from qfluentwidgets import (setTheme, Theme, SubtitleLabel, ProgressBar, 
                            BodyLabel, ComboBox, CardWidget, Slider, PushButton,
                            FluentWindow, NavigationItemPosition, ScrollArea, SpinBox, SwitchButton, SimpleCardWidget)
from qfluentwidgets import FluentIcon as FIF

from keyboard_reader import KeyboardReader
from emulator import GamepadEmulator
import driver_manager
from keymap import INV_KEYCODES

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AxisCard(CardWidget):
    def __init__(self, axis_id, title, emulator, main_window, parent=None):
        super().__init__(parent)
        self.emulator = emulator
        self.axis_id = axis_id
        self.main_window = main_window
        
        self.vbox = QVBoxLayout(self)
        self.title_label = SubtitleLabel(title, self)
        self.vbox.addWidget(self.title_label)
        
  
        self.bind_btn = PushButton(f"Button: {self.emulator.config['axes'][axis_id]['key']}")
        self.bind_btn.clicked.connect(self.start_binding)
        self.vbox.addWidget(self.bind_btn)
        
        self.curve_combo = ComboBox()
        self.curve_combo.addItems(["Linear", "Exponential", "Logarithmic"])
        self.curve_combo.setCurrentText(self.emulator.config['axes'][axis_id]['curve'])
        self.curve_combo.currentTextChanged.connect(self.on_curve_changed)
        self.vbox.addWidget(self.curve_combo)
        
        self.bar = ProgressBar(self)
        self.vbox.addWidget(self.bar)
        
        self.val_label = BodyLabel("Raw: 0.0% | Output: 0.0%", self)
        self.vbox.addWidget(self.val_label)
        
        self.sdz_label = BodyLabel(f"Deadzone (Start): {int(self.emulator.config['axes'][axis_id]['start_dz'] * 100)}%")
        self.vbox.addWidget(self.sdz_label)
        self.sdz_slider = Slider(Qt.Orientation.Horizontal, self)
        self.sdz_slider.setRange(0, 50)
        self.sdz_slider.setValue(int(self.emulator.config['axes'][axis_id]['start_dz'] * 100))
        self.sdz_slider.valueChanged.connect(self.on_sdz_changed)
        self.vbox.addWidget(self.sdz_slider)
        
        self.edz_label = BodyLabel(f"Deadzone (End): {int(self.emulator.config['axes'][axis_id]['end_dz'] * 100)}%")
        self.vbox.addWidget(self.edz_label)
        self.edz_slider = Slider(Qt.Orientation.Horizontal, self)
        self.edz_slider.setRange(0, 50)
        self.edz_slider.setValue(int(self.emulator.config['axes'][axis_id]['end_dz'] * 100))
        self.edz_slider.valueChanged.connect(self.on_edz_changed)
        self.vbox.addWidget(self.edz_slider)
        
    def start_binding(self):
        self.bind_btn.setText("Press any key...")
        self.bind_btn.setEnabled(False)
        self.main_window.start_listening(self)
        
    def finish_binding(self, keycode):
        key_name = INV_KEYCODES.get(keycode, "None")
        self.emulator.config['axes'][self.axis_id]['key'] = key_name
        self.bind_btn.setText(f"Button: {key_name}")
        self.bind_btn.setEnabled(True)
        self.emulator.update_blocks()
        self.emulator.save_config()
        
    def on_curve_changed(self, text):
        self.emulator.config['axes'][self.axis_id]['curve'] = text
        self.emulator.save_config()

    def on_sdz_changed(self, val):
        self.emulator.config['axes'][self.axis_id]['start_dz'] = val / 100.0
        self.sdz_label.setText(f"Deadzone (Start): {val}%")
        self.emulator.save_config()
        
    def on_edz_changed(self, val):
        self.emulator.config['axes'][self.axis_id]['end_dz'] = val / 100.0
        self.edz_label.setText(f"Deadzone (End): {val}%")
        self.emulator.save_config()
        
    def update_ui(self):
        conf = self.emulator.config['axes'][self.axis_id]
        kc = self.emulator.keycodes.get(conf['key'], 0)
        raw_val = self.emulator.reader.get_key_state(kc)
        eff_val = self.emulator.apply_math(raw_val, conf['start_dz'], conf['end_dz'], conf['curve'])
        
        self.bar.setValue(int(raw_val * 100))
        self.val_label.setText(f"Raw: {raw_val*100:.1f}% | Output: {eff_val*100:.1f}%")

class ButtonCard(CardWidget):
    def __init__(self, btn_id, title, emulator, main_window, parent=None):
        super().__init__(parent)
        self.emulator = emulator
        self.btn_id = btn_id
        self.main_window = main_window
        
        self.vbox = QVBoxLayout(self)
        self.title_label = SubtitleLabel(title, self)
        self.vbox.addWidget(self.title_label)
        
        self.bind_btn = PushButton(f"Button: {self.emulator.config['buttons'][btn_id]['key']}")
        self.bind_btn.clicked.connect(self.start_binding)
        self.vbox.addWidget(self.bind_btn)
        
        self.bar = ProgressBar(self)
        self.vbox.addWidget(self.bar)
        
        self.val_label = BodyLabel("Raw: 0.0% | Actuation: 50.0%", self)
        self.vbox.addWidget(self.val_label)
        
        self.act_slider = Slider(Qt.Orientation.Horizontal, self)
        self.act_slider.setRange(1, 99)
        self.act_slider.setValue(int(self.emulator.config['buttons'][btn_id]['actuation'] * 100))
        self.act_slider.valueChanged.connect(self.on_act_changed)
        self.vbox.addWidget(self.act_slider)
        
    def start_binding(self):
        self.bind_btn.setText("Press any key...")
        self.bind_btn.setEnabled(False)
        self.main_window.start_listening(self)
        
    def finish_binding(self, keycode):
        key_name = INV_KEYCODES.get(keycode, "None")
        self.emulator.config['buttons'][self.btn_id]['key'] = key_name
        self.bind_btn.setText(f"Button: {key_name}")
        self.bind_btn.setEnabled(True)
        self.emulator.update_blocks()
        self.emulator.save_config()
        
    def on_act_changed(self, val):
        self.emulator.config['buttons'][self.btn_id]['actuation'] = val / 100.0
        self.emulator.save_config()
        
    def update_ui(self):
        conf = self.emulator.config['buttons'][self.btn_id]
        kc = self.emulator.keycodes.get(conf['key'], 0)
        raw_val = self.emulator.reader.get_key_state(kc)
        is_pressed = raw_val >= conf['actuation']
        
        self.bar.setValue(int(raw_val * 100))
        if is_pressed:
            self.val_label.setText(f"Raw: {raw_val*100:.1f}% | Actuation: {conf['actuation']*100:.1f}% [PRESSED]")
        else:
            self.val_label.setText(f"Raw: {raw_val*100:.1f}% | Actuation: {conf['actuation']*100:.1f}%")

class DashboardPage(QWidget):
    def __init__(self, emulator, parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardPage")
        self.emulator = emulator
        layout = QVBoxLayout(self)
        
        
        self.driver_card = SimpleCardWidget(self)
        drv_layout = QVBoxLayout(self.driver_card)
        drv_layout.setContentsMargins(15, 15, 15, 15)
        
    
        self.drv_interception_layout = QHBoxLayout()
        self.drv_interception_label = SubtitleLabel("Interception (Key Hooker): Checking...", self.driver_card)
        self.drv_interception_btn = PushButton("Install Interception")
        self.drv_interception_btn.clicked.connect(lambda: self.install_driver('interception'))
        self.drv_interception_btn.hide()
        self.drv_interception_layout.addWidget(self.drv_interception_label)
        self.drv_interception_layout.addStretch(1)
        self.drv_interception_layout.addWidget(self.drv_interception_btn)
        drv_layout.addLayout(self.drv_interception_layout)
     
        self.drv_vigem_layout = QHBoxLayout()
        self.drv_vigem_label = SubtitleLabel("ViGEmBus (Gamepad Emulator): Checking...", self.driver_card)
        self.drv_vigem_btn = PushButton("Install ViGEmBus")
        self.drv_vigem_btn.clicked.connect(lambda: self.install_driver('vigem'))
        self.drv_vigem_btn.hide()
        self.drv_vigem_layout.addWidget(self.drv_vigem_label)
        self.drv_vigem_layout.addStretch(1)
        self.drv_vigem_layout.addWidget(self.drv_vigem_btn)
        drv_layout.addLayout(self.drv_vigem_layout)
        
      
        self.drv_hidhide_layout = QHBoxLayout()
        self.drv_hidhide_label = SubtitleLabel("HidHide (Hide Keyboard): Checking...", self.driver_card)
        self.drv_hidhide_btn = PushButton("Install HidHide")
        self.drv_hidhide_btn.clicked.connect(lambda: self.install_driver('hidhide'))
        self.drv_hidhide_btn.hide()
        self.drv_hidhide_layout.addWidget(self.drv_hidhide_label)
        self.drv_hidhide_layout.addStretch(1)
        self.drv_hidhide_layout.addWidget(self.drv_hidhide_btn)
        drv_layout.addLayout(self.drv_hidhide_layout)

        layout.addWidget(self.driver_card)
        
        
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        scroll.viewport().setStyleSheet("background-color: transparent;")
        
        guide_widget = QWidget()
        guide_widget.setObjectName("guideWidget")
        guide_widget.setStyleSheet("QWidget#guideWidget { background: transparent; }")
        guide_layout = QVBoxLayout(guide_widget)
        guide_layout.setContentsMargins(15, 15, 15, 15)
        guide_layout.setSpacing(15)
        
        title = SubtitleLabel("How to use the app?", guide_widget)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        guide_layout.addWidget(title)
        
        def add_guide_text(title_text, body_text):
            t = SubtitleLabel(title_text, guide_widget)
            b = BodyLabel(body_text, guide_widget)
            b.setWordWrap(True)
            b.setStyleSheet("margin-top: 5px; margin-bottom: 15px; color: #d0d0d0;")
            
            guide_layout.addWidget(t)
            guide_layout.addWidget(b)

        add_guide_text(
            "Welcome to LuminkeyAnalogInput!",
            "This app turns your keyboard into a full analog gamepad (Xbox 360 controller). "
            "Thanks to magnetic switches (Hall Effect), the program can read the exact actuation depth of each key "
            "and send it to games as smooth stick movements or trigger pulls."
        )
        
        add_guide_text(
            "Step 1: Driver Installation (Interception)",
            "For the program to intercept key presses before Windows handles them, "
            "you need a kernel-level driver. If you see warnings above, "
            "press the 'Install' button, wait for it to finish, and REBOOT your computer!"
        )
        
        add_guide_text(
            "Step 2: Key Binding",
            "Go to the 'Axes' and 'Buttons' tabs. There you can bind any physical key to the required "
            "game action. Click the bind button and press a physical key."
        )
        
        add_guide_text(
            "Step 3: Deadzones and Curves",
            "Every keyboard has some key travel tolerance. You can adjust the starting deadzone "
            "to ignore accidental presses, and the ending deadzone to reach 100% actuation before bottoming out.\n"
            "You can also choose a response curve (Linear, Exponential, Logarithmic) to adjust sensitivity."
        )
        
        add_guide_text(
            "Step 4: Gamepad Mode",
            "By default, when you press a bound key, a game might see a standard keystroke and conflict. "
            "Go to 'Settings' and enable 'Gamepad Mode'. This will hide bound keys from Windows! "
            "They will function ONLY as gamepad inputs."
        )
        
        guide_layout.addStretch(1)
        scroll.setWidget(guide_widget)
        
        layout.addWidget(scroll, 1) # stretch
        
        self.check_driver()

    def check_driver(self):
        
        if driver_manager.is_driver_installed():
            self.drv_interception_label.setText("Interception: INSTALLED & RUNNING")
            self.drv_interception_label.setStyleSheet("color: #00ff00;")
            self.drv_interception_btn.hide()
        else:
            self.drv_interception_label.setText("Interception: NOT INSTALLED")
            self.drv_interception_label.setStyleSheet("color: #ff0000;")
            self.drv_interception_btn.show()

     
        if driver_manager.is_vigem_installed():
            self.drv_vigem_label.setText("ViGEmBus: INSTALLED & RUNNING")
            self.drv_vigem_label.setStyleSheet("color: #00ff00;")
            self.drv_vigem_btn.hide()
        else:
            self.drv_vigem_label.setText("ViGEmBus: NOT INSTALLED")
            self.drv_vigem_label.setStyleSheet("color: #ff0000;")
            self.drv_vigem_btn.show()

        
        if driver_manager.is_hidhide_installed():
            self.drv_hidhide_label.setText("HidHide: INSTALLED & RUNNING")
            self.drv_hidhide_label.setStyleSheet("color: #00ff00;")
            self.drv_hidhide_btn.hide()
        else:
            self.drv_hidhide_label.setText("HidHide: NOT INSTALLED")
            self.drv_hidhide_label.setStyleSheet("color: #ff0000;")
            self.drv_hidhide_btn.show()

    def install_driver(self, driver_type):
        if driver_type == 'interception':
            btn = self.drv_interception_btn
            install_func = driver_manager.download_and_install_driver
            name = "Interception"
        elif driver_type == 'vigem':
            btn = self.drv_vigem_btn
            install_func = driver_manager.download_and_install_vigem
            name = "ViGEmBus"
        elif driver_type == 'hidhide':
            btn = self.drv_hidhide_btn
            install_func = driver_manager.download_and_install_hidhide
            name = "HidHide"
            
        btn.setText("Downloading and installing...")
        btn.setEnabled(False)
        QApplication.processEvents()
        
        success = install_func()
        
        if success:
            QMessageBox.information(self, "Success", f"Драйвер {name} installed successfully! Please REBOOT your PC.")
        else:
            QMessageBox.critical(self, "Error", f"Failed to install {name}. Try running as Administrator.")
            btn.setText(f"Install {name}")
            btn.setEnabled(True)
            
        self.check_driver()

    def update_ui(self):
        pass

class AxesPage(ScrollArea):
    def __init__(self, emulator, main_window, parent=None):
        super().__init__(parent)
        self.setObjectName("AxesPage")
        self.emulator = emulator
        
        view = QWidget()
        self.vbox = QVBoxLayout(view)
        
        self.cards = []
        axes_defs = [
            ('RT', 'Right Trigger (RT)'),
            ('LT', 'Left Trigger (LT)'),
            ('LX_NEG', 'Left Stick Left (X-)'),
            ('LX_POS', 'Left Stick Right (X+)'),
            ('LY_NEG', 'Left Stick Down (Y-)'),
            ('LY_POS', 'Left Stick Up (Y+)'),
            ('RX_NEG', 'Right Stick Left (X-)'),
            ('RX_POS', 'Right Stick Right (X+)'),
            ('RY_NEG', 'Right Stick Down (Y-)'),
            ('RY_POS', 'Right Stick Up (Y+)'),
        ]
        
        for aid, title in axes_defs:
            c = AxisCard(aid, title, self.emulator, main_window)
            self.vbox.addWidget(c)
            self.cards.append(c)
            
        self.setWidget(view)
        self.setWidgetResizable(True)

    def update_ui(self):
        for c in self.cards:
            c.update_ui()

class ButtonsPage(ScrollArea):
    def __init__(self, emulator, main_window, parent=None):
        super().__init__(parent)
        self.setObjectName("ButtonsPage")
        self.emulator = emulator
        
        view = QWidget()
        self.vbox = QVBoxLayout(view)
        
        self.cards = []
        for btn_id in self.emulator.config['buttons'].keys():
            c = ButtonCard(btn_id, f"Button {btn_id}", self.emulator, main_window)
            self.vbox.addWidget(c)
            self.cards.append(c)
            
        self.setWidget(view)
        self.setWidgetResizable(True)

    def update_ui(self):
        for c in self.cards:
            c.update_ui()

class SettingsPage(QWidget):
    def __init__(self, emulator, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPage")
        self.emulator = emulator
        
        layout = QVBoxLayout(self)
        
        title = SubtitleLabel("Global Settings", self)
        layout.addWidget(title)
        
        block_lbl = BodyLabel("Gamepad Mode (Hide bound keys from Windows/Games):", self)
        layout.addWidget(block_lbl)
        
        self.block_switch = SwitchButton("Enabled" if self.emulator.config.get('block_keys', False) else "Disabled", self)
        self.block_switch.setChecked(self.emulator.config.get('block_keys', False))
        self.block_switch.checkedChanged.connect(self.on_block_changed)
        layout.addWidget(self.block_switch)
        
        dist_lbl = BodyLabel("Max travel distance (hundredths of mm):", self)
        layout.addWidget(dist_lbl)
        
        self.dist_spin = SpinBox(self)
        self.dist_spin.setRange(100, 500)
        self.dist_spin.setValue(int(self.emulator.config.get('max_distance', 350.0)))
        self.dist_spin.valueChanged.connect(self.on_dist_changed)
        layout.addWidget(self.dist_spin)
        
        poll_lbl = BodyLabel("Polling rate (ms):", self)
        layout.addWidget(poll_lbl)
        
        self.poll_spin = SpinBox(self)
        self.poll_spin.setRange(1, 20)
        self.poll_spin.setValue(int(self.emulator.config.get('polling_rate_ms', 5)))
        self.poll_spin.valueChanged.connect(self.on_poll_changed)
        layout.addWidget(self.poll_spin)
        
        layout.addStretch(1)

    def on_dist_changed(self, val):
        self.emulator.config['max_distance'] = float(val)
        self.emulator.reader.max_distance = float(val)
        self.emulator.save_config()
        
    def on_poll_changed(self, val):
        self.emulator.config['polling_rate_ms'] = val
        self.emulator.save_config()
        
    def on_block_changed(self, checked):
        self.emulator.config['block_keys'] = checked
        self.block_switch.setText("Enabled" if checked else "Disabled")
        self.emulator.update_blocks()
        self.emulator.save_config()

    def update_ui(self):
        pass

class MainWindow(FluentWindow):
    key_bound_signal = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        setTheme(Theme.DARK)
        self.setWindowTitle("LuminkeyAnalogInput")
        self.setWindowIcon(QIcon(resource_path("app_icon.png")))
        self.resize(1000, 700)
        
        self.active_card = None
        self.key_bound_signal.connect(self.on_key_bound)
        
        self.reader = KeyboardReader()
        self.emulator = GamepadEmulator(self.reader)
        
        try:
            self.reader.start()
            self.emulator.start()
        except Exception as e:
            print("Error запуска:", e)
            
        self.dashboard_interface = DashboardPage(self.emulator, self)
        self.axes_interface = AxesPage(self.emulator, self, self)
        self.buttons_interface = ButtonsPage(self.emulator, self, self)
        self.settings_interface = SettingsPage(self.emulator, self)
        
        self.addSubInterface(self.dashboard_interface, FIF.HOME, "Dashboard", NavigationItemPosition.TOP)
        self.addSubInterface(self.axes_interface, FIF.GAME, "Axes", NavigationItemPosition.TOP)
        self.addSubInterface(self.buttons_interface, FIF.TILES, "Buttons", NavigationItemPosition.TOP)
        self.addSubInterface(self.settings_interface, FIF.SETTING, "Settings", NavigationItemPosition.BOTTOM)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(int(self.emulator.config.get('polling_rate_ms', 5)))
        
    def start_listening(self, card):
        self.active_card = card
        self.reader.set_listen_callback(self.key_bound_signal.emit)

    def on_key_bound(self, keycode):
        if self.active_card:
            self.active_card.finish_binding(keycode)
            self.active_card = None

    def update_ui(self):
        if self.stackedWidget.currentWidget() == self.dashboard_interface:
            self.dashboard_interface.update_ui()
        elif self.stackedWidget.currentWidget() == self.axes_interface:
            self.axes_interface.update_ui()
        elif self.stackedWidget.currentWidget() == self.buttons_interface:
            self.buttons_interface.update_ui()

    def closeEvent(self, event):
        self.emulator.stop()
        self.reader.stop()
        super().closeEvent(event)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def excepthook(exc_type, exc_value, exc_tb):
    import traceback
    with open("crash.log", "w", encoding="utf-8") as f:
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = excepthook

if __name__ == '__main__':
    if not is_admin():
        script_path = os.path.abspath(sys.argv[0])
        args = [f'"{script_path}"'] + sys.argv[1:]
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(args), None, 1)
        sys.exit()

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
