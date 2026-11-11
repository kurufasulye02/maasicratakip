# gui/maas_degisiklik.py - Maaş Değişiklik İşlemleri (V.3.2.0 - 3 Sütunlu Düzen)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import db_connection
from utils.base_page import BasePage
from utils.kurum_context import KurumContext
from utils.maas_excel_export import maas_degisiklik_excel_olustur
from utils.logger import log_info, log_warning, log_exception_context

MAAS_DEGISIKLIK_KOLONLARI = ("id", "saymanlik_no", "ad_soyad", "tc_no", "banka",
                             "eski_der", "eski_kad", "yeni_der", "yeni_kad", "terfi",
                             "aile_yardimi", "cocuk_0_6", "cocuk_6_ustu",
                             "uzman", "bas", "rapor", "emekli", "sendika",
                             "naklen_geldi", "naklen_gitti", "ucretsiz_dondu", "ucretsiz_cikti", "kesinti",
                             "saglik_sigorta", "kefalet")
TC_NO_INDEX = MAAS_DEGISIKLIK_KOLONLARI.index("tc_no")
KESINTI_INDEX = MAAS_DEGISIKLIK_KOLONLARI.index("kesinti")
SAGLIK_SIGORTA_INDEX = MAAS_DEGISIKLIK_KOLONLARI.index("saglik_sigorta")
KEFALET_INDEX = MAAS_DEGISIKLIK_KOLONLARI.index("kefalet")


class MaasDegisiklikIslemleri(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.kurum_id = KurumContext.get_active_id()
        self.selected_personel_id = None
        self.current_ay_yil = datetime.now().strftime("%Y-%m")
        self.create_widgets()
        self.load_personel_list()
        self.apply_theme(self.theme)

    def create_widgets(self):
        theme = self.theme

        self.frame = tk.Frame(self.parent, bg=theme['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        title = tk.Label(self.frame, text="📝 MAAŞ DEĞİŞİKLİK BİLDİRİM FORMU",
                         font=("Segoe UI", 18, "bold"), fg="#1a237e", bg=theme['bg'])
        title.grid(row=0, column=0, columnspan=6, pady=(0, 10))

        desc = tk.Label(self.frame,
                        text="Personele ait maaş değişikliklerini girin, MEB formatında Excel raporu oluşturun ve arşivleyin.",
                        font=("Segoe UI", 10), fg=theme['label_secondary'], bg=theme['bg'])
        desc.grid(row=1, column=0, columnspan=6, pady=(0, 15))

        self.kurum_label = tk.Label(self.frame, text=KurumContext.get_status_text(),
                                    font=("Segoe UI", 10, "bold"), fg="blue", bg=theme['bg'])
        self.kurum_label.grid(row=2, column=0, columnspan=6, sticky="w", pady=5)

        form_frame = tk.LabelFrame(self.frame, text="➕ Değişiklik Giriş / Düzenleme",
                                   bg=theme['bg'], fg=theme['fg'], padx=10, pady=10)
        form_frame.grid(row=3, column=0, columnspan=6, pady=10, sticky="ew")

        # ================= SÜTUN 1 (Kimlik ve Kadro) =================
        bolge1 = tk.Frame(form_frame, bg=theme['bg'])
        bolge1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        # Satır 0: Personel
        tk.Label(bolge1, text="Personel Seçin:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=0, column=0, sticky="w", pady=5)
        self.personel_combobox = ttk.Combobox(bolge1, width=28, font=("Segoe UI", 10))
        self.personel_combobox.grid(row=0, column=1, columnspan=3, pady=5, sticky="w")
        self.personel_combobox.bind("<<ComboboxSelected>>", self.personel_combobox_sec)

        # Satır 1: Banka Hesap No (YENİ YERİ)
        tk.Label(bolge1, text="Banka Hesap No:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_banka_hesap = tk.Entry(bolge1, width=22, font=("Segoe UI", 10))
        self.entry_banka_hesap.grid(row=1, column=1, columnspan=2, pady=5, sticky="w")

        # Satır 2: TC ve Saymanlık
        tk.Label(bolge1, text="TC Kimlik:", font=("Segoe UI", 10, "bold"), bg=theme['bg']).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_tc = tk.Entry(bolge1, width=15, font=("Segoe UI", 10))
        self.entry_tc.grid(row=2, column=1, pady=5, sticky="w")

        tk.Label(bolge1, text="Saymanlık No:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=2, column=2, sticky="w", padx=(10, 5), pady=5)
        self.entry_saymanlik = tk.Entry(bolge1, width=15, font=("Segoe UI", 10))
        self.entry_saymanlik.grid(row=2, column=3, pady=5, sticky="w")

        # Satır 3: ESKİ Başlığı
        tk.Label(bolge1, text="ESKİ", font=("Segoe UI", 9, "bold"), bg=theme['bg']).grid(row=3, column=0, sticky="w", pady=(10, 2))

        # Satır 4: Eski Der/Kad
        tk.Label(bolge1, text="Eski Der.:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=4, column=0, sticky="w")
        self.entry_eski_der = tk.Entry(bolge1, width=10, font=("Segoe UI", 10))
        self.entry_eski_der.grid(row=4, column=1, sticky="w")

        tk.Label(bolge1, text="Eski Kad.:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=4, column=2, sticky="w", padx=(10, 2))
        self.entry_eski_kad = tk.Entry(bolge1, width=10, font=("Segoe UI", 10))
        self.entry_eski_kad.grid(row=4, column=3, sticky="w")

        # Satır 5: YENİ Başlığı
        tk.Label(bolge1, text="YENİ", font=("Segoe UI", 9, "bold"), bg=theme['bg']).grid(row=5, column=0, sticky="w", pady=(15, 2))

        # Satır 6: Yeni Der/Kad
        tk.Label(bolge1, text="Yeni Der.:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=6, column=0, sticky="w")
        self.entry_yeni_der = tk.Entry(bolge1, width=10, font=("Segoe UI", 10))
        self.entry_yeni_der.grid(row=6, column=1, sticky="w")

        tk.Label(bolge1, text="Yeni Kad.:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=6, column=2, sticky="w", padx=(10, 2))
        self.entry_yeni_kad = tk.Entry(bolge1, width=10, font=("Segoe UI", 10))
        self.entry_yeni_kad.grid(row=6, column=3, sticky="w")

        # Satır 7: Terfi Tarihi
        tk.Label(bolge1, text="Terfi Tarihi:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=7, column=0, sticky="w", pady=(5, 2))
        self.entry_terfi_tarihi = tk.Entry(bolge1, width=15, font=("Segoe UI", 10))
        self.entry_terfi_tarihi.grid(row=7, column=1, columnspan=2, sticky="w")


        # ================= SÜTUN 2 (Mali Haklar) =================
        bolge2 = tk.Frame(form_frame, bg=theme['bg'])
        bolge2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        # Satır 0: Aile Yardımı
        self.var_aile_yardimi = tk.BooleanVar()
        tk.Checkbutton(bolge2, text="Aile Yardımı (Var)", variable=self.var_aile_yardimi, bg=theme['bg']).grid(row=0, column=0, columnspan=2, sticky="w", pady=2)

        # Satır 1: Çocuk 0-6
        tk.Label(bolge2, text="Çocuk Yrd. 0-6 Yaş:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_cocuk_0_6 = tk.Entry(bolge2, width=12, font=("Segoe UI", 10))
        self.entry_cocuk_0_6.grid(row=1, column=1, sticky="w", padx=2)

        # Satır 2: Çocuk 6+
        tk.Label(bolge2, text="Çocuk Yrd. 6+ Yaş:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_cocuk_6_ustu = tk.Entry(bolge2, width=12, font=("Segoe UI", 10))
        self.entry_cocuk_6_ustu.grid(row=2, column=1, sticky="w", padx=2)

        # Satır 3: Raporlu Gün
        tk.Label(bolge2, text="Raporlu (Gün):", font=("Segoe UI", 10), bg=theme['bg']).grid(row=3, column=0, sticky="w", pady=5)
        self.entry_raporlu = tk.Entry(bolge2, width=12, font=("Segoe UI", 10))
        self.entry_raporlu.grid(row=3, column=1, sticky="w", padx=2)

        # Satır 4: Kesinti (Haciz/Nafaka)
        tk.Label(bolge2, text="Kesinti (Haciz/Nafaka) TL:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=4, column=0, sticky="w", pady=5)
        self.entry_kesinti = tk.Entry(bolge2, width=12, font=("Segoe UI", 10))
        self.entry_kesinti.grid(row=4, column=1, sticky="w", padx=2)

        # Satır 5: Sağlık Sigortası
        tk.Label(bolge2, text="Sağlık/Hayat Sig. İnd. TL:", font=("Segoe UI", 10), bg=theme['bg']).grid(row=5, column=0, sticky="w", pady=5)
        self.entry_saglik_sigorta = tk.Entry(bolge2, width=12, font=("Segoe UI", 10))
        self.entry_saglik_sigorta.grid(row=5, column=1, sticky="w", padx=2)


        # ================= SÜTUN 3 (Durum Bildirimleri - Checkboxlar) =================
        bolge3 = tk.Frame(form_frame, bg=theme['bg'])
        bolge3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.var_uzman = tk.BooleanVar()
        self.var_bas_ogretmen = tk.BooleanVar()
        self.var_naklen_geldi = tk.BooleanVar()
        self.var_naklen_gitti = tk.BooleanVar()
        self.var_sendika = tk.BooleanVar()

        tk.Checkbutton(bolge3, text="Uzman Öğretmen", variable=self.var_uzman, bg=theme['bg']).grid(row=0, column=0, sticky="w", pady=2)
        tk.Checkbutton(bolge3, text="Baş Öğretmen", variable=self.var_bas_ogretmen, bg=theme['bg']).grid(row=1, column=0, sticky="w", pady=2)
        tk.Checkbutton(bolge3, text="Naklen Geldi", variable=self.var_naklen_geldi, bg=theme['bg']).grid(row=2, column=0, sticky="w", pady=2)
        tk.Checkbutton(bolge3, text="Naklen Gitti", variable=self.var_naklen_gitti, bg=theme['bg']).grid(row=3, column=0, sticky="w", pady=2)
        tk.Checkbutton(bolge3, text="Sendika Değişikliği", variable=self.var_sendika, bg=theme['bg']).grid(row=4, column=0, sticky="w", pady=2)


        # ================= SÜTUN 4 (İzin ve Diğer) =================
        bolge4 = tk.Frame(form_frame, bg=theme['bg'])
        bolge4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.var_ucretsiz_cikti = tk.BooleanVar()
        self.var_ucretsiz_dondu = tk.BooleanVar()
        self.var_kefalet = tk.BooleanVar()
        self.var_emekli = tk.BooleanVar()

        tk.Checkbutton(bolge4, text="Ücretsiz İzin Çıktı", variable=self.var_ucretsiz_cikti, bg=theme['bg']).grid(row=0, column=0, sticky="w", pady=2)
        tk.Checkbutton(bolge4, text="Ücretsiz İzin Döndü", variable=self.var_ucretsiz_dondu, bg=theme['bg']).grid(row=1, column=0, sticky="w", pady=2)
        tk.Checkbutton(bolge4, text="Kefalet Aidatı (Giriş)", variable=self.var_kefalet, bg=theme['bg']).grid(row=2, column=0, sticky="w", pady=2)
        tk.Checkbutton(bolge4, text="Emekli Oldu", variable=self.var_emekli, bg=theme['bg']).grid(row=3, column=0, sticky="w", pady=2)


        # --- BUTONLAR ---
        alt_bolge = tk.Frame(form_frame, bg=theme['bg'])
        alt_bolge.pack(side=tk.BOTTOM, fill=tk.X, pady=(15, 0))

        btn_frame = tk.Frame(alt_bolge, bg=theme['bg'])
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        btn_center = tk.Frame(btn_frame, bg=theme['bg'])
        btn_center.pack(anchor="center")

        self.btn_ekle = tk.Button(btn_center, text="➕ Değişiklik Ekle", command=self.ekle,
                                  bg="#4CAF50", fg="white", font=("Segoe UI", 9, "bold"), width=18)
        self.btn_ekle.pack(side=tk.LEFT, padx=3)

        self.btn_guncelle = tk.Button(btn_center, text="✏️ Güncelle", command=self.guncelle,
                                      bg="#FFC107", font=("Segoe UI", 9, "bold"), width=14)
        self.btn_guncelle.pack(side=tk.LEFT, padx=3)

        self.btn_temizle = tk.Button(btn_center, text="🧹 Temizle", command=self.temizle_form,
                                     bg="#9E9E9E", fg="white", font=("Segoe UI", 9), width=14)
        self.btn_temizle.pack(side=tk.LEFT, padx=3)

        list_frame = tk.LabelFrame(self.frame, text="📋 Bu Aya Ait Değişiklik Listesi",
                                   bg=theme['bg'], fg=theme['fg'], padx=10, pady=10)
        list_frame.grid(row=4, column=0, columnspan=6, pady=10, sticky="nsew")

        columns = MAAS_DEGISIKLIK_KOLONLARI
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)

        self.tree.heading("id", text="Sıra")
        self.tree.heading("saymanlik_no", text="Saymanlık No")
        self.tree.heading("ad_soyad", text="Ad Soyad")
        self.tree.heading("tc_no", text="TC")
        self.tree.heading("banka", text="Banka Hesap")
        self.tree.heading("eski_der", text="E. Der.")
        self.tree.heading("eski_kad", text="E. Kad.")
        self.tree.heading("yeni_der", text="Y. Der.")
        self.tree.heading("yeni_kad", text="Y. Kad.")
        self.tree.heading("terfi", text="Terfi Tarihi")
        self.tree.heading("aile_yardimi", text="Aile Yrd.")
        self.tree.heading("cocuk_0_6", text="Çocuk 0-6")
        self.tree.heading("cocuk_6_ustu", text="Çocuk 6+")
        self.tree.heading("uzman", text="Uzman")
        self.tree.heading("bas", text="Baş Öğrt")
        self.tree.heading("rapor", text="Raporlu (Gün)")
        self.tree.heading("emekli", text="Emekli")
        self.tree.heading("sendika", text="Sendika")
        self.tree.heading("naklen_geldi", text="Nak. Geldi")
        self.tree.heading("naklen_gitti", text="Nak. Gitti")
        self.tree.heading("ucretsiz_dondu", text="Ücr. Döndü")
        self.tree.heading("ucretsiz_cikti", text="Ücr. Çıktı")
        self.tree.heading("kesinti", text="Kesinti (TL)")
        self.tree.heading("saglik_sigorta", text="Sağlık Sig. (TL)")
        self.tree.heading("kefalet", text="Kefalet Aidatı")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("saymanlik_no", width=90, anchor="center")
        self.tree.column("ad_soyad", width=130)
        self.tree.column("tc_no", width=100, anchor="center")
        self.tree.column("banka", width=120)
        self.tree.column("eski_der", width=50, anchor="center")
        self.tree.column("eski_kad", width=50, anchor="center")
        self.tree.column("yeni_der", width=50, anchor="center")
        self.tree.column("yeni_kad", width=50, anchor="center")
        self.tree.column("terfi", width=80, anchor="center")
        self.tree.column("aile_yardimi", width=55, anchor="center")
        self.tree.column("cocuk_0_6", width=55, anchor="center")
        self.tree.column("cocuk_6_ustu", width=55, anchor="center")
        self.tree.column("uzman", width=50, anchor="center")
        self.tree.column("bas", width=60, anchor="center")
        self.tree.column("rapor", width=70, anchor="center")
        self.tree.column("emekli", width=50, anchor="center")
        self.tree.column("sendika", width=60, anchor="center")
        self.tree.column("naklen_geldi", width=60, anchor="center")
        self.tree.column("naklen_gitti", width=60, anchor="center")
        self.tree.column("ucretsiz_dondu", width=65, anchor="center")
        self.tree.column("ucretsiz_cikti", width=65, anchor="center")
        self.tree.column("kesinti", width=85, anchor="e")
        self.tree.column("saglik_sigorta", width=85, anchor="e")
        self.tree.column("kefalet", width=75, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.tree_sec)

        # ARŞİV VE ÖNCEKİ AYLAR
        alt_islemler_frame = tk.Frame(self.frame, bg=theme['bg'])
        alt_islemler_frame.grid(row=5, column=0, columnspan=6, pady=10, sticky="ew")
        alt_islemler_frame.grid_columnconfigure(0, weight=1)
        alt_islemler_frame.grid_columnconfigure(1, weight=1)

        arsiv_frame = tk.LabelFrame(alt_islemler_frame, text="📦 Arşiv İşlemleri",
                                    bg=theme['bg'], fg=theme['fg'], padx=10, pady=10)
        arsiv_frame.grid(row=0, column=0, sticky="nsew")

        arsiv_sol = tk.Frame(arsiv_frame, bg=theme['bg'])
        arsiv_sol.pack(fill=tk.X)

        tk.Label(arsiv_sol, text="Dönem (Yıl-Ay):", font=("Segoe UI", 10), bg=theme['bg']).pack(side=tk.LEFT, padx=5)
        self.entry_arsiv_donem = tk.Entry(arsiv_sol, width=12, font=("Segoe UI", 10))
        self.entry_arsiv_donem.pack(side=tk.LEFT, padx=5)
        self.entry_arsiv_donem.insert(0, datetime.now().strftime("%Y-%m"))
        self.entry_arsiv_donem.bind("<FocusOut>", lambda e: self.otomatik_kesinti_cek())
        self.entry_arsiv_donem.bind("<Return>", lambda e: self.otomatik_kesinti_cek())

        tk.Label(arsiv_sol, text="(Örn: 2026-01)", font=("Segoe UI", 8), fg=theme['label_secondary'], bg=theme['bg']).pack(side=tk.LEFT, padx=5)

        arsiv_sag = tk.Frame(arsiv_frame, bg=theme['bg'])
        arsiv_sag.pack(pady=5)

        self.btn_arsivle = tk.Button(arsiv_sag, text="📤 Arşive Gönder", command=self.arsivle,
                                     bg="#FF9800", fg="white", font=("Segoe UI", 9, "bold"), width=16)
        self.btn_arsivle.pack(side=tk.LEFT, padx=5)

        self.btn_arsiv_getir = tk.Button(arsiv_sag, text="📥 Arşivden Getir", command=self.arsiv_getir,
                                         bg="#795548", fg="white", font=("Segoe UI", 9, "bold"), width=16)
        self.btn_arsiv_getir.pack(side=tk.LEFT, padx=5)

        self.btn_arsiv_liste = tk.Button(arsiv_sag, text="📋 Arşiv Listesi", command=self.arsiv_listele,
                                         bg="#607D8B", fg="white", font=("Segoe UI", 9, "bold"), width=14)
        self.btn_arsiv_liste.pack(side=tk.LEFT, padx=5)

        onceki_aylar_frame = tk.LabelFrame(alt_islemler_frame, text="📅 Önceki Aylarda Ödeme Yapılan Personel Sayısı",
                                            bg=theme['bg'], fg=theme['fg'], padx=10, pady=10)
        onceki_aylar_frame.grid(row=0, column=1, sticky="nsew")

        onceki_inner = tk.Frame(onceki_aylar_frame, bg=theme['bg'])
        onceki_inner.pack(fill=tk.X)

        aylar = ["Ocak:", "Şubat:", "Mart:", "Nisan:", "Mayıs:", "Haziran:",
                 "Temmuz:", "Ağustos:", "Eylül:", "Ekim:", "Kasım:", "Aralık:"]

        self.onceki_ay_entries = []

        for idx, ay_adi in enumerate(aylar):
            tk.Label(onceki_inner, text=ay_adi, font=("Segoe UI", 9),
                     bg=theme['bg'], fg=theme['fg']).pack(side=tk.LEFT, padx=(5, 0))
            entry = tk.Entry(onceki_inner, width=5, font=("Segoe UI", 9),
                             bg=theme['entry_bg'], fg=theme['entry_fg'])
            entry.pack(side=tk.LEFT, padx=(0, 10))
            self.onceki_ay_entries.append(entry)

        devret_btn = tk.Button(onceki_aylar_frame, text="📥 Son Aydan Devret", command=self.son_aydan_devret,
                               bg="#1a237e", fg="white", font=("Segoe UI", 9, "bold"))
        devret_btn.pack(pady=5)

        self.load_onceki_aylar()

        action_frame = tk.Frame(self.frame, bg=theme['bg'])
        action_frame.grid(row=6, column=0, columnspan=6, pady=5)

        self.btn_sil = tk.Button(action_frame, text="🗑️ Seçili Değişikliği Sil", command=self.sil,
                                 bg="#f44336", fg="white", font=("Segoe UI", 10, "bold"), width=25)
        self.btn_sil.pack(side=tk.LEFT, padx=5)

        self.btn_excel = tk.Button(action_frame, text="📊 MEB Excel Raporu Oluştur", command=self.excel_olustur,
                                   bg="#2196F3", fg="white", font=("Segoe UI", 11, "bold"), width=25)
        self.btn_excel.pack(side=tk.LEFT, padx=15)

        self.btn_kaydet_onceki = tk.Button(action_frame, text="💾 Önceki Ayları Kaydet", command=self.kaydet_onceki_aylar,
                                           bg="#673AB7", fg="white", font=("Segoe UI", 10, "bold"), width=20)
        self.btn_kaydet_onceki.pack(side=tk.LEFT, padx=5)

        self.frame.grid_rowconfigure(4, weight=1)
        for col in range(6):
            self.frame.grid_columnconfigure(col, weight=1)

    # ... (Geri kalan tüm fonksiyonlar - load_personel_list, ekle, guncelle, arsivle vs. - AYNI şekilde kalacak)
    # NOT: Sadece create_widgets kısmı değişti, diğer fonksiyonlar önceki mesajındaki gibi kalmalı.
    # Eğer tüm dosyayı kopyalamak istersen, lütfen önceki tam kodu bu yeni create_widgets ile birleştir.
    
    def load_personel_list(self):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, ad_soyad, tc_no, saymanlik_no FROM personel WHERE kurum_id = ? AND (aktif IS NULL OR aktif = 1)", (self.kurum_id,))
            rows = cursor.fetchall()

        from utils.helpers import turkce_sirala_anahtari
        rows = sorted(rows, key=lambda r: turkce_sirala_anahtari(r[1] or ""))

        self.personel_listesi = rows
        self.personel_combobox['values'] = [f"{r[1]} (TC:{r[2]})" for r in rows]
        if rows:
            self.personel_combobox.set(self.personel_combobox['values'][0])
            self.personel_combobox_sec()

    def personel_combobox_sec(self, event=None):
        secim = self.personel_combobox.get()
        if not secim:
            return
        try:
            tc = secim.split("TC:")[1].replace(")", "").strip()
            self.entry_tc.delete(0, tk.END)
            self.entry_tc.insert(0, tc)
            self.entry_saymanlik.delete(0, tk.END)

            self.selected_personel_id = None
            for r in self.personel_listesi:
                if r[2] == tc:
                    self.selected_personel_id = r[0]
                    self.entry_saymanlik.insert(0, r[3] or "")
                    break

            self.otomatik_kesinti_cek()
        except (IndexError, ValueError, AttributeError) as e:
            log_exception_context("Personel seçimi işlenirken hata", e)

    def otomatik_kesinti_cek(self):
        if not self.selected_personel_id:
            return

        ay_yil = self.entry_arsiv_donem.get().strip()
        if not ay_yil:
            return

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tc_no FROM personel WHERE id = ?", (self.selected_personel_id,))
            personel_row = cursor.fetchone()
            if not personel_row:
                return

            tc_no = personel_row[0]

            cursor.execute("""
                SELECT k.kesilen_tutar
                FROM kesinti_takip k
                JOIN borc b ON b.id = k.borc_id
                JOIN personel p ON p.id = b.personel_id
                WHERE p.tc_no = ? AND k.ay_yil = ?
                ORDER BY k.id DESC LIMIT 1
            """, (tc_no, ay_yil))

            row = cursor.fetchone()

        if row:
            tutar = row[0] or 0
            log_info(f"Otomatik kesinti bulundu: TC={tc_no}, Ay={ay_yil}, Tutar={tutar}")
            self.entry_kesinti.delete(0, tk.END)
            self.entry_kesinti.insert(0, f"{tutar:.2f}")
        else:
            log_info(f"Otomatik kesinti bulunamadı: TC={tc_no}, Ay={ay_yil}")
            self.entry_kesinti.delete(0, tk.END)

    def _build_values_tuple(self, saymanlik_no, ad_soyad, tc, banka, eski_der, eski_kad,
                            yeni_der, yeni_kad, terfi, aile, c0_6, c6u, uzman, bas,
                            rapor, emekli, sendika, n_geldi, n_gitti, u_dondu, u_cikti,
                            kesinti, saglik, kefalet):
        return (
            len(self.tree.get_children()) + 1,
            saymanlik_no, ad_soyad, tc, banka,
            eski_der, eski_kad, yeni_der, yeni_kad, terfi,
            aile, c0_6, c6u,
            uzman, bas, rapor, emekli, sendika,
            n_geldi, n_gitti, u_dondu, u_cikti, kesinti,
            saglik, kefalet
        )

    def _collect_form(self):
        tc = self.entry_tc.get().strip()
        if not tc:
            messagebox.showerror("Hata", "Lütfen combobox'tan bir personel seçin!")
            return None

        ad_soyad = ""
        saymanlik_no = ""
        for r in self.personel_listesi:
            if r[2] == tc:
                ad_soyad = r[1]
                saymanlik_no = r[3] or ""
                break

        if not ad_soyad:
            messagebox.showerror("Hata", "Personel bulunamadı!")
            return None

        return {
            'tc': tc,
            'ad_soyad': ad_soyad,
            'saymanlik_no': saymanlik_no,
            'banka': self.entry_banka_hesap.get().strip(),
            'eski_der': self.entry_eski_der.get().strip(),
            'eski_kad': self.entry_eski_kad.get().strip(),
            'yeni_der': self.entry_yeni_der.get().strip(),
            'yeni_kad': self.entry_yeni_kad.get().strip(),
            'terfi': self.entry_terfi_tarihi.get().strip(),
            'rapor': self.entry_raporlu.get().strip(),
            'kesinti': self.entry_kesinti.get().strip(),
            'saglik': self.entry_saglik_sigorta.get().strip(),
            'kefalet': "X" if self.var_kefalet.get() else "",
            'aile': "X" if self.var_aile_yardimi.get() else "",
            'c0_6': self.entry_cocuk_0_6.get().strip(),
            'c6u': self.entry_cocuk_6_ustu.get().strip(),
            'uzman': "X" if self.var_uzman.get() else "",
            'bas': "X" if self.var_bas_ogretmen.get() else "",
            'emekli': "X" if self.var_emekli.get() else "",
            'sendika': "X" if self.var_sendika.get() else "",
            'n_geldi': "X" if self.var_naklen_geldi.get() else "",
            'n_gitti': "X" if self.var_naklen_gitti.get() else "",
            'u_dondu': "X" if self.var_ucretsiz_dondu.get() else "",
            'u_cikti': "X" if self.var_ucretsiz_cikti.get() else "",
        }

    def ekle(self):
        d = self._collect_form()
        if not d:
            return

        values = self._build_values_tuple(
            d['saymanlik_no'], d['ad_soyad'], d['tc'], d['banka'],
            d['eski_der'], d['eski_kad'], d['yeni_der'], d['yeni_kad'], d['terfi'],
            d['aile'], d['c0_6'], d['c6u'],
            d['uzman'], d['bas'], d['rapor'], d['emekli'], d['sendika'],
            d['n_geldi'], d['n_gitti'], d['u_dondu'], d['u_cikti'], d['kesinti'],
            d['saglik'], d['kefalet']
        )
        self.tree.insert("", tk.END, values=values)
        self.temizle_form()
        messagebox.showinfo("Başarılı", f"'{d['ad_soyad']}' için değişiklik listeye eklendi.")

    def guncelle(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Hata", "Lütfen güncellenecek satırı listeden seçin!")
            return

        d = self._collect_form()
        if not d:
            return

        eski_id = self.tree.item(selection[0])['values'][0]
        new_vals = list(self._build_values_tuple(
            d['saymanlik_no'], d['ad_soyad'], d['tc'], d['banka'],
            d['eski_der'], d['eski_kad'], d['yeni_der'], d['yeni_kad'], d['terfi'],
            d['aile'], d['c0_6'], d['c6u'],
            d['uzman'], d['bas'], d['rapor'], d['emekli'], d['sendika'],
            d['n_geldi'], d['n_gitti'], d['u_dondu'], d['u_cikti'], d['kesinti'],
            d['saglik'], d['kefalet']
        ))
        new_vals[0] = eski_id

        self.tree.item(selection[0], values=tuple(new_vals))
        self.temizle_form()
        messagebox.showinfo("Başarılı", "Değişiklik güncellendi.")

    def sil(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Hata", "Lütfen silinecek satırı seçin!")
            return
        self.tree.delete(selection[0])
        for i, item in enumerate(self.tree.get_children()):
            vals = self.tree.item(item)['values']
            self.tree.item(item, values=(i + 1,) + vals[1:])

    def tree_sec(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0])["values"]
        if not values:
            return

        tc = values[TC_NO_INDEX]
        for i, val in enumerate(self.personel_combobox['values']):
            if f"TC:{tc}" in val:
                self.personel_combobox.current(i)
                break
        self.personel_combobox_sec()

        self.entry_banka_hesap.delete(0, tk.END)
        self.entry_banka_hesap.insert(0, values[4] or "")

        self.entry_eski_der.delete(0, tk.END)
        self.entry_eski_der.insert(0, values[5] or "")
        self.entry_eski_kad.delete(0, tk.END)
        self.entry_eski_kad.insert(0, values[6] or "")

        self.entry_yeni_der.delete(0, tk.END)
        self.entry_yeni_der.insert(0, values[7] or "")
        self.entry_yeni_kad.delete(0, tk.END)
        self.entry_yeni_kad.insert(0, values[8] or "")

        self.entry_terfi_tarihi.delete(0, tk.END)
        self.entry_terfi_tarihi.insert(0, values[9] or "")

        self.var_aile_yardimi.set(values[10] == "X")
        self.entry_cocuk_0_6.delete(0, tk.END)
        self.entry_cocuk_0_6.insert(0, values[11] or "")
        self.entry_cocuk_6_ustu.delete(0, tk.END)
        self.entry_cocuk_6_ustu.insert(0, values[12] or "")

        self.entry_raporlu.delete(0, tk.END)
        self.entry_raporlu.insert(0, values[15] or "")

        self.var_uzman.set(values[13] == "X")
        self.var_bas_ogretmen.set(values[14] == "X")
        self.var_emekli.set(values[16] == "X")
        self.var_sendika.set(values[17] == "X")

        self.var_naklen_geldi.set(values[18] == "X")
        self.var_naklen_gitti.set(values[19] == "X")
        self.var_ucretsiz_dondu.set(values[20] == "X")
        self.var_ucretsiz_cikti.set(values[21] == "X")

        self.entry_kesinti.delete(0, tk.END)
        self.entry_kesinti.insert(0, values[KESINTI_INDEX])

        self.entry_saglik_sigorta.delete(0, tk.END)
        if len(values) > SAGLIK_SIGORTA_INDEX:
            self.entry_saglik_sigorta.insert(0, values[SAGLIK_SIGORTA_INDEX])

        self.var_kefalet.set(False)
        if len(values) > KEFALET_INDEX and values[KEFALET_INDEX] == "X":
            self.var_kefalet.set(True)

    def temizle_form(self):
        self.personel_combobox.set("")
        self.entry_tc.delete(0, tk.END)
        self.entry_saymanlik.delete(0, tk.END)
        self.entry_banka_hesap.delete(0, tk.END)
        self.entry_eski_der.delete(0, tk.END)
        self.entry_eski_kad.delete(0, tk.END)
        self.entry_yeni_der.delete(0, tk.END)
        self.entry_yeni_kad.delete(0, tk.END)
        self.entry_terfi_tarihi.delete(0, tk.END)
        self.entry_cocuk_0_6.delete(0, tk.END)
        self.entry_cocuk_6_ustu.delete(0, tk.END)
        self.entry_raporlu.delete(0, tk.END)
        self.entry_kesinti.delete(0, tk.END)
        self.entry_saglik_sigorta.delete(0, tk.END)

        self.var_aile_yardimi.set(False)
        self.var_uzman.set(False)
        self.var_bas_ogretmen.set(False)
        self.var_emekli.set(False)
        self.var_sendika.set(False)
        self.var_naklen_geldi.set(False)
        self.var_naklen_gitti.set(False)
        self.var_ucretsiz_dondu.set(False)
        self.var_ucretsiz_cikti.set(False)
        self.var_kefalet.set(False)

    def arsivle(self):
        if not self.tree.get_children():
            messagebox.showerror("Hata", "Arşivlenecek hiç veri yok!")
            return

        donem = self.entry_arsiv_donem.get().strip()
        if not donem:
            messagebox.showerror("Hata", "Lütfen arşiv dönemi (Yıl-Ay) giriniz!")
            return

        try:
            veri_listesi = []
            for item in self.tree.get_children():
                veri_listesi.append(list(self.tree.item(item)['values']))

            veri_json = json.dumps(veri_listesi, ensure_ascii=False)
            arsiv_adi = donem.replace("-", " ").upper() + " DÖNEMİ"

            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM maas_arsiv WHERE kurum_id = ? AND donem_ay_yil = ?", (self.kurum_id, donem))
                var = cursor.fetchone()

                if var:
                    cursor.execute("""
                        UPDATE maas_arsiv
                        SET arsiv_adi = ?, veri_json = ?, olusturma_tarihi = ?
                        WHERE id = ?
                    """, (arsiv_adi, veri_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), var[0]))
                    mesaj = f"✅ {donem} dönemine ait arşiv başarıyla GÜNCELLENDİ!"
                else:
                    cursor.execute("""
                        INSERT INTO maas_arsiv (kurum_id, arsiv_adi, donem_ay_yil, olusturma_tarihi, veri_json)
                        VALUES (?, ?, ?, ?, ?)
                    """, (self.kurum_id, arsiv_adi, donem, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), veri_json))
                    mesaj = f"✅ Veriler başarıyla arşivlendi!\n\nDönem: {arsiv_adi}"

                conn.commit()

            messagebox.showinfo("Başarılı", mesaj)

        except Exception as e:
            log_exception_context("Arşivleme hatası", e)
            messagebox.showerror("Hata", f"Arşivleme hatası: {str(e)}")

    def arsiv_getir(self):
        if not self.kurum_id:
            messagebox.showerror("Hata", "Aktif kurum seçili değil!")
            return

        donem = self.entry_arsiv_donem.get().strip()
        if not donem:
            messagebox.showerror("Hata", "Lütfen getirilecek arşiv dönemini (Yıl-Ay) giriniz!")
            return

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, arsiv_adi, veri_json FROM maas_arsiv
                WHERE kurum_id = ? AND donem_ay_yil = ?
                ORDER BY id DESC LIMIT 1
            """, (self.kurum_id, donem))
            row = cursor.fetchone()

        if not row:
            messagebox.showerror("Hata", f"{donem} dönemine ait arşivlenmiş veri bulunamadı!")
            return

        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            veri_listesi = json.loads(row[2])

            for i, values in enumerate(veri_listesi):
                values = list(values)
                while len(values) < len(MAAS_DEGISIKLIK_KOLONLARI):
                    values.append("")
                values[0] = i + 1
                self.tree.insert("", tk.END, values=tuple(values[:len(MAAS_DEGISIKLIK_KOLONLARI)]))

            messagebox.showinfo("Başarılı", f"✅ '{row[1]}' arşivinden veriler başarıyla yüklendi!")

        except Exception as e:
            log_exception_context("Arşivden getirme hatası", e)
            messagebox.showerror("Hata", f"Arşivden getirme hatası: {str(e)}")

    def arsiv_listele(self):
        if not self.kurum_id:
            messagebox.showerror("Hata", "Aktif kurum seçili değil!")
            return

        win = tk.Toplevel(self.frame)
        win.title("📋 Arşiv Listesi")
        win.geometry("600x450")
        win.transient(self.frame)
        win.grab_set()

        columns = ("id", "arsiv_adi", "donem", "tarih")
        tree = ttk.Treeview(win, columns=columns, show="headings")
        tree.heading("id", text="ID")
        tree.heading("arsiv_adi", text="Arşiv Adı")
        tree.heading("donem", text="Dönem")
        tree.heading("tarih", text="Kayıt Tarihi")

        tree.column("id", width=40, anchor="center")
        tree.column("arsiv_adi", width=200)
        tree.column("donem", width=100, anchor="center")
        tree.column("tarih", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(win, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, arsiv_adi, donem_ay_yil, olusturma_tarihi
                FROM maas_arsiv WHERE kurum_id = ? ORDER BY donem_ay_yil DESC
            """, (self.kurum_id,))
            for row in cursor.fetchall():
                tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3]))

        def on_double_click(event):
            item = tree.selection()
            if not item:
                return
            values = tree.item(item[0])["values"]
            donem = values[2]
            self.entry_arsiv_donem.delete(0, tk.END)
            self.entry_arsiv_donem.insert(0, donem)
            win.destroy()
            self.arsiv_getir()
            self.otomatik_kesinti_cek()

        tree.bind("<Double-1>", on_double_click)

        btn_frame = tk.Frame(win, bg=self.theme['bg'])
        btn_frame.pack(pady=10, fill=tk.X)

        def arsiv_sil():
            item = tree.selection()
            if not item:
                messagebox.showwarning("Uyarı", "Lütfen silinecek arşivi listeden seçin!", parent=win)
                return

            values = tree.item(item[0])["values"]
            arsiv_id = values[0]
            arsiv_adi = values[1]

            if not messagebox.askyesno("Onay",
                f"'{arsiv_adi}' adlı arşiv kaydını silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz!",
                parent=win):
                return

            try:
                with db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM maas_arsiv WHERE id = ?", (arsiv_id,))
                    conn.commit()

                tree.delete(item[0])
                messagebox.showinfo("Başarılı", "Arşiv kaydı başarıyla silindi.", parent=win)
            except Exception as e:
                messagebox.showerror("Hata", f"Silme işlemi sırasında hata oluştu:\n{str(e)}", parent=win)

        tk.Button(btn_frame, text="🗑️ Seçili Arşivi Sil", command=arsiv_sil,
                  bg="#f44336", fg="white", font=("Segoe UI", 10, "bold"), width=20).pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame, text="Kapat", command=win.destroy,
                  bg="#9E9E9E", fg="white", font=("Segoe UI", 10), width=12).pack(side=tk.RIGHT, padx=10)

    def excel_olustur(self):
        if not self.tree.get_children():
            messagebox.showerror("Hata", "Listede hiç değişiklik kaydı yok! Önce değişiklik ekleyin.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel dosyası", "*.xlsx")],
            initialfile=f"MAAŞ_BİLGİ_FORMU_{datetime.now().strftime('%Y%m')}.xlsx"
        )
        if not filepath:
            return

        try:
            with db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT kurum_adi, saymanlik_kod, vergi_no, banka_subesi, iban, amir_adi, amir_telefon
                    FROM kurum WHERE id = ?
                """, (self.kurum_id,))
                row = cursor.fetchone()

                cursor.execute("SELECT COUNT(*) FROM personel WHERE kurum_id = ? AND (aktif IS NULL OR aktif = 1)", (self.kurum_id,))
                toplam_personel_sayisi = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT veri_json FROM maas_arsiv
                    WHERE kurum_id = ? ORDER BY donem_ay_yil DESC LIMIT 1
                """, (self.kurum_id,))
                son_arsiv = cursor.fetchone()
                ucretsiz_izinli_sayisi = 0
                if son_arsiv:
                    try:
                        veri = json.loads(son_arsiv[0])
                        dondu = sum(1 for v in veri if len(v) > 20 and str(v[20]).strip().upper() == "X")
                        cikti = sum(1 for v in veri if len(v) > 21 and str(v[21]).strip().upper() == "X")
                        ucretsiz_izinli_sayisi = max(0, cikti - dondu)
                    except (json.JSONDecodeError, ValueError):
                        pass

            kurum_bilgileri = {
                'kurum_adi': row[0] if row else '',
                'saymanlik_kod': row[1] if row else '',
                'vergi_no': row[2] if row else '',
                'banka_subesi': row[3] if row else '',
                'iban': row[4] if row else '',
                'amir_adi': row[5] if row else '',
                'amir_telefon': row[6] if row else '',
                'toplam_personel_sayisi': toplam_personel_sayisi,
                'ucretsiz_izinli_sayisi': ucretsiz_izinli_sayisi,
                'donem_ay_yil': self.entry_arsiv_donem.get().strip()
            }

            onceki_aylar_listesi = []
            for entry in self.onceki_ay_entries:
                val = entry.get().strip()
                try:
                    onceki_aylar_listesi.append(int(val) if val else 0)
                except ValueError:
                    onceki_aylar_listesi.append(0)

            with db_connection() as conn_save:
                for i, deger in enumerate(onceki_aylar_listesi):
                    cursor3 = conn_save.cursor()
                    cursor3.execute("""
                        INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)
                    """, (f"onceki_ay_{i}", str(deger)))

            kurum_bilgileri['onceki_aylar'] = onceki_aylar_listesi

            veri_listesi = []
            for item in self.tree.get_children():
                veri_listesi.append(list(self.tree.item(item)['values']))

            maas_degisiklik_excel_olustur(kurum_bilgileri, veri_listesi, filepath)

            messagebox.showinfo("Başarılı", f"✅ MEB formatlı Excel raporu başarıyla oluşturuldu!\n\n📁 {filepath}")

        except Exception as e:
            log_exception_context("Rapor oluşturma hatası", e)
            messagebox.showerror("Hata", f"Rapor oluşturma hatası: {str(e)}")

    def son_aydan_devret(self):
        donem = self.entry_arsiv_donem.get().strip()
        if not donem:
            messagebox.showerror("Hata", "Lütfen önce bir dönem (Yıl-Ay) seçin!")
            return

        try:
            yil, ay = map(int, donem.split('-'))
        except (ValueError, AttributeError):
            messagebox.showerror("Hata", "Geçersiz dönem formatı! (Örn: 2026-09)")
            return

        if ay == 1:
            onceki_yil = yil - 1
            onceki_ay = 12
        else:
            onceki_yil = yil
            onceki_ay = ay - 1

        onceki_donem = f"{onceki_yil}-{onceki_ay:02d}"
        onceki_index = onceki_ay - 1
        hedef_index = ay - 1

        baz_sayi = None
        if 0 <= onceki_index < len(self.onceki_ay_entries):
            onceki_kutu_deger = self.onceki_ay_entries[onceki_index].get().strip()
            if onceki_kutu_deger:
                try:
                    baz_sayi = int(onceki_kutu_deger)
                except ValueError:
                    baz_sayi = None

        if baz_sayi is None:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT veri_json FROM maas_arsiv
                    WHERE kurum_id = ? AND donem_ay_yil = ?
                    ORDER BY id DESC LIMIT 1
                """, (self.kurum_id, onceki_donem))
                row = cursor.fetchone()

            if not row:
                messagebox.showerror("Hata",
                    f"'{onceki_donem}' kutucuğu boş ve o döneme ait arşivlenmiş veri de bulunamadı!\n\n"
                    f"Lütfen önce '{onceki_donem}' kutusuna bir değer girin ya da o dönemi arşive gönderin.")
                return

            veri_listesi_arsiv = json.loads(row[0])
            giren_arsiv = sum(1 for v in veri_listesi_arsiv if len(v) > 18 and v[18] == "X")
            cikan_arsiv = sum(1 for v in veri_listesi_arsiv if len(v) > 19 and v[19] == "X")

            with db_connection() as conn2:
                cursor2 = conn2.cursor()
                cursor2.execute("SELECT COUNT(*) FROM personel WHERE kurum_id = ? AND (aktif IS NULL OR aktif = 1)", (self.kurum_id,))
                toplam_personel = cursor2.fetchone()[0]

            baz_sayi = max(0, toplam_personel - cikan_arsiv + giren_arsiv)

        bu_ay_giren = 0
        bu_ay_cikan = 0
        for item in self.tree.get_children():
            v = self.tree.item(item)['values']
            if len(v) > 18 and str(v[18]).strip().upper() == "X":
                bu_ay_giren += 1
            if len(v) > 19 and str(v[19]).strip().upper() == "X":
                bu_ay_cikan += 1

        try:
            hedef_odeme = max(0, baz_sayi - bu_ay_cikan + bu_ay_giren)

            if 0 <= hedef_index < len(self.onceki_ay_entries):
                self.onceki_ay_entries[hedef_index].delete(0, tk.END)
                self.onceki_ay_entries[hedef_index].insert(0, str(hedef_odeme))

            messagebox.showinfo("Başarılı",
                f"✅ {onceki_donem} → {donem} devredildi!\n\n"
                f"Baz Sayı ({onceki_donem}): {baz_sayi}\n"
                f"Bu Ay Giren: {bu_ay_giren}, Bu Ay Çıkan: {bu_ay_cikan}\n"
                f"Sonuç: {hedef_odeme}"
            )
        except Exception as e:
            log_exception_context("Devretme hatası", e)
            messagebox.showerror("Hata", f"Devretme hatası: {str(e)}")

    def load_onceki_aylar(self):
        try:
            with db_connection() as conn:
                for i, entry in enumerate(self.onceki_ay_entries):
                    cursor = conn.cursor()
                    cursor.execute("SELECT deger FROM ayarlar WHERE anahtar = ?", (f"onceki_ay_{i}",))
                    row = cursor.fetchone()
                    if row:
                        try:
                            deger = int(row[0])
                        except (ValueError, TypeError):
                            deger = 0
                        if deger >= 0:
                            entry.delete(0, tk.END)
                            if deger > 0:
                                entry.insert(0, str(deger))
        except Exception:
            pass

    def kaydet_onceki_aylar(self):
        try:
            with db_connection() as conn:
                for i, entry in enumerate(self.onceki_ay_entries):
                    val = entry.get().strip()
                    if val == "":
                        deger = "0"
                    else:
                        try:
                            deger = str(int(val))
                        except ValueError:
                            deger = "0"

                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)
                    """, (f"onceki_ay_{i}", deger))

            messagebox.showinfo("Başarılı", "✅ Önceki aylar verileri başarıyla kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Kayıt hatası: {str(e)}")