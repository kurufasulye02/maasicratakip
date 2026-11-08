# gui/maas.py - Maaş kalemleri işlemleri (V.2.1)

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import db_connection
from utils.base_page import BasePage
# DÜZELTME: format_tl eklendi
from utils.helpers import parse_float, parse_id_from_secim, personel_listesi_yukle, get_aylar, format_tl
from utils.logger import log_exception_context


class MaasIslemleri(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.selected_personel_id = None
        self.selected_maas_id = None
        self.create_widgets()
        self.load_personel_list()
        self.apply_theme(self.theme)

    def create_widgets(self):
        theme = self.theme

        self.frame = tk.Frame(self.parent, bg=theme['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        title = tk.Label(self.frame, text="💰 MAAŞ KALEMLERİ",
                         font=("Segoe UI", 16, "bold"), fg="#1a237e", bg=theme['bg'])
        title.grid(row=0, column=0, columnspan=6, pady=10)

        desc = tk.Label(self.frame,
                        text="Sadece değişiklik olduğunda yeni maaş kaydı ekleyin. Sistem otomatik olarak en yakın tarihli maaşı kullanır.",
                        font=("Segoe UI", 9), fg=theme['label_secondary'], bg=theme['bg'])
        desc.grid(row=1, column=0, columnspan=6, pady=(0, 15))

        tk.Label(self.frame, text="Personel Seçin:*", font=("Segoe UI", 10, "bold"),
                 bg=theme['bg'], fg=theme['fg']).grid(row=2, column=0, sticky="w", pady=5)
        self.personel_combobox = ttk.Combobox(self.frame, width=35, font=("Segoe UI", 10))
        self.personel_combobox.grid(row=2, column=1, columnspan=2, pady=5, sticky="w")
        self.personel_combobox.bind("<<ComboboxSelected>>", self.personel_sec)

        tk.Label(self.frame, text="Başlangıç Ayı:*", font=("Segoe UI", 10, "bold"),
                 bg=theme['bg'], fg=theme['fg']).grid(row=2, column=3, sticky="w", pady=5)
        self.baslangic_combobox = ttk.Combobox(self.frame, width=15, font=("Segoe UI", 10))
        self.baslangic_combobox.grid(row=2, column=4, pady=5, sticky="w")
        self.baslangic_combobox['values'] = get_aylar()
        self.baslangic_combobox.set(datetime.now().strftime("%Y-%m"))

        tk.Label(self.frame, text="Bitiş Ayı:", font=("Segoe UI", 10),
                 bg=theme['bg'], fg=theme['fg']).grid(row=3, column=3, sticky="w", pady=5)
        self.bitis_combobox = ttk.Combobox(self.frame, width=15, font=("Segoe UI", 10))
        self.bitis_combobox.grid(row=3, column=4, pady=5, sticky="w")
        self.bitis_combobox['values'] = [""] + get_aylar()

        row = 4
        kalemler = [
            ("Aylık Tutar", "aylik_tutar"),
            ("Taban Aylık", "taban_aylik"),
            ("Ek Gösterge", "ek_gosterge"),
            ("Yan Ödeme", "yan_odeme"),
            ("Kıdem Aylık", "kidem"),
            ("Özel Hizmet Tazminatı", "ozel_hizmet")
        ]

        for label, key in kalemler:
            tk.Label(self.frame, text=f"{label}:", font=("Segoe UI", 10),
                     bg=theme['bg'], fg=theme['fg']).grid(row=row, column=0, sticky="e", pady=3, padx=5)
            entry = tk.Entry(self.frame, width=20, font=("Segoe UI", 10),
                             bg=theme['entry_bg'], fg=theme['entry_fg'], relief=tk.SOLID, bd=1)
            entry.grid(row=row, column=1, pady=3, sticky="w", padx=5)
            setattr(self, f"entry_{key}", entry)
            row += 1

        row = 4
        kalemler2 = [
            ("Makam Tazminatı", "makam"),
            ("Dil Tazminatı", "dil"),
            ("Ek Ödeme 666", "ek_odeme_666"),
            ("Ek Tazminat", "ek_tazminat"),
            ("İlave Ödeme", "ilave_odeme")
        ]

        for label, key in kalemler2:
            tk.Label(self.frame, text=f"{label}:", font=("Segoe UI", 10),
                     bg=theme['bg'], fg=theme['fg']).grid(row=row, column=2, sticky="e", pady=3, padx=5)
            entry = tk.Entry(self.frame, width=20, font=("Segoe UI", 10),
                             bg=theme['entry_bg'], fg=theme['entry_fg'], relief=tk.SOLID, bd=1)
            entry.grid(row=row, column=3, pady=3, sticky="w", padx=5)
            setattr(self, f"entry_{key}", entry)
            row += 1

        row = 14
        tk.Label(self.frame, text="TOPLAM MAAŞ:", font=("Segoe UI", 11, "bold"),
                 bg=theme['bg'], fg=theme['fg']).grid(row=row, column=0, sticky="e", pady=5)
        self.lbl_toplam = tk.Label(self.frame, text="0.00 TL", font=("Segoe UI", 11, "bold"),
                                   fg="green", bg=theme['bg'])
        self.lbl_toplam.grid(row=row, column=1, sticky="w", pady=5)

        tk.Label(self.frame, text="HACİZ TUTARI (1/4):", font=("Segoe UI", 11, "bold"),
                 bg=theme['bg'], fg=theme['fg']).grid(row=row, column=2, sticky="e", pady=5)
        self.lbl_haciz = tk.Label(self.frame, text="0.00 TL", font=("Segoe UI", 11, "bold"),
                                  fg="red", bg=theme['bg'])
        self.lbl_haciz.grid(row=row, column=3, sticky="w", pady=5)

        button_frame = tk.Frame(self.frame, bg=theme['bg'])
        button_frame.grid(row=15, column=0, columnspan=6, pady=15)

        self.btn_hesapla = tk.Button(button_frame, text="🧮 Hesapla", command=self.hesapla,
                                     font=("Segoe UI", 10, "bold"), bg="#2196F3", fg="white",
                                     width=12, height=1, relief=tk.RAISED, bd=2, cursor="hand2")
        self.btn_hesapla.pack(side=tk.LEFT, padx=5)

        self.btn_kaydet = tk.Button(button_frame, text="💾 Kaydet", command=self.kaydet,
                                    font=("Segoe UI", 10, "bold"), bg="#4CAF50", fg="white",
                                    width=12, height=1, relief=tk.RAISED, bd=2, cursor="hand2")
        self.btn_kaydet.pack(side=tk.LEFT, padx=5)

        self.btn_temizle = tk.Button(button_frame, text="🧹 Temizle", command=self.temizle,
                                     font=("Segoe UI", 10, "bold"), bg="#9E9E9E", fg="white",
                                     width=12, height=1, relief=tk.RAISED, bd=2, cursor="hand2")
        self.btn_temizle.pack(side=tk.LEFT, padx=5)

        self.btn_yenile = tk.Button(button_frame, text="🔄 Yenile", command=self.load_personel_list,
                                    font=("Segoe UI", 10, "bold"), bg="#FF9800", fg="white",
                                    width=12, height=1, relief=tk.RAISED, bd=2, cursor="hand2")
        self.btn_yenile.pack(side=tk.LEFT, padx=5)

        self.btn_sil = tk.Button(button_frame, text="🗑️ Sil", command=self.sil,
                                 font=("Segoe UI", 10, "bold"), bg="#f44336", fg="white",
                                 width=12, height=1, relief=tk.RAISED, bd=2, cursor="hand2")
        self.btn_sil.pack(side=tk.LEFT, padx=5)

        tk.Label(self.frame, text="Kayıtlı Maaş Bilgileri (Tarihli):", font=("Segoe UI", 10, "bold"),
                 bg=theme['bg'], fg=theme['fg']).grid(row=16, column=0, columnspan=6, pady=10)

        columns = ("id", "baslangic", "bitis", "toplam", "haciz", "durum")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=6)

        self.tree.heading("id", text="ID")
        self.tree.heading("baslangic", text="Başlangıç")
        self.tree.heading("bitis", text="Bitiş")
        self.tree.heading("toplam", text="Toplam Maaş")
        self.tree.heading("haciz", text="Haciz (1/4)")
        self.tree.heading("durum", text="Durum")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("baslangic", width=80, anchor="center")
        self.tree.column("bitis", width=80, anchor="center")
        self.tree.column("toplam", width=120, anchor="e")
        self.tree.column("haciz", width=120, anchor="e")
        self.tree.column("durum", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=17, column=0, columnspan=5, sticky="nsew")
        scrollbar.grid(row=17, column=5, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self.tree_sec)

        self.frame.grid_rowconfigure(17, weight=1)
        for col in range(6):
            self.frame.grid_columnconfigure(col, weight=1)

        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(3, weight=1)

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

        self.load_maas_kayitlari()
        self.temizle()

    def load_maas_kayitlari(self):
        if not self.selected_personel_id:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, baslangic_ay, bitis_ay, 
                       aylik_tutar + taban_aylik + ek_gosterge + yan_odeme + kidem + ozel_hizmet + 
                       makam + dil + ek_odeme_666 + ek_tazminat + ilave_odeme as toplam,
                       (aylik_tutar + taban_aylik + ek_gosterge + yan_odeme + kidem + ozel_hizmet + 
                        makam + dil + ek_odeme_666 + ek_tazminat + ilave_odeme) / 4 as haciz
                FROM maas_kalemleri
                WHERE personel_id = ?
                ORDER BY baslangic_ay DESC
            """, (self.selected_personel_id,))

            for row in cursor.fetchall():
                durum = "Aktif" if row[2] is None else "Pasif"
                self.tree.insert("", tk.END, values=(
                    row[0], row[1], row[2] or "-",
                    format_tl(row[3] or 0),
                    format_tl(row[4] or 0),
                    durum
                ))

    def hesapla(self):
        toplam = 0
        kalemler = [
            'aylik_tutar', 'taban_aylik', 'ek_gosterge', 'yan_odeme', 'kidem',
            'ozel_hizmet', 'makam', 'dil', 'ek_odeme_666',
            'ek_tazminat', 'ilave_odeme'
        ]

        for key in kalemler:
            entry = getattr(self, f"entry_{key}")
            metin = entry.get().strip()
            if not metin:
                continue
            deger = parse_float(metin)
            if deger is None:
                messagebox.showerror("Hata", "Lütfen geçerli sayılar giriniz!")
                return
            toplam += deger

        haciz = toplam / 4
        self.lbl_toplam.config(text=format_tl(toplam))
        self.lbl_haciz.config(text=format_tl(haciz))

    def kaydet(self):
        if not self.selected_personel_id:
            messagebox.showerror("Hata", "Lütfen bir personel seçin!")
            return

        baslangic = self.baslangic_combobox.get()
        if not baslangic:
            messagebox.showerror("Hata", "Lütfen başlangıç ayı seçin!")
            return

        bitis = self.bitis_combobox.get() or None

        if bitis and bitis < baslangic:
            messagebox.showerror("Hata",
                f"Bitiş ayı ({bitis}) başlangıç ayından ({baslangic}) önce olamaz!")
            return

        kalem_entries = {
            'aylik_tutar': self.entry_aylik_tutar,
            'taban_aylik': self.entry_taban_aylik,
            'ek_gosterge': self.entry_ek_gosterge,
            'yan_odeme': self.entry_yan_odeme,
            'kidem': self.entry_kidem,
            'ozel_hizmet': self.entry_ozel_hizmet,
            'makam': self.entry_makam,
            'dil': self.entry_dil,
            'ek_odeme_666': self.entry_ek_odeme_666,
            'ek_tazminat': self.entry_ek_tazminat,
            'ilave_odeme': self.entry_ilave_odeme
        }

        kalemler = {}
        for key, entry in kalem_entries.items():
            metin = entry.get().strip()
            if metin == '':
                kalemler[key] = 0.0
                continue
            deger = parse_float(metin)
            if deger is None:
                messagebox.showerror("Hata", "Lütfen tüm alanlara geçerli sayı giriniz!")
                return
            kalemler[key] = deger

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM maas_kalemleri
                WHERE personel_id = ? AND baslangic_ay = ?
            """, (self.selected_personel_id, baslangic))

            var = cursor.fetchone()

            if var:
                cursor.execute("""
                    UPDATE maas_kalemleri
                    SET bitis_ay = ?, aylik_tutar = ?, taban_aylik = ?, ek_gosterge = ?, yan_odeme = ?, kidem = ?,
                        ozel_hizmet = ?, makam = ?, dil = ?, ek_odeme_666 = ?,
                        ek_tazminat = ?, ilave_odeme = ?
                    WHERE id = ?
                """, (
                    bitis,
                    kalemler['aylik_tutar'], kalemler['taban_aylik'],
                    kalemler['ek_gosterge'], kalemler['yan_odeme'], kalemler['kidem'],
                    kalemler['ozel_hizmet'], kalemler['makam'],
                    kalemler['dil'], kalemler['ek_odeme_666'],
                    kalemler['ek_tazminat'], kalemler['ilave_odeme'],
                    var[0]
                ))
                mesaj = "Maaş bilgileri güncellendi!"
            else:
                cursor.execute("""
                    INSERT INTO maas_kalemleri 
                    (personel_id, baslangic_ay, bitis_ay, aylik_tutar, taban_aylik, ek_gosterge, yan_odeme, 
                     kidem, ozel_hizmet, makam, dil, ek_odeme_666, ek_tazminat, ilave_odeme)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.selected_personel_id, baslangic, bitis,
                    kalemler['aylik_tutar'], kalemler['taban_aylik'],
                    kalemler['ek_gosterge'], kalemler['yan_odeme'],
                    kalemler['kidem'], kalemler['ozel_hizmet'],
                    kalemler['makam'], kalemler['dil'],
                    kalemler['ek_odeme_666'], kalemler['ek_tazminat'],
                    kalemler['ilave_odeme']
                ))
                mesaj = "Maaş bilgileri kaydedildi!"

            conn.commit()

        messagebox.showinfo("Başarılı", mesaj)
        self.load_maas_kayitlari()
        self.temizle()

    def temizle(self):
        kalemler = [
            'aylik_tutar', 'taban_aylik', 'ek_gosterge', 'yan_odeme', 'kidem',
            'ozel_hizmet', 'makam', 'dil', 'ek_odeme_666',
            'ek_tazminat', 'ilave_odeme'
        ]

        for key in kalemler:
            entry = getattr(self, f"entry_{key}")
            entry.delete(0, tk.END)

        self.lbl_toplam.config(text="0.00 TL")
        self.lbl_haciz.config(text="0.00 TL")
        self.bitis_combobox.set("")
        self.selected_maas_id = None

    def sil(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Hata", "Lütfen silinecek maaş kaydını listeden seçin!")
            return

        values = self.tree.item(selection[0])["values"]
        if not values:
            messagebox.showerror("Hata", "Seçili kayıt geçersiz!")
            return

        self.selected_maas_id = values[0]
        baslangic = values[1] if len(values) > 1 else "?"
        bitis = values[2] if len(values) > 2 and values[2] != "-" else "-"

        if not messagebox.askyesno(
            "Onay",
            f"Seçili maaş kaydını silmek istediğinize emin misiniz?\n\n"
            f"Başlangıç: {baslangic}\n"
            f"Bitiş: {bitis}"
        ):
            return

        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM maas_kalemleri WHERE id = ?", (self.selected_maas_id,))
            messagebox.showinfo("Başarılı", "Maaş kaydı silindi.")
            self.temizle()
            self.load_maas_kayitlari()
        except Exception as e:
            log_exception_context("Maaş kaydı silme hatası", e)
            messagebox.showerror("Hata", f"Silme hatası: {str(e)}")

    def tree_sec(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0])["values"]
        if not values:
            return

        maas_id = values[0]
        self.selected_maas_id = maas_id
        baslangic = values[1]
        bitis = values[2] if values[2] != "-" else ""

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT aylik_tutar, taban_aylik, ek_gosterge, yan_odeme, kidem, ozel_hizmet,
                       makam, dil, ek_odeme_666, ek_tazminat, ilave_odeme
                FROM maas_kalemleri
                WHERE id = ?
            """, (maas_id,))
            row = cursor.fetchone()

        if row:
            self.temizle()
            self.baslangic_combobox.set(baslangic)
            self.bitis_combobox.set(bitis)

            kalemler = [
                'aylik_tutar', 'taban_aylik', 'ek_gosterge', 'yan_odeme', 'kidem',
                'ozel_hizmet', 'makam', 'dil', 'ek_odeme_666',
                'ek_tazminat', 'ilave_odeme'
            ]

            for i, key in enumerate(kalemler):
                entry = getattr(self, f"entry_{key}")
                # Giriş kutuları için ondalık nokta (.) kullanıyoruz (parse_float zaten virgülü de kabul ediyor)
                entry.insert(0, f"{(row[i] or 0):.2f}")

            self.hesapla()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x600")
    app = MaasIslemleri(root)
    root.mainloop()