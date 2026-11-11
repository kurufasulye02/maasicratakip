# gui/kurum.py - Kurum bilgileri ekranı (V.3.2.0)

import tkinter as tk
from tkinter import ttk, messagebox

from database import db_connection
from utils.base_page import BasePage
from utils.db_repo import get_kurum_list, count_personel_for_kurum
from utils.kurum_context import KurumContext


class KurumIslemleri(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.kurum_id = None
        self.create_widgets()
        self.listele()
        self.apply_theme(self.theme)

    def create_widgets(self):
        theme = self.theme
        self.frame = tk.Frame(self.parent, bg=theme['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.styled_label(self.frame, "KURUM BILGILERI", title=True, font_size=18).grid(
            row=0, column=0, columnspan=2, pady=(0, 5))
        self.styled_label(
            self.frame,
            "Birden fazla kurum ekleyebilir, listeden secip duzenleyebilirsiniz.",
            secondary=True
        ).grid(row=1, column=0, columnspan=2, pady=(0, 15))

        form = tk.Frame(self.frame, bg=theme['bg'])
        form.grid(row=2, column=0, sticky="nsew", padx=(0, 15))

        fields = [
            ("KURUM / BIRIM ADI:*", "entry_kurum_adi", 55, None),
            ("KURUM KODU:*", "entry_kurum_kodu", 30, None),
            ("KURUM VERGI NO:*", "entry_vergi_no", 30, None),
            ("AMIR ADI SOYADI:*", "entry_amir_adi", 40, None),
            ("AMIR GOREVI:*", "entry_amir_unvan", 30, "MÜDÜR"),
        ]
        for i, (label, attr, width, default) in enumerate(fields):
            self.styled_label(form, label, bold=True).grid(row=i, column=0, sticky="e", pady=6, padx=5)
            entry = self.styled_entry(form, width=width)
            entry.grid(row=i, column=1, sticky="w", pady=6)
            if default:
                entry.insert(0, default)
            setattr(self, attr, entry)

        self.styled_label(form, "SAYMANLIK KURUM KODU:", bold=True).grid(row=5, column=0, sticky="e", pady=6, padx=5)
        self.entry_saymanlik_kod = self.styled_entry(form, width=30)
        self.entry_saymanlik_kod.grid(row=5, column=1, sticky="w", pady=6)
        self._set_placeholder(self.entry_saymanlik_kod, "13.01.31.62-303")

        self.styled_label(form, "BANKA ŞUBESİ:", bold=True).grid(row=6, column=0, sticky="e", pady=6, padx=5)
        self.entry_banka_subesi = self.styled_entry(form, width=40)
        self.entry_banka_subesi.grid(row=6, column=1, sticky="w", pady=6)

        self.styled_label(form, "IBAN NO:", bold=True).grid(row=7, column=0, sticky="e", pady=6, padx=5)
        self.entry_iban = self.styled_entry(form, width=50)
        self.entry_iban.grid(row=7, column=1, sticky="w", pady=6)
        self._set_placeholder(self.entry_iban, "TR__ ____ ____ ____ ____ ____ __")

        self.styled_label(form, "AMİR TELEFON NO:", bold=True).grid(row=8, column=0, sticky="e", pady=6, padx=5)
        self.entry_amir_telefon = self.styled_entry(form, width=20)
        self.entry_amir_telefon.grid(row=8, column=1, sticky="w", pady=6)
        self._set_placeholder(self.entry_amir_telefon, "05__ _______")

        btn_frame = tk.Frame(form, bg=theme['bg'])
        btn_frame.grid(row=9, column=0, columnspan=2, pady=15)
        self.styled_button(btn_frame, "Kaydet", self.kaydet, 'primary', 14).pack(side=tk.LEFT, padx=4)
        self.styled_button(btn_frame, "Guncelle", self.guncelle, 'warning', 14).pack(side=tk.LEFT, padx=4)
        self.styled_button(btn_frame, "Temizle", self.temizle, 'gray', 14).pack(side=tk.LEFT, padx=4)
        self.styled_button(btn_frame, "Sil", self.sil, 'danger', 14).pack(side=tk.LEFT, padx=4)
        self.styled_button(btn_frame, "Aktif Kurum Yap", self.aktif_yap, 'secondary', 16).pack(side=tk.LEFT, padx=4)

        list_frame = ttk.LabelFrame(self.frame, text="Kayitli Kurumlar", padding=10)
        list_frame.grid(row=2, column=1, sticky="nsew")

        columns = ("id", "kurum_adi", "kurum_kodu", "amir")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=14)
        self.tree.heading("id", text="ID")
        self.tree.heading("kurum_adi", text="Kurum Adi")
        self.tree.heading("kurum_kodu", text="Kod")
        self.tree.heading("amir", text="Amir")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("kurum_adi", width=200)
        self.tree.column("kurum_kodu", width=80, anchor="center")
        self.tree.column("amir", width=140)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.tree_sec)

        self.lbl_aktif = self.styled_label(self.frame, "", secondary=True)
        self.lbl_aktif.grid(row=3, column=0, columnspan=2, pady=(10, 0), sticky="w")

        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)

    def _set_placeholder(self, entry, placeholder_text):
        entry.placeholder = placeholder_text
        entry.insert(0, placeholder_text)
        entry.config(fg="gray")

        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END)
                entry.config(fg=self.theme['entry_fg'])

        def on_focus_out(event):
            if entry.get().strip() == "":
                entry.insert(0, placeholder_text)
                entry.config(fg="gray")

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def _clean(self, entry):
        """Placeholder metni varsa boş döndürür. (V.2.0 düzeltmesi)"""
        val = entry.get().strip()
        if hasattr(entry, 'placeholder') and val == entry.placeholder:
            return ""
        return val

    def _form_values(self):
        return {
            'kurum_adi': self.entry_kurum_adi.get().strip(),
            'kurum_kodu': self.entry_kurum_kodu.get().strip(),
            'vergi_no': self.entry_vergi_no.get().strip(),
            'amir_adi': self.entry_amir_adi.get().strip(),
            'amir_unvan': self.entry_amir_unvan.get().strip() or "MÜDÜR",
            'saymanlik_kod': self._clean(self.entry_saymanlik_kod),
            'banka_subesi': self.entry_banka_subesi.get().strip(),
            'iban': self._clean(self.entry_iban),
            'amir_telefon': self._clean(self.entry_amir_telefon),
        }

    def _validate(self, data):
        required = [
            ('kurum_adi', 'Kurum / Birim Adi'),
            ('kurum_kodu', 'Kurum Kodu'),
            ('vergi_no', 'Kurum Vergi No'),
            ('amir_adi', 'Amir Adi Soyadi'),
        ]
        for key, label in required:
            if not data[key]:
                messagebox.showerror("Hata", f"{label} zorunludur!")
                return False
        return True

    def listele(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        aktif_id = KurumContext.get_active_id()
        for k in get_kurum_list():
            tag = ()
            if k['id'] == aktif_id:
                tag = ('aktif',)
            self.tree.insert("", tk.END, values=(
                k['id'], k['kurum_adi'] or '-', k['kurum_kodu'] or '-',
                f"{k['amir_adi'] or '-'} ({k['amir_unvan'] or 'MÜDÜR'})"
            ), tags=tag)
        self.tree.tag_configure('aktif', background='#E8F5E9')
        aktif = KurumContext.get_active()
        if aktif:
            self.lbl_aktif.config(
                text=f"Aktif kurum: {aktif.get('kurum_adi', '-')} (ID:{aktif['id']})",
                fg="green"
            )
        else:
            self.lbl_aktif.config(text="Henuz aktif kurum secilmedi.", fg="orange")

    def tree_sec(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])['values']
        if not values:
            return
        self.kurum_id = values[0]
        with db_connection() as conn:
            row = conn.execute("""
                SELECT kurum_adi, kurum_kodu, vergi_no, amir_adi, amir_unvan,
                       saymanlik_kod, banka_subesi, iban, amir_telefon
                FROM kurum WHERE id = ?
            """, (self.kurum_id,)).fetchone()
        if row:
            self.entry_kurum_adi.delete(0, tk.END)
            self.entry_kurum_adi.insert(0, row['kurum_adi'] or "")
            self.entry_kurum_kodu.delete(0, tk.END)
            self.entry_kurum_kodu.insert(0, row['kurum_kodu'] or "")
            self.entry_vergi_no.delete(0, tk.END)
            self.entry_vergi_no.insert(0, row['vergi_no'] or "")
            self.entry_amir_adi.delete(0, tk.END)
            self.entry_amir_adi.insert(0, row['amir_adi'] or "")
            self.entry_amir_unvan.delete(0, tk.END)
            self.entry_amir_unvan.insert(0, row['amir_unvan'] or "MÜDÜR")

            # Boş değer için placeholder göster (V.2.0)
            self.entry_saymanlik_kod.delete(0, tk.END)
            if row['saymanlik_kod']:
                self.entry_saymanlik_kod.insert(0, row['saymanlik_kod'])
                self.entry_saymanlik_kod.config(fg=self.theme['entry_fg'])
            else:
                self._set_placeholder(self.entry_saymanlik_kod, "13.01.31.62-303")

            self.entry_banka_subesi.delete(0, tk.END)
            self.entry_banka_subesi.insert(0, row['banka_subesi'] or "")

            self.entry_iban.delete(0, tk.END)
            if row['iban']:
                self.entry_iban.insert(0, row['iban'])
                self.entry_iban.config(fg=self.theme['entry_fg'])
            else:
                self._set_placeholder(self.entry_iban, "TR__ ____ ____ ____ ____ ____ __")

            self.entry_amir_telefon.delete(0, tk.END)
            if row['amir_telefon']:
                self.entry_amir_telefon.insert(0, row['amir_telefon'])
                self.entry_amir_telefon.config(fg=self.theme['entry_fg'])
            else:
                self._set_placeholder(self.entry_amir_telefon, "05__ _______")

    def temizle(self):
        for entry in (self.entry_kurum_adi, self.entry_kurum_kodu, self.entry_vergi_no,
                      self.entry_amir_adi, self.entry_amir_unvan,
                      self.entry_saymanlik_kod, self.entry_banka_subesi,
                      self.entry_iban, self.entry_amir_telefon):
            entry.delete(0, tk.END)
            if hasattr(entry, 'placeholder'):
                entry.config(fg=self.theme['entry_fg'])
        self.entry_amir_unvan.insert(0, "MÜDÜR")
        self._set_placeholder(self.entry_saymanlik_kod, "13.01.31.62-303")
        self._set_placeholder(self.entry_iban, "TR__ ____ ____ ____ ____ ____ __")
        self._set_placeholder(self.entry_amir_telefon, "05__ _______")

        self.kurum_id = None
        self.tree.selection_remove(self.tree.selection())

    def kaydet(self):
        data = self._form_values()
        if not self._validate(data):
            return
        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO kurum 
                    (kurum_adi, kurum_kodu, vergi_no, amir_adi, amir_unvan,
                     saymanlik_kod, banka_subesi, iban, amir_telefon)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (data['kurum_adi'], data['kurum_kodu'], data['vergi_no'],
                      data['amir_adi'], data['amir_unvan'], data['saymanlik_kod'],
                      data['banka_subesi'], data['iban'], data['amir_telefon']))
                self.kurum_id = cursor.lastrowid
            if KurumContext.get_active_id() is None:
                KurumContext.set_active(self.kurum_id)
            messagebox.showinfo("Basarili", "Kurum kaydedildi!")
            self.temizle()
            self.listele()
        except Exception as e:
            messagebox.showerror("Hata", f"Kayit hatasi: {e}")

    def guncelle(self):
        if not self.kurum_id:
            messagebox.showerror("Hata", "Guncellenecek kurumu listeden secin!")
            return
        data = self._form_values()
        if not self._validate(data):
            return
        if not messagebox.askyesno("Onay", "Kurum bilgilerini guncellemek istiyor musunuz?"):
            return
        try:
            with db_connection() as conn:
                conn.execute("""
                    UPDATE kurum SET kurum_adi=?, kurum_kodu=?, vergi_no=?, amir_adi=?, amir_unvan=?,
                                    saymanlik_kod=?, banka_subesi=?, iban=?, amir_telefon=?
                    WHERE id=?
                """, (data['kurum_adi'], data['kurum_kodu'], data['vergi_no'],
                      data['amir_adi'], data['amir_unvan'], data['saymanlik_kod'],
                      data['banka_subesi'], data['iban'], data['amir_telefon'],
                      self.kurum_id))
            messagebox.showinfo("Basarili", "Kurum guncellendi!")
            self.listele()
        except Exception as e:
            messagebox.showerror("Hata", f"Guncelleme hatasi: {e}")

    def sil(self):
        if not self.kurum_id:
            messagebox.showerror("Hata", "Silinecek kurumu listeden secin!")
            return
        p_count = count_personel_for_kurum(self.kurum_id)
        if p_count > 0:
            messagebox.showerror(
                "Hata",
                f"Bu kurumda {p_count} personel kaydi var.\nOnce personelleri silin veya baska kuruma tasiyin."
            )
            return
        if not messagebox.askyesno("Onay", "Bu kurumu silmek istediginize emin misiniz?"):
            return
        try:
            silinen_id = self.kurum_id
            with db_connection() as conn:
                conn.execute("DELETE FROM kurum WHERE id = ?", (silinen_id,))
            if KurumContext.get_active_id() == silinen_id:
                kalan = get_kurum_list()
                KurumContext.set_active(kalan[0]['id'] if kalan else None)
            self.temizle()
            self.listele()
            messagebox.showinfo("Basarili", "Kurum silindi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Silme hatasi: {e}")

    def aktif_yap(self):
        if not self.kurum_id:
            messagebox.showerror("Hata", "Aktif yapilacak kurumu listeden secin!")
            return
        KurumContext.set_active(self.kurum_id)
        self.listele()
        messagebox.showinfo("Basarili", "Aktif kurum degistirildi.")