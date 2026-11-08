# utils/backup.py - Veritabanı yedekleme yardımcı fonksiyonları

import os
import sys
import shutil
from datetime import datetime

from database import DB_PATH, BASE_DIR

BACKUP_DIR = os.path.join(BASE_DIR, 'yedekler')
MAX_YEDEK_SAYISI = 30  # Bu sayıdan fazla yedek birikirse en eskiler silinir (disk taşmasın diye).


def yedek_al():
    """data/icra.db dosyasının bir kopyasını, zaman damgalı olarak
    'yedekler' klasörüne alır. Başarılıysa oluşturulan dosyanın yolunu döner,
    veritabanı dosyası henüz yoksa (ilk açılış, hiç işlem yapılmamış) None döner."""
    if not os.path.exists(DB_PATH):
        return None

    os.makedirs(BACKUP_DIR, exist_ok=True)

    zaman_damgasi = datetime.now().strftime('%Y%m%d_%H%M%S')
    yedek_adi = f"icra_yedek_{zaman_damgasi}.db"
    yedek_yolu = os.path.join(BACKUP_DIR, yedek_adi)

    shutil.copy2(DB_PATH, yedek_yolu)

    _eski_yedekleri_temizle()

    return yedek_yolu


def yedekleri_listele():
    """'yedekler' klasöründeki tüm yedekleri, EN YENİ EN ÜSTTE olacak şekilde döner.
    Her eleman: (dosya_adi, tam_yol, tarih_saat_str, boyut_kb)"""
    if not os.path.isdir(BACKUP_DIR):
        return []

    sonuc = []
    for f in os.listdir(BACKUP_DIR):
        if f.startswith("icra_yedek_") and f.endswith(".db"):
            tam_yol = os.path.join(BACKUP_DIR, f)
            mtime = os.path.getmtime(tam_yol)
            tarih_str = datetime.fromtimestamp(mtime).strftime('%d.%m.%Y %H:%M:%S')
            boyut_kb = round(os.path.getsize(tam_yol) / 1024, 1)
            sonuc.append((f, tam_yol, tarih_str, boyut_kb, mtime))

    sonuc.sort(key=lambda x: x[4], reverse=True)  # en yeni en üstte
    return [(f, yol, tarih, boyut) for (f, yol, tarih, boyut, _mtime) in sonuc]


def yedekten_geri_yukle(yedek_yolu):
    """Seçilen yedek dosyasını mevcut veritabanının üzerine geri yükler.
    Güvenlik için, üzerine yazmadan HEMEN ÖNCE mevcut veritabanının da bir
    yedeğini alır (yanlışlıkla yanlış yedek seçilirse geri dönebilmek için)."""
    if not os.path.exists(yedek_yolu):
        raise FileNotFoundError(f"Seçilen yedek dosyası bulunamadı: {yedek_yolu}")

    # Geri yüklemeden hemen önceki durumu da kaybetmemek için otomatik güvenlik yedeği.
    if os.path.exists(DB_PATH):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        zaman_damgasi = datetime.now().strftime('%Y%m%d_%H%M%S')
        guvenlik_yedegi = os.path.join(BACKUP_DIR, f"icra_yedek_{zaman_damgasi}_GERIYUKLEME_ONCESI.db")
        shutil.copy2(DB_PATH, guvenlik_yedegi)

    shutil.copy2(yedek_yolu, DB_PATH)
    return True


def _eski_yedekleri_temizle():
    """Yedek sayısı MAX_YEDEK_SAYISI'nı aşarsa, en eski yedekleri siler."""
    try:
        if not os.path.isdir(BACKUP_DIR):
            return
        dosyalar = [
            os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR)
            if f.startswith("icra_yedek_") and f.endswith(".db")
        ]
        if len(dosyalar) <= MAX_YEDEK_SAYISI:
            return
        dosyalar.sort(key=os.path.getmtime)  # En eski önce
        fazla = len(dosyalar) - MAX_YEDEK_SAYISI
        for dosya in dosyalar[:fazla]:
            os.remove(dosya)
    except Exception:
        # Temizlik başarısız olsa bile yedekleme işlemini etkilemesin.
        pass
