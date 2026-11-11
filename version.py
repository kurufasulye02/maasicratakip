# version.py - Program versiyon bilgisi (V.3.2.0)

VERSION = "3.2.0"
VERSION_DATE = "2026-11-11"
VERSION_NOTLARI = "V.3.2.0 — Şablon uyumu, hata düzeltmeleri, tek versiyon kaynağı"

APP_NAME = "İCRA/NAFAKA/MAAŞ TAKİP PROGRAMI"
APP_SUBTITLE = "Milli Eğitim Bakanlığı Okul/Kurumları İçin"
APP_TITLE = f"{APP_NAME} - MEB - V.{VERSION}"

def get_display_version():
    return f"V.{VERSION}"

def get_title_with_version():
    return APP_TITLE

def get_about_text():
    return f"""{APP_NAME}
Versiyon: {VERSION}
Tarih: {VERSION_DATE}

{VERSION_NOTLARI}

✅ Maaştan haciz takibi
✅ Borç yönetimi
✅ Excel/PDF raporlama
✅ Çoklu kurum desteği
✅ Otomatik yedekleme
✅ Maaş değişiklik arşivi
✅ Sağlık/Hayat Sigortası İndirimi desteği
✅ GitHub desteği ile otomatik güncelleme
"""