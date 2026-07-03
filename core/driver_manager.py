import os
import urllib.request
import zipfile
import tempfile
import ctypes
import sys
import subprocess

def is_driver_installed():
    try:
        from interception.interception import Interception
        import interception.exceptions
        ctx = Interception()
        try:
            ctx.get_handles()
            return True
        except interception.exceptions.DriverNotFoundError:
            return False
        except Exception:
           
            return True
        finally:
            ctx.destroy()
    except Exception:
        return False

def download_and_install_driver():
   
    try:
        url = "https://github.com/oblitum/Interception/releases/download/v1.0.1/Interception.zip"
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "Interception.zip")
        
   
        urllib.request.urlretrieve(url, zip_path)
        

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        installer_path = os.path.join(temp_dir, "Interception", "command line installer", "install-interception.exe")
        
        if not os.path.exists(installer_path):
            raise Exception("Installer not found inside the downloaded archive.")
        
        ps_cmd = f"Start-Process '{installer_path}' -ArgumentList '/install' -Wait -Verb RunAs"
        res = subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
        
        return res.returncode == 0
    except Exception as e:
        print(f"Driver install error: {e}")
        return False

def is_vigem_installed():
    try:
        import vgamepad as vg
        vg.VX360Gamepad()
        return True
    except Exception:
        return False

def download_and_install_vigem():
  
    try:
        ps_cmd = "Start-Process 'winget' -ArgumentList 'install -e --id ViGEm.ViGEmBus --accept-source-agreements --accept-package-agreements --silent' -Wait -Verb RunAs"
        res = subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
        
        return res.returncode == 0
    except Exception as e:
        print(f"ViGEmBus install error: {e}")
        return False

def is_hidhide_installed():
    return os.path.exists(r"C:\Program Files\Nefarius Software Solutions\HidHide")

def download_and_install_hidhide():
    
    try:
        ps_cmd = "Start-Process 'winget' -ArgumentList 'install -e --id Nefarius.HidHide --accept-source-agreements --accept-package-agreements --silent' -Wait -Verb RunAs"
        res = subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
        
        return res.returncode == 0
    except Exception as e:
        print(f"HidHide install error: {e}")
        return False

