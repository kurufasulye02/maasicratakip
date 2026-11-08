# utils/maas_excel_export.py - Maaş Değişiklik Formu (V.3.0 - Kefalet Aidatı Eklendi)

import shutil
import os
import sys
import openpyxl
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime


def _sablon_dizini():
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'templates')


def maas_degisiklik_excel_olustur(kurum_bilgileri, veri_listesi, dosya_yolu):
    """MEB Maaş Değişiklik Bildirim Formu'nu şablonu kopyalayıp oluşturur.
    V.2.1: W sütununa Kefalet Aidatı eklendi."""

    template_dir = _sablon_dizini()
    template_path = os.path.join(template_dir, 'MAAŞ_BİLGİ_FORMU_SABLON.xlsx')

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Şablon dosyası bulunamadı: {template_path}")

    shutil.copy2(template_path, dosya_yolu)

    wb = openpyxl.load_workbook(dosya_yolu)
    ws = wb.active

    # Birleştirilmiş hücreleri kaydet ve geçici olarak kaldır
    merged_ranges = list(ws.merged_cells.ranges)
    for cr in merged_ranges:
        ws.unmerge_cells(str(cr))

    aylar_tr = {
        1: "OCAK", 2: "ŞUBAT", 3: "MART", 4: "NİSAN", 5: "MAYIS", 6: "HAZİRAN",
        7: "TEMMUZ", 8: "AĞUSTOS", 9: "EYLÜL", 10: "EKİM", 11: "KASIM", 12: "ARALIK"
    }

    donem_str = kurum_bilgileri.get('donem_ay_yil')
    if donem_str:
        try:
            yil, ay = map(int, donem_str.split('-'))
            ay_adi_tr = aylar_tr.get(ay, "BİLİNMİYOR")
            baslik_donem = f"{ay_adi_tr} {yil}"
        except (ValueError, IndexError):
            simdi = datetime.now()
            baslik_donem = f"{aylar_tr[simdi.month]} {simdi.year}"
    else:
        simdi = datetime.now()
        baslik_donem = f"{aylar_tr[simdi.month]} {simdi.year}"

    # --- KURUM BİLGİLERİ ---
    ws['E3'] = kurum_bilgileri.get('kurum_adi', '')
    ws['E4'] = kurum_bilgileri.get('saymanlik_kod', '')
    ws['E5'] = kurum_bilgileri.get('vergi_no', '')
    ws['E6'] = kurum_bilgileri.get('banka_subesi', '')
    ws['E7'] = kurum_bilgileri.get('iban', '')
    ws['E8'] = kurum_bilgileri.get('amir_adi', '')
    ws['E9'] = kurum_bilgileri.get('amir_telefon', '')

    # --- SAĞ TARAFTAKİ BİRLEŞMİŞ HÜCRELERE VERİLER ---
    ws['T3'] = baslik_donem
    ws['T4'] = kurum_bilgileri.get('toplam_personel_sayisi', 0)
    ws['T5'] = kurum_bilgileri.get('ucretsiz_izinli_sayisi', 0)

    giren = sum(1 for v in veri_listesi if len(v) > 18 and v[18] == "X")
    cikan = sum(1 for v in veri_listesi if len(v) > 19 and v[19] == "X")
    ws['T6'] = giren
    ws['T7'] = cikan

    toplam_personel = kurum_bilgileri.get('toplam_personel_sayisi', 0)
    ucretsiz_izinli = kurum_bilgileri.get('ucretsiz_izinli_sayisi', 0)
    odeme_yapilan = toplam_personel - (ucretsiz_izinli + cikan) + giren
    if odeme_yapilan < 0:
        odeme_yapilan = 0
    ws['AA9'] = odeme_yapilan
    ws['AB2'] = datetime.now().strftime("%d.%m.%Y")

    # Önceki aylar
    onceki_aylar = kurum_bilgileri.get('onceki_aylar', [])
    for i, sayi in enumerate(onceki_aylar):
        if i < 12:
            col_letter = get_column_letter(20 + i)  # T → AE
            ws[f'{col_letter}9'] = sayi

    # --- VERİ SATIRLARI (14. SATIRDAN İTİBAREN) ---
    # Sıra: 0:id, 1:saymanlik, 2:ad_soyad, 3:tc, 4:banka, 5:eski_der, 6:eski_kad, 
    # 7:yeni_der, 8:yeni_kad, 9:terfi, 10:aile, 11:c0_6, 12:c6u, 13:uzman, 14:bas, 
    # 15:rapor, 16:emekli, 17:sendika, 18:n_geldi, 19:n_gitti, 20:u_dondu, 21:u_cikti, 
    # 22:kesinti, 23:saglik_sigorta, 24:kefalet

    baslangic_satir = 14
    for idx, values in enumerate(veri_listesi):
        satir = baslangic_satir + idx

        ws[f'A{satir}'] = values[0]    # Sıra No
        ws[f'B{satir}'] = values[1]    # Saymanlık No
        ws[f'D{satir}'] = values[2]    # Ad Soyad
        ws[f'E{satir}'] = values[3]    # TC
        ws[f'F{satir}'] = values[4]    # Banka Hesap

        ws[f'G{satir}'] = values[5]    # Eski Der.
        ws[f'H{satir}'] = values[6]    # Eski Kad.
        ws[f'I{satir}'] = values[7]    # Yeni Der.
        ws[f'J{satir}'] = values[8]    # Yeni Kad.
        ws[f'K{satir}'] = values[9]    # Terfi Tarihi

        ws[f'M{satir}'] = values[10]   # Aile Yardımı
        ws[f'N{satir}'] = values[11]   # Çocuk 0-6
        ws[f'O{satir}'] = values[12]   # Çocuk 6+

        ws[f'P{satir}'] = values[13]   # Uzman
        ws[f'Q{satir}'] = values[14]   # Baş Öğrt
        ws[f'R{satir}'] = values[15]   # Raporlu

        ws[f'S{satir}'] = values[18]   # Naklen Geldi
        ws[f'T{satir}'] = values[19]   # Naklen Gitti
        ws[f'U{satir}'] = values[23] if len(values) > 23 else ""  # Sağlık/Hayat Sigortası

        # V ve W AYRI sütunlar (V: Kesinti, W: Kefalet)
        ws[f'V{satir}'] = values[22]   # Kesinti (Haciz/Nafaka)
        ws[f'W{satir}'] = values[24] if len(values) > 24 else ""  # Kefalet Aidatı (Giriş)

        # X:Y, Z:AA, AB:AC, AD:AE birleşik - sol sütuna yaz
        ws[f'X{satir}'] = values[20]   # Ücr. Döndü (X:Y birleşik)
        ws[f'Z{satir}'] = values[21]   # Ücr. Çıktı (Z:AA birleşik)
        ws[f'AB{satir}'] = values[16]  # Emekli (AB:AC birleşik)
        ws[f'AD{satir}'] = values[17]  # Sendika (AD:AE birleşik)

    # Birleştirmeleri geri getir
    for cr in merged_ranges:
        ws.merge_cells(str(cr))

    # Müdür ismi
    if kurum_bilgileri.get('amir_adi'):
        ws['Y33'] = kurum_bilgileri.get('amir_adi')
        ws['Y33'].font = Font(name='Times New Roman', size=16, bold=True)
        ws['Y33'].alignment = Alignment(horizontal='center')
        
        ws['Y34'] = "Müdür"
        ws['Y34'].font = Font(name='Times New Roman', size=14, bold=True)
        ws['Y34'].alignment = Alignment(horizontal='center')

    wb.save(dosya_yolu)
    return dosya_yolu