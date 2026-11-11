# utils/helpers.py - Yardımcı fonksiyonlar (V.3.2.0)

from datetime import datetime
from utils.kurum_context import KurumContext

def format_tl(tutar):
    if tutar is None:
        tutar = 0.0
    return f"{tutar:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")

_TR_ALFABE = "AaBbCcÇçDdEeFfGgĞğHhIıİiJjKkLlMmNnOoÖöPpRrSsŞşTtUuÜüVvYyZz"
_TR_SIRA = {ch: i for i, ch in enumerate(_TR_ALFABE)}

def turkce_sirala_anahtari(metin):
    if not metin:
        return ()
    return tuple(_TR_SIRA.get(ch, 1000 + ord(ch)) for ch in metin)

def format_float(deger):
    try:
        return float(deger.replace(",", ".").replace(" ", ""))
    except (ValueError, AttributeError):
        return 0.0

def get_current_ay_yil():
    return datetime.now().strftime("%Y-%m")

def get_aylar(onceki_yil=2, sonraki_yil=2):
    simdi = datetime.now()
    baslangic = simdi.year - onceki_yil
    bitis = simdi.year + sonraki_yil
    aylar = []
    for yil in range(baslangic, bitis + 1):
        for ay in range(1, 13):
            aylar.append(f"{yil}-{ay:02d}")
    return aylar

def parse_float(deger):
    if deger is None:
        return None
    if isinstance(deger, (int, float)):
        return float(deger)
    deger = str(deger).strip()
    if not deger:
        return None
    deger = deger.replace(" ", "")
    if "." in deger and "," in deger:
        if deger.rfind(",") > deger.rfind("."):
            deger = deger.replace(".", "").replace(",", ".")
        else:
            deger = deger.replace(",", "")
    elif "," in deger:
        deger = deger.replace(",", ".")
    try:
        return float(deger)
    except ValueError:
        return None

def parse_id_from_secim(secim):
    if not secim or "ID:" not in secim:
        return None
    try:
        return int(secim.split("ID:")[1].replace(")", "").strip())
    except (ValueError, IndexError):
        return None

def personel_listesi_yukle(combobox, kurum_id=None, sadece_borclu=False):
    from utils.db_repo import get_personel_list
    if kurum_id is None:
        kurum_id = KurumContext.get_active_id()
    
    # sadece_borclu parametresi eklendi
    personeller = get_personel_list(kurum_id=kurum_id, sadece_borclu=sadece_borclu)
    combobox['values'] = [f"{p[1]} (ID:{p[0]})" for p in personeller]
    if personeller:
        combobox.set(combobox['values'][0])
    else:
        combobox.set("")
    return personeller