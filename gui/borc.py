# gui/borc.py - Borç işlemleri ekranı (V.3.2.0)

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import db_connection
from utils.base_page import BasePage
from utils.helpers import parse_float, parse_id_from_secim, personel_listesi_yukle, format_tl


class BorcIslemleri(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.selected_borc_id = None
        self.selected_personel_id = None
        self.create_widgets()
        self.load_personel_list()
        self.apply_theme(self.theme)

    def create_widgets(self):
        theme = self.theme
        self.frame = tk.Frame(self.parent, bg=theme['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title = tk.Label(self.frame, text="📄 BORÇ İŞLEMLERİ",
                         font=("Arial", 16, "bold"), fg="blue", bg=theme['bg'])
        title.grid(row=0, column=0, columnspan=4, pady=10)

        tk.Label(self.frame, text="Personel Seçin:*", font=("Arial", 10), bg=theme['bg']).grid(row=1, column=0, sticky="w", pady=5)
        self.personel_combobox = ttk.Combobox(self.frame, width=40)
        self.personel_combobox.grid(row=1, column=1, columnspan=2, pady=5, sticky="w")
        self.personel_combobox.bind("<<ComboboxSelected>>", self.personel_sec)

        tk.Label(self.frame, text="Borç Türü:*", font=("Arial", 10), bg=theme['bg']).grid(row=2, column=0, sticky="w", pady=5)
        self.tur_combobox = ttk.Combobox(self.frame, width=15, state="readonly", values=["İcra", "Nafaka"])
        self.tur_combobox.set("İcra")
        self.tur_combobox.grid(row=2, column=1, pady=5, sticky="w")
        self.tur_combobox.bind("<<ComboboxSelected>>", self.tur_degisti)

        self.lbl_nafaka_tutari = tk.Label(self.frame, text="Aylık Nafaka Tutarı:*", font=("Arial", 10), bg=theme['bg'])
        self.entry_nafaka_tutari = tk.Entry(self.frame, width=20)
        self.lbl_nafaka_tutari.grid(row=2, column=2, sticky="w", pady=5)
        self.entry_nafaka_tutari.grid(row=2, column=3, pady=5, sticky="w")
        self.lbl_nafaka_tutari.grid_remove()
        self.entry_nafaka_tutari.grid_remove()

        tk.Label(self.frame, text="İcra Dairesi Adı:*", font=("Arial", 10), bg=theme['bg']).grid(row=3, column=0, sticky="w", pady=5)
        self.entry_daire = tk.Entry(self.frame, width=30)
        self.entry_daire.grid(row=3, column=1, pady=5, sticky="w")

        tk.Label(self.frame, text="Dosya No:*", font=("Arial", 10), bg=theme['bg']).grid(row=4, column=0, sticky="w", pady=5)
        self.entry_dosya = tk.Entry(self.frame, width=30)
        self.entry_dosya.grid(row=4, column=1, pady=5, sticky="w")

        tk.Label(self.frame, text="Toplam Borç:*", font=("Arial", 10), bg=theme['bg']).grid(row=5, column=0, sticky="w", pady=5)
        self.entry_borc = tk.Entry(self.frame, width=20)
        self.entry_borc.grid(row=5, column=1, pady=5, sticky="w")

        tk.Label(self.frame, text="Daha Önce Yapılan Kesinti:", font=("Arial", 10), bg=theme['bg']).grid(row=3, column=2, sticky="w", pady=5)
        self.entry_onceki_kesinti = tk.Entry(self.frame, width=20)
        self.entry_onceki_kesinti.grid(row=3, column=3, pady=5, sticky="w")
        self.entry_onceki_kesinti.insert(0, "0")

        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=6, column=0, columnspan=4, pady=15)

        self.btn_ekle = tk.Button(button_frame, text="➕ Ekle", command=self.ekle,
                                  font=("Arial", 10), bg="#4CAF50", fg="white", width=12)
        self.btn_ekle.pack(side=tk.LEFT, padx=5)

        self.btn_guncelle = tk.Button(button_frame, text="✏️ Güncelle", command=self.guncelle,
                                      font=("Arial", 10), bg="#FFC107", width=12)
        self.btn_guncelle.pack(side=tk.LEFT, padx=5)

        self.btn_sil = tk.Button(button_frame, text="🗑️ Sil", command=self.sil,
                                 font=("Arial", 10), bg="#f44336", fg="white", width=12)
        self.btn_sil.pack(side=tk.LEFT, padx=5)

        self.btn_temizle = tk.Button(button_frame, text="🧹 Temizle", command=self.temizle,
                                     font=("Arial", 10), bg="#9E9E9E", fg="white", width=12)
        self.btn_temizle.pack(side=tk.LEFT, padx=5)

        self.btn_yenile = tk.Button(button_frame, text="🔄 Yenile", command=self.load_borc_list,
                                    font=("Arial", 10), bg="#2196F3", fg="white", width=12)
        self.btn_yenile.pack(side=tk.LEFT, padx=5)

        tk.Label(self.frame, text="Kayıtlı Borçlar:", font=("Arial", 10, "bold"), bg=theme['bg']).grid(row=7, column=0, columnspan=4, pady=10)

        columns = ("id", "personel", "tur", "icra_daire", "dosya_no", "onceki_kesinti", "toplam_borc")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=10)

        self.tree.heading("id", text="ID")
        self.tree.heading("personel", text="Personel")
        self.tree.heading("tur", text="Tür")
        self.tree.heading("icra_daire", text="İcra Dairesi")
        self.tree.heading("dosya_no", text="Dosya No")
        self.tree.heading("onceki_kesinti", text="Önceki Kesinti")
        self.tree.heading("toplam_borc", text="Toplam Borç")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("personel", width=150)
        self.tree.column("tur", width=70, anchor="center")
        self.tree.column("icra_daire", width=180)
        self.tree.column("dosya_no", width=130, anchor="center")
        self.tree.column("onceki_kesinti", width=120, anchor="e")
        self.tree.column("toplam_borc", width=140, anchor="e")

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=8, column=0, columnspan=3, sticky="nsew")
        scrollbar.grid(row=8, column=3, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self.tree_sec)

        self.frame.grid_rowconfigure(8, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(3, weight=1)

    def tur_degisti(self, event=None):
        if self.tur_combobox.get() == "Nafaka":
            self.lbl_nafaka_tutari.grid()
            self.entry_nafaka_tutari.grid()
        else:
            self.lbl_nafaka_tutari.grid_remove()
            self.entry_nafaka_tutari.grid_remove()
            self.entry_nafaka_tutari.delete(0, tk.END)

    def load_personel_list(self):
        self.personel_listesi = personel_listesi_yukle(self.personel_combobox)
        if self.personel_listesi:
            self.personel_sec()

    def personel_sec(self, event=None):
        secim = self.personel_combobox.get()
        self.selected_personel_id = parse_id_from_secim(secim)
        if self.selected_personel_id is None:
            if secim:
                messagebox.showerror("Hata", "Geçersiz personel seçimi!")
            return
        self.load_borc_list()

    def load_borc_list(self):
        if not self.selected_personel_id:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.id, p.ad_soyad, b.icra_daire_adi, b.dosya_no, b.toplam_borc,
                       b.borc_turu, b.aylik_nafaka_tutari, b.onceki_kesinti
                FROM borc b
                JOIN personel p ON p.id = b.personel_id
                WHERE b.personel_id = ?
                ORDER BY b.id DESC
            """, (self.selected_personel_id,))

            for row in cursor.fetchall():
                tur = row[5] or 'icra'
                tur_gosterim = "Nafaka" if tur == 'nafaka' else "İcra"
                self.tree.insert("", tk.END, values=(
                    row[0], row[1], tur_gosterim, row[2] or '', row[3] or '',
                    format_tl(row[7] or 0),
                    format_tl(row[4] or 0)
                ))

    def temizle(self):
        self.entry_daire.delete(0, tk.END)
        self.entry_dosya.delete(0, tk.END)
        self.entry_borc.delete(0, tk.END)
        self.entry_onceki_kesinti.delete(0, tk.END)
        self.entry_onceki_kesinti.insert(0, "0")
        self.entry_nafaka_tutari.delete(0, tk.END)
        self.tur_combobox.set("İcra")
        self.tur_degisti()
        self.selected_borc_id = None

    def get_borc_turu_ve_tutar(self):
        tur_gosterim = self.tur_combobox.get()
        tur = 'nafaka' if tur_gosterim == 'Nafaka' else 'icra'

        if tur == 'icra':
            return tur, 0.0

        tutar = parse_float(self.entry_nafaka_tutari.get())
        if tutar is None:
            messagebox.showerror("Hata", "Nafaka borcunda geçerli bir Aylık Nafaka Tutarı giriniz!")
            return None
        if tutar <= 0:
            messagebox.showerror("Hata", "Aylık nafaka tutarı 0'dan büyük olmalıdır!")
            return None
        return tur, tutar

    def ekle(self):
        if not self.selected_personel_id:
            messagebox.showerror("Hata", "Lütfen bir personel seçin!")
            return

        daire = self.entry_daire.get().strip()
        dosya = self.entry_dosya.get().strip()

        if not daire:
            messagebox.showerror("Hata", "İcra Dairesi alanı zorunludur!")
            return

        if not dosya:
            messagebox.showerror("Hata", "Dosya No alanı zorunludur!")
            return

        borc = parse_float(self.entry_borc.get())
        if borc is None:
            messagebox.showerror("Hata", "Geçerli bir borç miktarı giriniz!")
            return

        onceki_kesinti = parse_float(self.entry_onceki_kesinti.get())
        if onceki_kesinti is None:
            onceki_kesinti = 0.0

        turu_ve_tutar = self.get_borc_turu_ve_tutar()
        if turu_ve_tutar is None:
            return
        borc_turu, nafaka_tutari = turu_ve_tutar

        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO borc (personel_id, icra_daire_adi, dosya_no, toplam_borc, onceki_kesinti, borc_turu, aylik_nafaka_tutari)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (self.selected_personel_id, daire, dosya, borc, onceki_kesinti, borc_turu, nafaka_tutari))

            messagebox.showinfo("Başarılı", "Borç başarıyla eklendi!")
            self.temizle()
            self.load_borc_list()

        except Exception as e:
            messagebox.showerror("Hata", f"Kayıt hatası: {str(e)}")

    def guncelle(self):
        if not self.selected_borc_id:
            messagebox.showerror("Hata", "Lütfen güncellenecek borcu seçin!")
            return

        daire = self.entry_daire.get().strip()
        dosya = self.entry_dosya.get().strip()

        if not daire:
            messagebox.showerror("Hata", "İcra Dairesi alanı zorunludur!")
            return

        if not dosya:
            messagebox.showerror("Hata", "Dosya No alanı zorunludur!")
            return

        borc = parse_float(self.entry_borc.get())
        if borc is None:
            messagebox.showerror("Hata", "Geçerli bir borç miktarı giriniz!")
            return

        onceki_kesinti = parse_float(self.entry_onceki_kesinti.get())
        if onceki_kesinti is None:
            onceki_kesinti = 0.0

        turu_ve_tutar = self.get_borc_turu_ve_tutar()
        if turu_ve_tutar is None:
            return
        borc_turu, nafaka_tutari = turu_ve_tutar

        if not messagebox.askyesno("Onay", "Bu borç bilgisini güncellemek istediğinize emin misiniz?"):
            return

        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE borc
                    SET icra_daire_adi = ?, dosya_no = ?, toplam_borc = ?, onceki_kesinti = ?, borc_turu = ?, aylik_nafaka_tutari = ?
                    WHERE id = ?
                """, (daire, dosya, borc, onceki_kesinti, borc_turu, nafaka_tutari, self.selected_borc_id))

            messagebox.showinfo("Başarılı", "Borç başarıyla güncellendi!")
            self.temizle()
            self.load_borc_list()

        except Exception as e:
            messagebox.showerror("Hata", f"Güncelleme hatası: {str(e)}")

    def sil(self):
        if not self.selected_borc_id:
            messagebox.showerror("Hata", "Lütfen silinecek borcu seçin!")
            return

        if not messagebox.askyesno("Onay", "Bu borç kaydını silmek istediğinize emin misiniz?\n\n⚠️ İlişkili kesinti kayıtları da silinecektir!"):
            return

        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM kesinti_takip WHERE borc_id = ?", (self.selected_borc_id,))
                cursor.execute("DELETE FROM borc WHERE id = ?", (self.selected_borc_id,))

            messagebox.showinfo("Başarılı", "Borç başarıyla silindi!")
            self.temizle()
            self.load_borc_list()

        except Exception as e:
            messagebox.showerror("Hata", f"Silme hatası: {str(e)}")

    def tree_sec(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0])["values"]
        if not values:
            return

        self.selected_borc_id = values[0]

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT icra_daire_adi, dosya_no, toplam_borc, onceki_kesinti, borc_turu, aylik_nafaka_tutari
                FROM borc
                WHERE id = ?
            """, (self.selected_borc_id,))
            row = cursor.fetchone()

        if row:
            self.entry_daire.delete(0, tk.END)
            self.entry_daire.insert(0, row[0] or '')

            self.entry_dosya.delete(0, tk.END)
            self.entry_dosya.insert(0, row[1] or '')

            self.entry_borc.delete(0, tk.END)
            self.entry_borc.insert(0, f"{(row[2] or 0):.2f}")

            self.entry_onceki_kesinti.delete(0, tk.END)
            self.entry_onceki_kesinti.insert(0, f"{(row[3] or 0):.2f}")

            tur = row[4] or 'icra'
            self.tur_combobox.set("Nafaka" if tur == 'nafaka' else "İcra")
            self.tur_degisti()
            if tur == 'nafaka':
                self.entry_nafaka_tutari.delete(0, tk.END)
                self.entry_nafaka_tutari.insert(0, f"{(row[5] or 0):.2f}")