# utils/logger.py - Hata loglama ve raporlama sistemi

import logging
import os
import sys
import traceback
import shutil
from datetime import datetime

# EXE-GÜVENLİ YOL: exe'ye paketlendiğinde (sys.frozen), normal .py modüllerinin
# __file__ konumu güvenilir değildir. database.py'deki mantıkla tutarlı olarak,
# exe'nin yanındaki klasör esas alınır (onefile'da geçici klasöre değil).
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_DIR = os.path.join(_BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'icra_program.log')
MAX_LOG_BYTES = 2 * 1024 * 1024  # 2 MB

_logger = None


def get_logger():
    """Uygulama geneli logger'ı döndürür (lazy init)."""
    global _logger
    if _logger is not None:
        return _logger

    os.makedirs(LOG_DIR, exist_ok=True)
    _logger = logging.getLogger('icra_program')
    _logger.setLevel(logging.DEBUG)

    if not _logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        _logger.addHandler(handler)

    return _logger


def _rotate_if_needed():
    """Log dosyası çok büyüdüyse yedekle ve sıfırla."""
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_BYTES:
        backup = LOG_FILE.replace('.log', f'_{datetime.now():%Y%m%d_%H%M%S}.log')
        shutil.move(LOG_FILE, backup)


def setup_logging():
    """Uygulama başlangıcında çağrılır."""
    _rotate_if_needed()
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("Program başlatıldı")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Çalışma dizini: {os.getcwd()}")
    return logger


def log_info(message):
    get_logger().info(message)


def log_warning(message):
    get_logger().warning(message)


def log_error(message, exc_info=False):
    get_logger().error(message, exc_info=exc_info)


def log_exception_context(message, exception):
    """GUI işlemlerindeki hataları kaydet."""
    get_logger().error(
        f"{message}: {exception}\n{traceback.format_exc()}"
    )


def install_global_exception_hook():
    """Yakalanmamış hataları logla ve kullanıcıya bildir."""

    def _hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        tb_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        get_logger().critical(f"Yakalanmamış hata:\n{tb_text}")

        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk._default_root
            if root and root.winfo_exists():
                messagebox.showerror(
                    "Beklenmeyen Hata",
                    f"Bir hata oluştu ve log dosyasına kaydedildi.\n\n"
                    f"Hata: {exc_value}\n\n"
                    f"Geliştiriciye iletmek için:\n"
                    f"Yardım → Hata Raporu Gönder menüsünü kullanın.",
                    parent=root
                )
        except Exception:
            pass

    sys.excepthook = _hook


def get_log_file_path():
    return LOG_FILE


def get_log_dir():
    return LOG_DIR


def read_recent_logs(max_lines=200):
    """Son log satırlarını oku."""
    if not os.path.exists(LOG_FILE):
        return "Henüz log kaydı yok."
    with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    return ''.join(lines[-max_lines:])


def export_log_to(dest_path):
    """Log dosyasını belirtilen konuma kopyala."""
    if not os.path.exists(LOG_FILE):
        raise FileNotFoundError("Log dosyası bulunamadı.")
    shutil.copy2(LOG_FILE, dest_path)


def show_error_report_dialog(parent=None):
    """Kullanıcıya log görüntüleme ve dışa aktarma penceresi aç."""
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    win = tk.Toplevel(parent)
    win.title("Hata Raporu Gönder")
    win.geometry("700x500")
    win.transient(parent)
    win.grab_set()

    tk.Label(
        win,
        text="Program hataları aşağıdaki log dosyasına kaydedilir.\n"
             "Bu dosyayı geliştiriciye e-posta veya mesajla gönderebilirsiniz.",
        font=("Segoe UI", 10),
        justify=tk.LEFT,
        wraplength=650
    ).pack(padx=15, pady=(15, 5), anchor="w")

    tk.Label(
        win,
        text=f"Log dosyası: {LOG_FILE}",
        font=("Segoe UI", 9),
        fg="gray"
    ).pack(padx=15, anchor="w")

    text_frame = ttk.Frame(win)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

    scrollbar = ttk.Scrollbar(text_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, font=("Consolas", 9))
    text.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=text.yview)

    text.insert(tk.END, read_recent_logs(300))
    text.config(state=tk.DISABLED)

    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=(0, 15))

    def _export():
        dest = filedialog.asksaveasfilename(
            parent=win,
            title="Log Dosyasını Kaydet",
            defaultextension=".log",
            initialfile=f"icra_hata_raporu_{datetime.now():%Y%m%d}.log",
            filetypes=[("Log dosyası", "*.log"), ("Metin dosyası", "*.txt"), ("Tüm dosyalar", "*.*")]
        )
        if dest:
            try:
                export_log_to(dest)
                messagebox.showinfo("Başarılı", f"Log dosyası kaydedildi:\n{dest}", parent=win)
            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarma hatası: {e}", parent=win)

    def _open_folder():
        try:
            os.startfile(LOG_DIR)
        except Exception as e:
            messagebox.showerror("Hata", f"Klasör açılamadı: {e}", parent=win)

    tk.Button(btn_frame, text="📁 Log Klasörünü Aç", command=_open_folder,
              font=("Segoe UI", 10), padx=10).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="💾 Dosyayı Kaydet / Gönder", command=_export,
              font=("Segoe UI", 10, "bold"), padx=10).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Kapat", command=win.destroy,
              font=("Segoe UI", 10), padx=10).pack(side=tk.LEFT, padx=5)
