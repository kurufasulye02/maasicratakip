# utils/updater.py - GitHub Üzerinden Otomatik Güncelleme Kontrolü

import urllib.request
import urllib.error
import json
import threading
import webbrowser
from tkinter import messagebox
import version as _v

# GitHub'daki version.json dosyasının RAW linki
# NOT: Linkin sonuna token eklense bile kod onu otomatik temizler.
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/kurufasulye02/maasicratakip/main/version.json"
DOWNLOAD_URL = "https://github.com/kurufasulye02/maasicratakip/releases/latest"


def check_for_updates(parent_window):
    """Arka planda GitHub'a bağlanıp sürüm kontrolü yapar."""
    
    def _check():
        # URL'de ?token= varsa kesip at (Temiz link kullan)
        url = GITHUB_VERSION_URL.split('?')[0]
        
        try:
            # Tarayıcı gibi davranmak için User-Agent ekliyoruz
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            latest_version = data.get("latest_version", "0.0.0")
            update_notes = data.get("update_notes", "Yeni özellikler ve hata düzeltmeleri.")
            download_url = data.get("download_url", DOWNLOAD_URL)

            # Mevcut versiyon ile GitHub'daki versiyonu karşılaştır
            if latest_version > _v.VERSION:
                parent_window.after(0, lambda: show_update_dialog(parent_window, latest_version, update_notes, download_url))
            else:
                print(f"Güncelleme Kontrolü: Sürümünüz güncel. (Mevcut: V.{_v.VERSION}, GitHub: V.{latest_version})")
                
        except urllib.error.HTTPError as e:
            print(f"Güncelleme kontrolü başarısız (HTTP {e.code}): URL'yi kontrol edin. Link: {url}")
        except Exception as e:
            print(f"Güncelleme kontrolü başarısız (İnternet yok veya başka bir hata): {e}")

    # Kontrolü arka planda başlat
    threading.Thread(target=_check, daemon=True).start()


def show_update_dialog(parent, latest_version, notes, download_url):
    """Yeni sürüm bulunduğunda kullanıcıya sorar."""
    msg = (f"Yeni bir sürüm mevcut!\n\n"
           f"Mevcut Sürümünüz: V.{_v.VERSION}\n"
           f"Yeni Sürüm: V.{latest_version}\n\n"
           f"Yenilikler:\n{notes}\n\n"
           f"İndirme sayfasına gitmek ister misiniz?")
           
    cevap = messagebox.askyesno("🚀 Güncelleme Mevcut", msg, parent=parent)
    
    if cevap:
        webbrowser.open(download_url)