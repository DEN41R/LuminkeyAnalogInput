# LuminkeyAnalogInput

LuminkeyAnalogInput is an open-source tool that transforms your magnetic switch (Hall Effect) keyboard into a fully functional analog gamepad (Xbox 360 controller) on Windows.

It reads the raw, continuous actuation depth of your keypresses and maps them directly to gamepad axes (like analog sticks or triggers). This allows you to smoothly steer cars, precisely control character movement speed, or gradually apply throttle and brake in games using just your keyboard!

## Features

- **Full Analog Control**: Maps the depth of your keypresses directly to gamepad axes.
- **Customizable Response Curves**: Choose between Linear, Exponential, or Logarithmic curves for steering, throttle, or camera controls.
- **Adjustable Deadzones**: Configure starting and ending deadzones to filter out resting fingers and adjust bottom-out behavior.
- **Gamepad Mode**: Automatically hides your bound keys from Windows so games only register the Gamepad inputs, preventing conflicting keyboard/controller switching in-game.
- **Easy Setup**: Built-in 1-click dependency installer via Windows Package Manager (winget).


## Requirements

The application requires three dependencies to function perfectly. The built-in dashboard will automatically detect missing dependencies and provide an install button for each:

1. **Interception**: A kernel-level driver used to intercept keystrokes before Windows processes them (essential for Gamepad Mode).
2. **ViGEmBus**: A virtual gamepad emulation framework that allows Windows to recognize the fake Xbox 360 controller.
3. **HidHide**: A utility to completely hide your original physical keyboard inputs from games when Gamepad Mode is active.

## Installation

1. Download the latest `LuminkeyAnalogInput.exe` from the [Releases](https://github.com/DEN41R/LuminkeyAnalogInput/releases) page.
2. Run the executable.
3. On the **Dashboard**, check the Driver Status section. If any drivers are missing, click their **Install** buttons.
4. **Reboot your PC** after installing kernel-level drivers.

## Usage

1. Open **LuminkeyAnalogInput**.
2. Go to the **Axes** or **Buttons** tab.
3. Click "Button: None" next to the action you want to map (e.g., Right Trigger - Throttle).
4. Press the physical key on your keyboard.
5. Set your desired deadzones and response curves.
6. (Optional but Recommended) Go to **Settings** and enable **Gamepad Mode** to prevent your keyboard keys from interfering with the game.
7. Launch your game and enjoy analog control!

## Building from source

1. Clone the repository.
2. Install Python 3.10+
3. Install dependencies: `pip install PyQt6 qfluentwidgets vgamepad interception-python`
4. Run `python build.py` to create the standalone executable using PyInstaller.

## License

This project is open-source and available under the MIT License.
