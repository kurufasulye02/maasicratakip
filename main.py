# main.py - Program başlangıç noktası (V.3.1 - Görev Çubuğu İkon Düzeltmesi)

import ctypes
import sys
import tkinter as tk
from database import init_database
from gui.main_window import MainWindow
from utils.logger import setup_logging, install_global_exception_hook

# Windows Görev Çubuğunda kendi ikonumuzun görünmesi için Uygulama Kimliği (AppUserModelID) ataması
if sys.platform == "win32":
    try:
        myappid = 'meb.icranafaka.takip.v2' # Benzersiz bir kimlik
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

def main():
    setup_logging()
    install_global_exception_hook()
    
    # Veritabanını oluştur (ilk çalıştırmada)
    init_database()
    
    # Ana pencereyi başlat
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
