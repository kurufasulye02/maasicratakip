# gui/personel.py - Personel işlemleri ekranı (V.2.0)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import openpyxl

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import db_connection
from utils.base_page import BasePage
from utils.kurum_context import KurumContext
from utils.db_repo import get_personel_list, personel_pasife_al, personel_aktif_et
from utils.logger import log_exception_context


class PersonelIslemleri(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.selected_personel_id = None
        self.create_widgets()
        self.listele()
        self.apply_theme(self.theme)

    def create_widgets(self):
        self.frame = tk.Frame(self.parent, bg=self.theme['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.kurum_id = KurumContext.get_active_id()

        self.kurum_info_label = tk.Label(
            self.frame,
            text=KurumContext.get_status_text(),
            font=("Arial", 9),
            fg="#555555",
            bg=self.theme['bg']
        )
        self.kurum_info_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 2))

        title = tk.Label(self.frame, text="👤 PERSONEL İŞLEMLERİ",
                         font=("Arial", 16, "bold"), fg="blue", bg=self.theme['bg'])
        title.grid(row=1, column=0, columnspan=4, pady=10)

        tk.Label(self.frame, text="Ad Soyad:*", font=("Arial", 10), bg=self.theme['bg']).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_ad = tk.Entry(self.frame, width=30)
        self.entry_ad.grid(row=2, column=1, pady=5)

        tk.Label(self.frame, text="Sicil No:", font=("Arial", 10), bg=self.theme['bg']).grid(row=2, column=2, sticky="w", pady=5)
        self.entry_sicil = tk.Entry(self.frame, width=20)
        self.entry_sicil.grid(row=2, column=3, pady=5)

        tk.Label(self.frame, text="TC Kimlik No:*", font=("Arial", 10), bg=self.theme['bg']).grid(row=3, column=0, sticky="w", pady=5)
        self.entry_tc = tk.Entry(self.frame, width=30)
        self.entry_tc.grid(row=3, column=1, pady=5)

        tk.Label(self.frame, text="Saymanlık No:", font=("Arial", 10), bg=self.theme['bg']).grid(row=3, column=2, sticky="w", pady=5)
        self.entry_saymanlik = tk.Entry(self.frame, width=20)
        self.entry_saymanlik.grid(row=3, column=3, pady=5)

        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=15)

        self.btn_ekle = tk.Button(button_frame, text="➕ Ekle", command=self.ekle,
                                  font=("Arial", 10), bg="#4CAF50", fg="white", width=12)
        self.btn_ekle.pack(side=tk.LEFT, padx=5)

        self.btn_excel = tk.Button(button_frame, text="📂 Excel'den Aktar", command=self.excel_aktar,
                                   font=("Arial", 10, "bold"), bg="#2196F3", fg="white", width=15)
        self.btn_excel.pack(side=tk.LEFT, padx=5)

        self.btn_guncelle = tk.Button(button_frame, text="✏️ Güncelle", command=self.guncelle,
                                      font=("Arial", 10), bg="#FFC107", width=12)
        self.btn_guncelle.pack(side=tk.LEFT, padx=5)

        self.btn_sil = tk.Button(button_frame, text="🗑️ Sil (Kalıcı)", command=self.sil,
                                 font=("Arial", 10), bg="#f44336", fg="white", width=14)
        self.btn_sil.pack(side=tk.LEFT, padx=5)

        self.btn_pasife_al = tk.Button(button_frame, text="🚪 Kurumdan Ayrıldı", command=self.pasife_al,
                                 font=("Arial", 10), bg="#795548", fg="white", width=16)
        self.btn_pasife_al.pack(side=tk.LEFT, padx=5)

        self.btn_aktif_et = tk.Button(button_frame, text="♻️ Geri Aktif Et", command=self.aktif_et,
                                 font=("Arial", 10), bg="#009688", fg="white", width=14)
        self.btn_aktif_et.pack(side=tk.LEFT, padx=5)

        self.btn_temizle = tk.Button(button_frame, text="🧹 Temizle", command=self.temizle,
                                     font=("Arial", 10), bg="#9E9E9E", fg="white", width=12)
        self.btn_temizle.pack(side=tk.LEFT, padx=5)

        self.btn_yenile = tk.Button(button_frame, text="🔄 Yenile", command=self.listele,
                                    font=("Arial", 10), bg="#2196F3", fg="white", width=12)
        self.btn_yenile.pack(side=tk.LEFT, padx=5)

        search_frame = ttk.Frame(self.frame)
        search_frame.grid(row=5, column=0, columnspan=4, pady=10, sticky="ew")

        tk.Label(search_frame, text="🔍 Ara:").pack(side=tk.LEFT, padx=5)
        self.entry_ara = tk.Entry(search_frame, width=30)
        self.entry_ara.pack(side=tk.LEFT, padx=5)
        self.entry_ara.bind("<KeyRelease>", self.ara)

        self.var_ayrilan_goster = tk.BooleanVar(value=False)
        self.chk_ayrilan_goster = tk.Checkbutton(
            search_frame, text="Ayrılanları da göster", variable=self.var_ayrilan_goster,
            command=self.ara
        )
        self.chk_ayrilan_goster.pack(side=tk.LEFT, padx=15)

        columns = ("id", "ad_soyad", "sicil_no", "tc_no", "saymanlik_no", "durum")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=12)

        self.tree.heading("id", text="ID")
        self.tree.heading("ad_soyad", text="Ad Soyad")
        self.tree.heading("sicil_no", text="Sicil No")
        self.tree.heading("tc_no", text="TC Kimlik")
        self.tree.heading("saymanlik_no", text="Saymanlık No")
        self.tree.heading("durum", text="Durum")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("ad_soyad", width=200)
        self.tree.column("sicil_no", width=120)
        self.tree.column("tc_no", width=150, anchor="center")
        self.tree.column("saymanlik_no", width=150, anchor="center")
        self.tree.column("durum", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=6, column=0, columnspan=3, sticky="nsew")
        scrollbar.grid(row=6, column=3, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self.tree_sec)

        self.frame.grid_rowconfigure(6, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)

        self.selected_id = None

        self.status_label = tk.Label(self.frame, text="", font=("Arial", 9), fg="gray", bg=self.theme['bg'])
        self.status_label.grid(row=7, column=0, columnspan=4, sticky="w", pady=5)

    def _refresh_kurum(self):
        self.kurum_id = KurumContext.get_active_id()
        if hasattr(self, 'kurum_info_label'):
            self.kurum_info_label.config(text=KurumContext.get_status_text())
        self.listele(self.entry_ara.get() if hasattr(self, 'entry_ara') else "")

    def listele(self, aranan=""):
        self.kurum_id = KurumContext.get_active_id()
        if hasattr(self, 'kurum_info_label'):
            self.kurum_info_label.config(text=KurumContext.get_status_text())

        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.kurum_id:
            self.status_label.config(text="Aktif kurum seçilmedi — önce Kurum Bilgileri sayfasından kurum seçin")
            return

        ayrilanlari_da_goster = self.var_ayrilan_goster.get() if hasattr(self, 'var_ayrilan_goster') else False
        rows = get_personel_list(kurum_id=self.kurum_id, search=aranan, only_active=not ayrilanlari_da_goster)
        for row in rows:
            aktif = row[5] if len(row) > 5 else 1
            durum = "Ayrıldı" if aktif == 0 else "Aktif"
            self.tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3], row[4], durum))

        count = len(rows)
        self.status_label.config(text=f"Toplam {count} personel (aktif kurum)")

    def ara(self, event=None):
        aranan = self.entry_ara.get()
        self.listele(aranan)

    def tree_sec(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0])["values"]
        if values:
            self.selected_id = values[0]
            self.entry_ad.delete(0, tk.END)
            self.entry_ad.insert(0, values[1] or "")
            self.entry_sicil.delete(0, tk.END)
            self.entry_sicil.insert(0, values[2] or "")
            self.entry_tc.delete(0, tk.END)
            self.entry_tc.insert(0, values[3] or "")
            self.entry_saymanlik.delete(0, tk.END)
            self.entry_saymanlik.insert(0, values[4] or "")

    def temizle(self):
        self.entry_ad.delete(0, tk.END)
        self.entry_sicil.delete(0, tk.END)
        self.entry_tc.delete(0, tk.END)
        self.entry_saymanlik.delete(0, tk.END)
        self.selected_id = None

    def excel_aktar(self):
        """Excel'den personel aktar - TÜM SATIRLAR TEK TRANSACTION (V.2.0)."""
        if not self.kurum_id:
            messagebox.showerror("Hata", "Önce bir kurum seçin (Kurum Bilgileri sayfasından).")
            return

        filepath = filedialog.askopenfilename(
            title="Personel Listesi Excel Dosyasını Seçin",
            filetypes=[("Excel dosyaları", "*.xlsx")]
        )
        if not filepath:
            return

        try:
            wb = openpyxl.load_workbook(filepath, data_only=True)
            ws = wb.active

            sayac = 0
            hatali_satirlar = []

            # V.2.0: Tüm aktarım tek transaction içinde - ya hep ya hiç
            with db_connection() as conn:
                cursor = conn.cursor()
                satir_no = 1
                for row in ws.iter_rows(min_row=2, values_only=True):
                    satir_no += 1
                    ad_soyad = str(row[0]).strip() if row[0] else ""
                    tc_no = str(row[1]).strip() if row[1] else ""
                    saymanlik_no = str(row[2]).strip() if row[2] else ""

                    if not ad_soyad or not tc_no:
                        hatali_satirlar.append(f"Satır {satir_no}: Ad veya TC boş")
                        continue

                    if len(tc_no) != 11 or not tc_no.isdigit():
                        hatali_satirlar.append(f"Satır {satir_no}: TC '{tc_no}' 11 haneli değil")
                        continue

                    cursor.execute("SELECT id FROM personel WHERE tc_no = ?", (tc_no,))
                    var = cursor.fetchone()

                    if var:
                        cursor.execute("""
                            UPDATE personel SET ad_soyad = ?, saymanlik_no = ?
                            WHERE id = ?
                        """, (ad_soyad, saymanlik_no, var[0]))
                    else:
                        cursor.execute("""
                            INSERT INTO personel (kurum_id, ad_soyad, tc_no, saymanlik_no)
                            VALUES (?, ?, ?, ?)
                        """, (self.kurum_id, ad_soyad, tc_no, saymanlik_no))

                    sayac += 1

            self.listele()

            mesaj = f"✅ {sayac} personel başarıyla aktarıldı."
            if hatali_satirlar:
                mesaj += f"\n\n⚠️ {len(hatali_satirlar)} satır atlandı:\n" + "\n".join(hatali_satirlar[:5])
                if len(hatali_satirlar) > 5:
                    mesaj += f"\n... ve {len(hatali_satirlar)-5} satır daha."

            messagebox.showinfo("Aktarım Tamamlandı", mesaj)

        except Exception as e:
            log_exception_context("Excel aktarım hatası", e)
            messagebox.showerror("Hata", f"Excel dosyası okunurken hata oluştu:\n{str(e)}")

    def ekle(self):
        ad = self.entry_ad.get().strip()
        tc = self.entry_tc.get().strip()

        if not ad:
            messagebox.showerror("Hata", "Ad Soyad alanı zorunludur!")
            return

        if not tc:
            messagebox.showerror("Hata", "TC Kimlik No alanı zorunludur!")
            return

        if len(tc) != 11 or not tc.isdigit():
            messagebox.showerror("Hata", "TC Kimlik No 11 haneli ve sadece rakam olmalıdır!")
            return

        if not self.kurum_id:
            messagebox.showerror("Hata", "Aktif kurum seçilmedi! Kurum Bilgileri sayfasından kurum seçin.")
            return

        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO personel (kurum_id, ad_soyad, sicil_no, tc_no, saymanlik_no)
                    VALUES (?, ?, ?, ?, ?)
                """, (self.kurum_id, ad, self.entry_sicil.get().strip(),
                      tc, self.entry_saymanlik.get().strip()))

            messagebox.showinfo("Başarılı", "Personel başarıyla eklendi!")
            self.temizle()
            self.listele()

        except Exception as e:
            if "UNIQUE" in str(e) and "tc_no" in str(e):
                messagebox.showerror("Hata", "Bu TC Kimlik No zaten kayıtlı!")
            else:
                log_exception_context("Personel ekleme hatası", e)
                messagebox.showerror("Hata", f"Kayıt hatası: {str(e)}")

    def guncelle(self):
        if not self.selected_id:
            messagebox.showerror("Hata", "Lütfen güncellenecek personeli seçin!")
            return

        ad = self.entry_ad.get().strip()
        tc = self.entry_tc.get().strip()

        if not ad:
            messagebox.showerror("Hata", "Ad Soyad alanı zorunludur!")
            return

        if not tc:
            messagebox.showerror("Hata", "TC Kimlik No alanı zorunludur!")
            return

        if len(tc) != 11 or not tc.isdigit():
            messagebox.showerror("Hata", "TC Kimlik No 11 haneli ve sadece rakam olmalıdır!")
            return

        if not messagebox.askyesno("Onay", "Bu personeli güncellemek istediğinize emin misiniz?"):
            return

        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE personel
                    SET ad_soyad = ?, sicil_no = ?, tc_no = ?, saymanlik_no = ?
                    WHERE id = ?
                """, (ad, self.entry_sicil.get().strip(), tc,
                      self.entry_saymanlik.get().strip(), self.selected_id))

            messagebox.showinfo("Başarılı", "Personel başarıyla güncellendi!")
            self.temizle()
            self.listele()

        except Exception as e:
            if "UNIQUE" in str(e) and "tc_no" in str(e):
                messagebox.showerror("Hata", "Bu TC Kimlik No başka bir personelde kayıtlı!")
            else:
                messagebox.showerror("Hata", f"Güncelleme hatası: {str(e)}")

    def sil(self):
        if not self.selected_id:
            messagebox.showerror("Hata", "Lütfen silinecek personeli seçin!")
            return

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM maas_kalemleri WHERE personel_id = ?", (self.selected_id,))
            maas_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM borc WHERE personel_id = ?", (self.selected_id,))
            borc_count = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COUNT(*) FROM kesinti_takip
                WHERE borc_id IN (SELECT id FROM borc WHERE personel_id = ?)
            """, (self.selected_id,))
            kesinti_count = cursor.fetchone()[0]

        mesaj = f"Bu personeli silmek istediğinize emin misiniz?\n\n"
        if maas_count > 0:
            mesaj += f"⚠️ {maas_count} adet maaş kaydı var.\n"
        if borc_count > 0:
            mesaj += f"⚠️ {borc_count} adet borç kaydı var.\n"
        if kesinti_count > 0:
            mesaj += f"⚠️ {kesinti_count} adet kesinti kaydı var.\n"
        mesaj += "\nBu kayıtlar da silinecektir!"

        if not messagebox.askyesno("Onay", mesaj):
            return

        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM kesinti_takip
                    WHERE borc_id IN (SELECT id FROM borc WHERE personel_id = ?)
                """, (self.selected_id,))
                cursor.execute("DELETE FROM maas_kalemleri WHERE personel_id = ?", (self.selected_id,))
                cursor.execute("DELETE FROM borc WHERE personel_id = ?", (self.selected_id,))
                cursor.execute("DELETE FROM personel WHERE id = ?", (self.selected_id,))

            messagebox.showinfo("Başarılı", "Personel başarıyla silindi!")
            self.temizle()
            self.listele()

        except Exception as e:
            messagebox.showerror("Hata", f"Silme hatası: {str(e)}")

    def pasife_al(self):
        if not self.selected_id:
            messagebox.showerror("Hata", "Lütfen bir personel seçin!")
            return

        if not messagebox.askyesno(
            "Onay",
            "Bu personeli 'Kurumdan Ayrıldı' olarak işaretlemek istediğinize emin misiniz?\n\n"
            "Kayıt SİLİNMEZ, geçmiş borç/kesinti verileri korunur.\n"
            "Sadece bundan sonraki raporlarda ve seçim listelerinde görünmez."
        ):
            return

        try:
            personel_pasife_al(self.selected_id)
            messagebox.showinfo("Başarılı", "Personel 'Ayrıldı' olarak işaretlendi.")
            self.temizle()
            self.listele(self.entry_ara.get())
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem başarısız: {str(e)}")

    def aktif_et(self):
        if not self.selected_id:
            messagebox.showerror("Hata", "Lütfen bir personel seçin!")
            return

        try:
            personel_aktif_et(self.selected_id)
            messagebox.showinfo("Başarılı", "Personel tekrar aktif duruma getirildi.")
            self.temizle()
            self.listele(self.entry_ara.get())
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem başarısız: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x600")
    app = PersonelIslemleri(root)
    root.mainloop()