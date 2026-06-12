import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://github.com/nefarius/HidHide/releases/download/v1.5.230/HidHide_1.5.230_x64.exe"
print("Downloading HidHide...")
try:
    urllib.request.urlretrieve(url, "HidHide_Installer.exe")
    print("Download complete!")
except Exception as e:
    print(f"Error downloading: {e}")
