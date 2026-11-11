# gui/kesinti.py - Kesinti işlemleri (V.3.2.0)

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import db_connection
from utils.base_page import BasePage
from utils.helpers import parse_float, parse_id_from_secim, personel_listesi_yukle, get_aylar, format_tl
from utils.kurum_context import KurumContext
from utils.logger import log_warning, log_exception_context
from gui.maas_degisiklik import MAAS_DEGISIKLIK_KOLONLARI, TC_NO_INDEX, KESINTI_INDEX


class KesintiIslemleri(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.kurum_id = KurumContext.get_active_id()
        self.selected_personel_id = None
        self.selected_borc_id = None
        self.selected_maas_id = None
        self.selected_kesinti_id = None
        self.selected_borc_turu = 'icra'
        self.selected_nafaka_tutari = 0.0
        
        self.onceki_kalan_float = 0.0
        self.hesaplanan_float = 0.0
        
        self._uyari_gosterildi = set()
        self.create_widgets()
        self.load_personel_list()
        self.apply_theme(self.theme)

    def create_widgets(self):
        theme = self.theme

        self.frame = tk.Frame(self.parent, bg=theme['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title = tk.Label(self.frame, text="✏️ KESİNTİ İŞLEMLERİ",
                         font=("Arial", 16, "bold"), fg="blue", bg=theme['bg'])
        title.grid(row=0, column=0, columnspan=5, pady=10)

        tk.Label(self.frame, text="Personel Seçin:*", font=("Arial", 10), bg=theme['bg']).grid(row=1, column=0, sticky="w", pady=5)
        self.personel_combobox = ttk.Combobox(self.frame, width=35)
        self.personel_combobox.grid(row=1, column=1, pady=5, sticky="w")
        self.personel_combobox.bind("<<ComboboxSelected>>", self.personel_sec)

        tk.Label(self.frame, text="Ay/Yıl:*", font=("Arial", 10), bg=theme['bg']).grid(row=1, column=2, sticky="w", pady=5)
        self.ay_combobox = ttk.Combobox(self.frame, width=15)
        self.ay_combobox.grid(row=1, column=3, pady=5, sticky="w")
        self.ay_combobox['values'] = get_aylar()
        self.ay_combobox.set(datetime.now().strftime("%Y-%m"))
        self.ay_combobox.bind("<<ComboboxSelected>>", self.ay_sec)

        tk.Label(self.frame, text="Borç Seçin:*", font=("Arial", 10), bg=theme['bg']).grid(row=2, column=0, sticky="w", pady=5)
        self.borc_combobox = ttk.Combobox(self.frame, width=35)
        self.borc_combobox.grid(row=2, column=1, pady=5, sticky="w")
        self.borc_combobox.bind("<<ComboboxSelected>>", self.borc_sec)

        tk.Label(self.frame, text="Maaş Kaydı Seçin:*", font=("Arial", 10), bg=theme['bg']).grid(row=2, column=2, sticky="w", pady=5)
        self.maas_combobox = ttk.Combobox(self.frame, width=30)
        self.maas_combobox.grid(row=2, column=3, pady=5, sticky="w")
        self.maas_combobox.bind("<<ComboboxSelected>>", self.maas_sec)

        maas_frame = ttk.LabelFrame(self.frame, text="📊 Maaş Bilgileri", padding=10)
        maas_frame.grid(row=3, column=0, columnspan=5, pady=10, sticky="ew")

        tk.Label(maas_frame, text="Aylık Tutar:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.lbl_aylik_tutar = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_aylik_tutar.grid(row=0, column=1, sticky="w", pady=2, padx=10)

        tk.Label(maas_frame, text="Taban Aylık:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=2)
        self.lbl_taban = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_taban.grid(row=1, column=1, sticky="w", pady=2, padx=10)

        tk.Label(maas_frame, text="Ek Gösterge:", font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=2)
        self.lbl_ek_gosterge = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_ek_gosterge.grid(row=2, column=1, sticky="w", pady=2, padx=10)

        tk.Label(maas_frame, text="Yan Ödeme:", font=("Arial", 9)).grid(row=3, column=0, sticky="w", pady=2)
        self.lbl_yan_odeme = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_yan_odeme.grid(row=3, column=1, sticky="w", pady=2, padx=10)

        tk.Label(maas_frame, text="Kıdem Aylık:", font=("Arial", 9)).grid(row=4, column=0, sticky="w", pady=2)
        self.lbl_kidem = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_kidem.grid(row=4, column=1, sticky="w", pady=2, padx=10)

        tk.Label(maas_frame, text="Özel Hizmet:", font=("Arial", 9)).grid(row=0, column=2, sticky="w", pady=2)
        self.lbl_ozel_hizmet = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_ozel_hizmet.grid(row=0, column=3, sticky="w", pady=2, padx=10)

        tk.Label(maas_frame, text="Makam:", font=("Arial", 9)).grid(row=1, column=2, sticky="w", pady=2)
        self.lbl_makam = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_makam.grid(row=1, column=3, sticky="w", pady=2, padx=10)

        tk.Label(maas_frame, text="Dil Tazminatı:", font=("Arial", 9)).grid(row=2, column=2, sticky="w", pady=2)
        self.lbl_dil = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_dil.grid(row=2, column=3, sticky="w", pady=2, padx=10)

        tk.Label(maas_frame, text="Ek Ödeme 666:", font=("Arial", 9)).grid(row=3, column=2, sticky="w", pady=2)
        self.lbl_ek_odeme = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_ek_odeme.grid(row=3, column=3, sticky="w", pady=2, padx=10)

        tk.Label(maas_frame, text="Ek Tazminat:", font=("Arial", 9)).grid(row=4, column=2, sticky="w", pady=2)
        self.lbl_ek_tazminat = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_ek_tazminat.grid(row=4, column=3, sticky="w", pady=2, padx=10)

        tk.Label(maas_frame, text="İlave Ödeme:", font=("Arial", 9)).grid(row=5, column=2, sticky="w", pady=2)
        self.lbl_ilave_odeme = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="blue")
        self.lbl_ilave_odeme.grid(row=5, column=3, sticky="w", pady=2, padx=10)

        tk.Label(maas_frame, text="TOPLAM MAAŞ:", font=("Arial", 10, "bold")).grid(row=6, column=0, sticky="w", pady=5)
        self.lbl_toplam = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 10, "bold"), fg="green")
        self.lbl_toplam.grid(row=6, column=1, sticky="w", pady=5, padx=10)

        self.lbl_hesaplanan_baslik = tk.Label(maas_frame, text="ÖN HESAPLAMA (1/4):", font=("Arial", 10, "bold"))
        self.lbl_hesaplanan_baslik.grid(row=6, column=2, sticky="w", pady=5)
        self.lbl_hesaplanan = tk.Label(maas_frame, text="0.00 TL", font=("Arial", 10, "bold"), fg="orange")
        self.lbl_hesaplanan.grid(row=6, column=3, sticky="w", pady=5, padx=10)

        borc_frame = ttk.LabelFrame(self.frame, text="📄 Borç Bilgileri", padding=10)
        borc_frame.grid(row=4, column=0, columnspan=5, pady=10, sticky="ew")

        tk.Label(borc_frame, text="İcra Dairesi:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.lbl_daire = tk.Label(borc_frame, text="-", font=("Arial", 9, "bold"))
        self.lbl_daire.grid(row=0, column=1, sticky="w", pady=2, padx=10)

        tk.Label(borc_frame, text="Dosya No:", font=("Arial", 9)).grid(row=0, column=2, sticky="w", pady=2)
        self.lbl_dosya = tk.Label(borc_frame, text="-", font=("Arial", 9, "bold"))
        self.lbl_dosya.grid(row=0, column=3, sticky="w", pady=2, padx=10)

        tk.Label(borc_frame, text="Daha Önce Yapılan Kesinti:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=2)
        self.lbl_onceki_kesinti = tk.Label(borc_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="green")
        self.lbl_onceki_kesinti.grid(row=1, column=1, sticky="w", pady=2, padx=10)

        tk.Label(borc_frame, text="Önceki Kalan Borç:", font=("Arial", 9)).grid(row=1, column=2, sticky="w", pady=2)
        self.lbl_onceki_kalan = tk.Label(borc_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="red")
        self.lbl_onceki_kalan.grid(row=1, column=3, sticky="w", pady=2, padx=10)

        tk.Label(borc_frame, text="Toplam Borç:", font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=2)
        self.lbl_toplam_borc = tk.Label(borc_frame, text="0.00 TL", font=("Arial", 9, "bold"), fg="red")
        self.lbl_toplam_borc.grid(row=2, column=1, sticky="w", pady=2, padx=10)

        kesinti_frame = ttk.LabelFrame(self.frame, text="✏️ Kesinti Girişi", padding=10)
        kesinti_frame.grid(row=5, column=0, columnspan=5, pady=10, sticky="ew")

        tk.Label(kesinti_frame, text="Kesilecek Tutar:*", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_kesinti = tk.Entry(kesinti_frame, width=20, font=("Arial", 12))
        self.entry_kesinti.grid(row=0, column=1, pady=5, padx=10)

        self.btn_hesapla = tk.Button(kesinti_frame, text="📊 Ön Hesaplamayı Getir", command=self.hesapla,
                                     font=("Arial", 9), bg="#2196F3", fg="white")
        self.btn_hesapla.grid(row=0, column=2, padx=10)

        tk.Label(kesinti_frame, text="Açıklama:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_aciklama = tk.Entry(kesinti_frame, width=50)
        self.entry_aciklama.grid(row=1, column=1, columnspan=2, pady=5, sticky="w")

        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=6, column=0, columnspan=5, pady=15)

        self.btn_kaydet = tk.Button(button_frame, text="💾 Kesinti Kaydet", command=self.kaydet,
                                    font=("Arial", 10), bg="#4CAF50", fg="white", width=15)
        self.btn_kaydet.pack(side=tk.LEFT, padx=5)

        self.btn_temizle = tk.Button(button_frame, text="🧹 Temizle", command=self.temizle,
                                     font=("Arial", 10), bg="#9E9E9E", fg="white", width=12)
        self.btn_temizle.pack(side=tk.LEFT, padx=5)

        self.btn_yenile = tk.Button(button_frame, text="🔄 Yenile", command=self.load_personel_list,
                                    font=("Arial", 10), bg="#FF9800", fg="white", width=12)
        self.btn_yenile.pack(side=tk.LEFT, padx=5)

        self.btn_gecmis = tk.Button(button_frame, text="📜 Kesinti Geçmişi", command=self.show_gecmis,
                                    font=("Arial", 10), bg="#9C27B0", fg="white", width=15)
        self.btn_gecmis.pack(side=tk.LEFT, padx=5)

    def load_personel_list(self):
        # Sadece borcu olan personelleri getir
        self.personel_listesi = personel_listesi_yukle(self.personel_combobox, sadece_borclu=True)
        if self.personel_listesi:
            self.personel_sec()
        else:
            self.borc_combobox.set("")
            self.borc_combobox['values'] = []
            self.selected_borc_id = None
            self.lbl_daire.config(text="-")
            self.lbl_dosya.config(text="-")
            self.lbl_toplam_borc.config(text=format_tl(0))
            self.lbl_onceki_kalan.config(text=format_tl(0))
            self.onceki_kalan_float = 0.0

    def personel_sec(self, event=None):
        secim = self.personel_combobox.get()
        self.selected_personel_id = parse_id_from_secim(secim)
        if self.selected_personel_id is None:
            if secim:
                messagebox.showerror("Hata", "Geçersiz personel seçimi!")
            return

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, icra_daire_adi, dosya_no, toplam_borc
                FROM borc WHERE personel_id = ? ORDER BY id ASC
            """, (self.selected_personel_id,))
            borclar = cursor.fetchall()

        self.borc_listesi = borclar
        self.borc_combobox['values'] = [f"{b[1]} - {b[2]} (ID:{b[0]})" for b in borclar]

        if borclar:
            self.borc_combobox.set(self.borc_combobox['values'][0])
            self.borc_sec()
        else:
            self.borc_combobox.set("")
            self.borc_combobox['values'] = []
            self.selected_borc_id = None
            self.selected_borc_turu = 'icra'
            self.selected_nafaka_tutari = 0.0
            self.lbl_daire.config(text="-")
            self.lbl_dosya.config(text="-")
            self.lbl_toplam_borc.config(text=format_tl(0))
            self.lbl_onceki_kalan.config(text=format_tl(0))
            self.onceki_kalan_float = 0.0
            return

        self.load_maas_list()

    # ... (Kalan kodlar aynı, load_maas_list, maas_sec, get_maas_bilgileri, borc_sec vb. değişmiyor)
    def load_maas_list(self):
        if not self.selected_personel_id:
            return

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, baslangic_ay, bitis_ay,
                       aylik_tutar + taban_aylik + ek_gosterge + yan_odeme + kidem + ozel_hizmet + 
                       makam + dil + ek_odeme_666 + ek_tazminat + ilave_odeme as toplam
                FROM maas_kalemleri
                WHERE personel_id = ?
                ORDER BY baslangic_ay DESC
            """, (self.selected_personel_id,))
            maaslar = cursor.fetchall()

        if maaslar:
            self.maas_listesi = maaslar
            self.maas_combobox['values'] = [
                f"{m[1]} - {m[2] or 'Aktif'} (Toplam: {m[3]:,.0f} TL)"
                for m in maaslar
            ]
            self.maas_combobox.set(self.maas_combobox['values'][0])
            self.selected_maas_id = maaslar[0][0]
            self.get_maas_bilgileri()
        else:
            self.maas_combobox['values'] = []
            self.maas_combobox.set("")
            messagebox.showwarning("Uyarı", "Bu personele ait maaş kaydı bulunamadı!")

    def maas_sec(self, event=None):
        secim = self.maas_combobox.get()
        if not secim:
            return
        for m in self.maas_listesi:
            if f"{m[1]} - {m[2] or 'Aktif'} (Toplam: {m[3]:,.0f} TL)" == secim:
                self.selected_maas_id = m[0]
                break
        self.get_maas_bilgileri()

    def get_maas_bilgileri(self):
        if not self.selected_maas_id:
            return

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT aylik_tutar, taban_aylik, ek_gosterge, yan_odeme, kidem, ozel_hizmet,
                       makam, dil, ek_odeme_666, ek_tazminat, ilave_odeme
                FROM maas_kalemleri WHERE id = ?
            """, (self.selected_maas_id,))
            row = cursor.fetchone()

        if row:
            vals = [r or 0 for r in row]
            self.lbl_aylik_tutar.config(text=format_tl(vals[0]))
            self.lbl_taban.config(text=format_tl(vals[1]))
            self.lbl_ek_gosterge.config(text=format_tl(vals[2]))
            self.lbl_yan_odeme.config(text=format_tl(vals[3]))
            self.lbl_kidem.config(text=format_tl(vals[4]))
            self.lbl_ozel_hizmet.config(text=format_tl(vals[5]))
            self.lbl_makam.config(text=format_tl(vals[6]))
            self.lbl_dil.config(text=format_tl(vals[7]))
            self.lbl_ek_odeme.config(text=format_tl(vals[8]))
            self.lbl_ek_tazminat.config(text=format_tl(vals[9]))
            self.lbl_ilave_odeme.config(text=format_tl(vals[10]))

            toplam = sum(vals)
            self.lbl_toplam.config(text=format_tl(toplam))

            if self.selected_borc_turu == 'nafaka':
                return

            hesaplanan = toplam / 4
            self.hesaplanan_float = hesaplanan
            self.lbl_hesaplanan.config(text=format_tl(hesaplanan))
            self.entry_kesinti.delete(0, tk.END)
            self.entry_kesinti.insert(0, f"{hesaplanan:.2f}")

    def borc_sec(self, event=None):
        secim = self.borc_combobox.get()
        if not secim:
            self.selected_borc_id = None
            self.selected_borc_turu = 'icra'
            self.selected_nafaka_tutari = 0.0
            self.update_borc_turu_ui()
            return

        self.selected_borc_id = parse_id_from_secim(secim)
        if self.selected_borc_id is None:
            return

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT icra_daire_adi, dosya_no, toplam_borc, onceki_kesinti, borc_turu, aylik_nafaka_tutari
                FROM borc WHERE id = ?
            """, (self.selected_borc_id,))
            row = cursor.fetchone()

        if row:
            self.lbl_daire.config(text=row[0] or '-')
            self.lbl_dosya.config(text=row[1] or '-')
            self.lbl_toplam_borc.config(text=format_tl(row[2] or 0))
            self.lbl_onceki_kesinti.config(text=format_tl(row[3] or 0))
            self.selected_borc_turu = row[4] or 'icra'
            self.selected_nafaka_tutari = row[5] or 0.0
            self.get_onceki_kalan()
            self.update_borc_turu_ui()

    def update_borc_turu_ui(self):
        if self.selected_borc_turu == 'nafaka':
            self.btn_hesapla.config(state=tk.DISABLED)
            self.lbl_hesaplanan_baslik.config(text="MAHKEME KARARI TUTARI:")
            self.hesaplanan_float = self.selected_nafaka_tutari
            self.lbl_hesaplanan.config(text=format_tl(self.selected_nafaka_tutari))
            self.entry_kesinti.delete(0, tk.END)
            self.entry_kesinti.insert(0, f"{self.selected_nafaka_tutari:.2f}")
        else:
            self.btn_hesapla.config(state=tk.NORMAL)
            self.lbl_hesaplanan_baslik.config(text="ÖN HESAPLAMA (1/4):")
            if self.selected_maas_id:
                self.get_maas_bilgileri()

    def ay_sec(self, event=None):
        self.get_onceki_kalan()

    def get_onceki_kalan(self):
        if not self.selected_borc_id:
            return

        secili_ay = self.ay_combobox.get()

        with db_connection() as conn:
            cursor = conn.cursor()
            if secili_ay:
                cursor.execute("""
                    SELECT ay_sonu_kalan FROM kesinti_takip
                    WHERE borc_id = ? AND ay_yil < ?
                    ORDER BY ay_yil DESC, id DESC LIMIT 1
                """, (self.selected_borc_id, secili_ay))
            else:
                cursor.execute("""
                    SELECT ay_sonu_kalan FROM kesinti_takip
                    WHERE borc_id = ?
                    ORDER BY ay_yil DESC, id DESC LIMIT 1
                """, (self.selected_borc_id,))
            row = cursor.fetchone()

            if row and row[0] is not None:
                self.onceki_kalan_float = row[0]
                self.lbl_onceki_kalan.config(text=format_tl(row[0]))
            else:
                cursor.execute(
                    "SELECT toplam_borc, onceki_kesinti FROM borc WHERE id = ?",
                    (self.selected_borc_id,)
                )
                borc_row = cursor.fetchone()
                if borc_row:
                    toplam = borc_row[0] or 0.0
                    onceki = borc_row[1] or 0.0
                    kalan = toplam - onceki
                    self.onceki_kalan_float = kalan
                    self.lbl_onceki_kalan.config(text=format_tl(kalan))
                else:
                    self.onceki_kalan_float = 0.0
                    self.lbl_onceki_kalan.config(text=format_tl(0))

    def hesapla(self):
        self.get_maas_bilgileri()

    def kaydet(self):
        if not self.selected_personel_id:
            messagebox.showerror("Hata", "Lütfen bir personel seçin!")
            return

        if not self.selected_borc_id:
            messagebox.showerror("Hata", "Lütfen bir borç seçin!")
            return

        ay_yil = self.ay_combobox.get()
        if not ay_yil:
            messagebox.showerror("Hata", "Lütfen ay/yıl seçin!")
            return

        kesilen_tutar = parse_float(self.entry_kesinti.get())
        if kesilen_tutar is None:
            messagebox.showerror("Hata", "Geçerli bir kesinti tutarı giriniz!")
            return

        if kesilen_tutar <= 0:
            messagebox.showerror("Hata", "Kesinti tutarı 0'dan büyük olmalıdır!")
            return

        onceki_kalan = self.onceki_kalan_float
        hesaplanan = self.hesaplanan_float

        ay_sonu_kalan = onceki_kalan - kesilen_tutar

        if ay_sonu_kalan < 0:
            if not messagebox.askyesno("Uyarı",
                f"Kesinti tutarı kalan borçtan fazla!\n\n"
                f"Kalan Borç: {format_tl(onceki_kalan)}\n"
                f"Kesilecek Tutar: {format_tl(kesilen_tutar)}\n"
                f"Fazla Kesinti: {format_tl(abs(ay_sonu_kalan))}\n\n"
                f"Yine de kaydetmek istiyor musunuz?"):
                return
            ay_sonu_kalan = 0

        aciklama = self.entry_aciklama.get().strip()
        arsiv_guncellendi = False

        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM kesinti_takip WHERE borc_id = ? AND ay_yil = ?
                """, (self.selected_borc_id, ay_yil))
                if cursor.fetchone()[0] > 0:
                    messagebox.showerror("Hata",
                        f"Bu borç için {ay_yil} ayına ait kesinti kaydı zaten mevcut!\n\n"
                        f"Aynı ay birden fazla kez kaydedilemez - lütfen farklı bir ay seçin.")
                    return

                cursor.execute("""
                    INSERT INTO kesinti_takip 
                    (borc_id, ay_yil, onceki_kalan, hesaplanan_kesinti, kesilen_tutar, ay_sonu_kalan, aciklama)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (self.selected_borc_id, ay_yil, onceki_kalan, hesaplanan, kesilen_tutar, ay_sonu_kalan, aciklama))

                try:
                    cursor.execute("""
                        SELECT id, veri_json FROM maas_arsiv 
                        WHERE kurum_id = ? AND donem_ay_yil = ?
                    """, (self.kurum_id, ay_yil))
                    arsiv_row = cursor.fetchone()

                    if arsiv_row:
                        arsiv_id = arsiv_row[0]
                        veri_listesi = json.loads(arsiv_row[1])

                        tc_no = None
                        cursor.execute("SELECT tc_no FROM personel WHERE id = ?", (self.selected_personel_id,))
                        tc_row = cursor.fetchone()

                        if tc_row:
                            tc_no = tc_row[0]
                            beklenen = len(MAAS_DEGISIKLIK_KOLONLARI)

                            for i, satir in enumerate(veri_listesi):
                                if len(satir) > TC_NO_INDEX and str(satir[TC_NO_INDEX]) == str(tc_no):
                                    if len(satir) != beklenen:
                                        log_warning(
                                            f"Arşiv satırı kolon sayısı uyumsuz "
                                            f"({len(satir)} != {beklenen}), TC {tc_no} atlandı."
                                        )
                                        break
                                    satir[KESINTI_INDEX] = f"{kesilen_tutar:.2f}"
                                    veri_listesi[i] = satir
                                    arsiv_guncellendi = True
                                    break

                            if arsiv_guncellendi:
                                yeni_json = json.dumps(veri_listesi, ensure_ascii=False)
                                cursor.execute("""
                                    UPDATE maas_arsiv SET veri_json = ? WHERE id = ?
                                """, (yeni_json, arsiv_id))
                except Exception as e:
                    log_exception_context("Arşiv güncelleme hatası", e)

            arsiv_notu = "\n✅ Arşiv de güncellendi." if arsiv_guncellendi else "\n⚠️ Arşivde bu dönem için kayıt yok (Maaş Değişiklik ekranından arşivleyin)."
            
            messagebox.showinfo("Başarılı",
                f"✅ Kesinti başarıyla kaydedildi!\n\n"
                f"Önceki Kalan: {format_tl(onceki_kalan)}\n"
                f"Kesilen Tutar: {format_tl(kesilen_tutar)}\n"
                f"Yeni Kalan: {format_tl(ay_sonu_kalan)}"
                f"{arsiv_notu}"
            )

            self.temizle()
            self.borc_sec()
            self.get_onceki_kalan()

        except Exception as e:
            log_exception_context("Kesinti kayıt hatası", e)
            messagebox.showerror("Hata", f"Kayıt hatası: {str(e)}")

    def temizle(self):
        self.entry_kesinti.delete(0, tk.END)
        self.entry_aciklama.delete(0, tk.END)
        self.selected_kesinti_id = None

    def show_gecmis(self):
        if not self.selected_borc_id:
            messagebox.showerror("Hata", "Lütfen bir borç seçin!")
            return

        gecmis_window = tk.Toplevel(self.frame)
        gecmis_window.title("Kesinti Geçmişi")
        gecmis_window.geometry("850x450")

        columns = ("id", "ay_yil", "onceki_kalan", "hesaplanan", "kesilen", "ay_sonu_kalan", "aciklama")
        tree = ttk.Treeview(gecmis_window, columns=columns, show="headings")

        tree.heading("id", text="ID")
        tree.heading("ay_yil", text="Ay/Yıl")
        tree.heading("onceki_kalan", text="Önceki Kalan")
        tree.heading("hesaplanan", text="Hesaplanan")
        tree.heading("kesilen", text="Kesilen")
        tree.heading("ay_sonu_kalan", text="Ay Sonu Kalan")
        tree.heading("aciklama", text="Açıklama")

        tree.column("id", width=50, anchor="center")
        tree.column("ay_yil", width=90, anchor="center")
        tree.column("onceki_kalan", width=110, anchor="e")
        tree.column("hesaplanan", width=110, anchor="e")
        tree.column("kesilen", width=110, anchor="e")
        tree.column("ay_sonu_kalan", width=110, anchor="e")
        tree.column("aciklama", width=140)

        scrollbar = ttk.Scrollbar(gecmis_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(gecmis_window)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=8)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y, pady=5)

        def yukle():
            for item in tree.get_children():
                tree.delete(item)
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, ay_yil, onceki_kalan, hesaplanan_kesinti, kesilen_tutar, ay_sonu_kalan, aciklama
                    FROM kesinti_takip WHERE borc_id = ?
                    ORDER BY ay_yil DESC, id DESC
                """, (self.selected_borc_id,))
                for row in cursor.fetchall():
                    tree.insert("", tk.END, values=(
                        row[0], row[1],
                        format_tl(row[2] or 0),
                        format_tl(row[3] or 0),
                        format_tl(row[4] or 0),
                        format_tl(row[5] or 0),
                        row[6] or ""
                    ))

        def sonraki_ay_var_mi(ay_yil):
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM kesinti_takip
                    WHERE borc_id = ? AND ay_yil > ?
                """, (self.selected_borc_id, ay_yil))
                return cursor.fetchone()[0]

        def secili_kaydi_al():
            secim = tree.selection()
            if not secim:
                messagebox.showwarning("Uyarı", "Lütfen listeden bir kayıt seçin!")
                return None
            return tree.item(secim[0])["values"]

        def sil():
            degerler = secili_kaydi_al()
            if not degerler:
                return
            kesinti_id, ay_yil = degerler[0], degerler[1]

            sonraki_sayisi = sonraki_ay_var_mi(ay_yil)
            uyari = f"{ay_yil} ayına ait bu kesinti kaydını silmek istediğinize emin misiniz?"
            if sonraki_sayisi > 0:
                uyari += (f"\n\n⚠️ Bu aydan SONRAKİ {sonraki_sayisi} ay için zaten kayıt var. "
                          f"Bu kaydı silmek onların 'Önceki Kalan Borç' değerini otomatik "
                          f"güncellemez - gerekirse o ayları elden kontrol edin.")

            if not messagebox.askyesno("Onay", uyari):
                return

            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM kesinti_takip WHERE id = ?", (kesinti_id,))

            yukle()
            self.get_onceki_kalan()
            messagebox.showinfo("Başarılı", "Kayıt silindi.")

        def duzenle():
            degerler = secili_kaydi_al()
            if not degerler:
                return
            kesinti_id, ay_yil = degerler[0], degerler[1]
            
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT onceki_kalan, kesilen_tutar FROM kesinti_takip WHERE id = ?", (kesinti_id,))
                row = cursor.fetchone()
                onceki_kalan = row[0] if row else 0.0
                mevcut_kesilen = row[1] if row else 0.0

            sonraki_sayisi = sonraki_ay_var_mi(ay_yil)

            duzenle_win = tk.Toplevel(gecmis_window)
            duzenle_win.title(f"{ay_yil} Kaydını Düzenle")
            duzenle_win.geometry("380x220")
            duzenle_win.resizable(False, False)

            tk.Label(duzenle_win, text=f"Ay/Yıl: {ay_yil}", font=("Arial", 10, "bold")).pack(pady=(15, 5))
            tk.Label(duzenle_win, text=f"Önceki Kalan Borç: {format_tl(onceki_kalan)}", font=("Arial", 9)).pack(pady=2)

            tk.Label(duzenle_win, text="Kesilen Tutar:", font=("Arial", 10)).pack(pady=(10, 2))
            entry_kesilen = tk.Entry(duzenle_win, width=20, justify="center")
            entry_kesilen.pack()
            entry_kesilen.insert(0, f"{mevcut_kesilen:.2f}")

            if sonraki_sayisi > 0:
                tk.Label(duzenle_win, text=f"⚠️ Sonraki {sonraki_sayisi} ayın kaydı bu değişiklikten\n"
                                            f"otomatik etkilenmez, elden kontrol edin.",
                         font=("Arial", 8), fg="#B71C1C", justify="center").pack(pady=(10, 0))

            def kaydet_duzenleme():
                yeni_kesilen = parse_float(entry_kesilen.get())
                if yeni_kesilen is None:
                    messagebox.showerror("Hata", "Geçerli bir tutar giriniz!", parent=duzenle_win)
                    return

                yeni_ay_sonu = onceki_kalan - yeni_kesilen

                with db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE kesinti_takip
                        SET kesilen_tutar = ?, ay_sonu_kalan = ?
                        WHERE id = ?
                    """, (yeni_kesilen, yeni_ay_sonu, kesinti_id))

                duzenle_win.destroy()
                yukle()
                self.get_onceki_kalan()
                messagebox.showinfo("Başarılı", "Kayıt güncellendi.")

            tk.Button(duzenle_win, text="💾 Kaydet", command=kaydet_duzenleme,
                      bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(pady=15)

        tk.Button(button_frame, text="✏️ Düzenle", command=duzenle,
                  bg="#FFC107", font=("Arial", 10), width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="🗑️ Sil", command=sil,
                  bg="#f44336", fg="white", font=("Arial", 10), width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="🔄 Yenile", command=yukle,
                  bg="#2196F3", fg="white", font=("Arial", 10), width=12).pack(side=tk.LEFT, padx=5)

        yukle()