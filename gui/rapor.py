# gui/rapor.py - Raporlama ekranı (V.2.1)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
from datetime import datetime
import shutil

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import db_connection
from utils.excel_export import ExcelExporter
from utils.pdf_export import PDFExporter
from utils.base_page import BasePage
from utils.helpers import parse_id_from_secim, personel_listesi_yukle, get_aylar, format_tl
from utils.logger import log_exception_context


class RaporIslemleri(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.selected_personel_id = None
        self.selected_borc_id = None
        self.selected_ay = None
        self.create_widgets()
        self.load_personel_list()
        self.apply_theme(self.theme)

    def create_widgets(self):
        self.frame = tk.Frame(self.parent, bg=self.theme['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        title = tk.Label(self.frame, text="📊 RAPORLAMA",
                         font=("Segoe UI", 18, "bold"), fg="#1a237e", bg=self.theme['bg'])
        title.grid(row=0, column=0, columnspan=4, pady=(0, 15))

        tk.Label(self.frame, text="Personel Seçin:*", font=("Segoe UI", 10, "bold"), bg=self.theme['bg']).grid(row=1, column=0, sticky="w", pady=5)
        self.personel_combobox = ttk.Combobox(self.frame, width=35, font=("Segoe UI", 10))
        self.personel_combobox.grid(row=1, column=1, pady=5, sticky="w", padx=(0, 20))
        self.personel_combobox.bind("<<ComboboxSelected>>", self.personel_sec)

        tk.Label(self.frame, text="Ay Seçin:*", font=("Segoe UI", 10, "bold"), bg=self.theme['bg']).grid(row=1, column=2, sticky="w", pady=5)
        self.ay_combobox = ttk.Combobox(self.frame, width=15, font=("Segoe UI", 10))
        self.ay_combobox.grid(row=1, column=3, pady=5, sticky="w")
        self.ay_combobox['values'] = get_aylar()
        self.ay_combobox.set(datetime.now().strftime("%Y-%m"))
        self.ay_combobox.bind("<<ComboboxSelected>>", self.ay_sec)

        tk.Label(self.frame, text="Raporlanacak Borç Seçin:", font=("Segoe UI", 10, "bold"), bg=self.theme['bg']).grid(row=2, column=0, sticky="w", pady=5)
        self.borc_combobox = ttk.Combobox(self.frame, width=45, font=("Segoe UI", 10))
        self.borc_combobox.grid(row=2, column=1, columnspan=3, pady=5, sticky="w")
        self.borc_combobox.bind("<<ComboboxSelected>>", self.borc_sec)

        self.info_frame = ttk.LabelFrame(self.frame, text="📋 Personel Bilgileri", padding=15)
        self.info_frame.grid(row=3, column=0, columnspan=4, pady=15, sticky="ew")

        self.lbl_maas = tk.Label(self.info_frame, text="Maaş Kaydı: -", font=("Segoe UI", 10))
        self.lbl_maas.pack(anchor="w", pady=3)

        self.lbl_borc = tk.Label(self.info_frame, text="Borç Kaydı: -", font=("Segoe UI", 10))
        self.lbl_borc.pack(anchor="w", pady=3)

        self.lbl_kesinti = tk.Label(self.info_frame, text="Kesinti Kayıtları:", font=("Segoe UI", 10))
        self.lbl_kesinti.pack(anchor="w", pady=(3, 0))

        kesinti_liste_frame = tk.Frame(self.info_frame)
        kesinti_liste_frame.pack(anchor="w", fill=tk.X, pady=(0, 3))

        kesinti_columns = ("ay_yil", "kesilen_tutar", "ay_sonu_kalan")
        self.kesinti_listesi_tree = ttk.Treeview(
            kesinti_liste_frame, columns=kesinti_columns, show="headings", height=4
        )
        self.kesinti_listesi_tree.heading("ay_yil", text="Ay/Yıl")
        self.kesinti_listesi_tree.heading("kesilen_tutar", text="Kesilen Tutar")
        self.kesinti_listesi_tree.heading("ay_sonu_kalan", text="Ay Sonu Kalan")
        self.kesinti_listesi_tree.column("ay_yil", width=90, anchor="center")
        self.kesinti_listesi_tree.column("kesilen_tutar", width=130, anchor="e")
        self.kesinti_listesi_tree.column("ay_sonu_kalan", width=130, anchor="e")

        kesinti_scroll = ttk.Scrollbar(kesinti_liste_frame, orient=tk.VERTICAL,
                                        command=self.kesinti_listesi_tree.yview)
        self.kesinti_listesi_tree.configure(yscrollcommand=kesinti_scroll.set)
        self.kesinti_listesi_tree.pack(side=tk.LEFT)
        kesinti_scroll.pack(side=tk.LEFT, fill=tk.Y)

        self.lbl_kalan = tk.Label(self.info_frame, text="Güncel Kalan Borç: -", font=("Segoe UI", 10, "bold"))
        self.lbl_kalan.pack(anchor="w", pady=3)

        button_frame = tk.Frame(self.frame, bg=self.theme['bg'])
        button_frame.grid(row=4, column=0, columnspan=4, pady=20)

        self.btn_excel = tk.Button(button_frame, text="📊 Excel Rapor Oluştur", command=self.excel_rapor,
                                   font=("Segoe UI", 11, "bold"), bg="#217346", fg="white",
                                   width=22, height=1, relief=tk.RAISED, bd=2, cursor="hand2")
        self.btn_excel.pack(side=tk.LEFT, padx=10)

        self.btn_pdf = tk.Button(button_frame, text="📄 PDF Rapor Oluştur", command=self.pdf_rapor,
                                 font=("Segoe UI", 11, "bold"), bg="#D32F2F", fg="white",
                                 width=22, height=1, relief=tk.RAISED, bd=2, cursor="hand2")
        self.btn_pdf.pack(side=tk.LEFT, padx=10)

        for btn in [self.btn_excel, self.btn_pdf]:
            def on_enter(e, b=btn):
                b.config(relief=tk.SUNKEN, bd=3)
            def on_leave(e, b=btn):
                b.config(relief=tk.RAISED, bd=2)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

    def ay_sec(self, event=None):
        self.selected_ay = self.ay_combobox.get()
        self.update_personel_info()

    def load_personel_list(self):
        # Sadece borcu olan personelleri getir
        self.personel_listesi = personel_listesi_yukle(self.personel_combobox, sadece_borclu=True)
        if self.personel_listesi:
            self.personel_sec()

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
            self.selected_borc_id = None
            for item in self.kesinti_listesi_tree.get_children():
                self.kesinti_listesi_tree.delete(item)
            self.lbl_kesinti.config(text="Kesinti Kayıtları: -")

        self.update_personel_info()

    def borc_sec(self, event=None):
        secim = self.borc_combobox.get()
        self.selected_borc_id = parse_id_from_secim(secim)
        self.update_personel_info()

    def update_personel_info(self):
        if not self.selected_personel_id:
            return

        with db_connection() as conn:
            cursor = conn.cursor()
            row = None  # UnboundLocalError önlemi

            ay = self.selected_ay or datetime.now().strftime("%Y-%m")
            cursor.execute("""
                SELECT COUNT(*) FROM maas_kalemleri 
                WHERE personel_id = ? AND baslangic_ay <= ?
                      AND (bitis_ay IS NULL OR bitis_ay >= ?)
            """, (self.selected_personel_id, ay, ay))
            maas_count = cursor.fetchone()[0]
            if maas_count > 0:
                self.lbl_maas.config(text=f"Maaş Kaydı: {ay} için var", fg="green")
            else:
                self.lbl_maas.config(text=f"Maaş Kaydı: {ay} için yok!", fg="red")

            cursor.execute("SELECT COUNT(*) FROM borc WHERE personel_id = ?", (self.selected_personel_id,))
            borc_count = cursor.fetchone()[0]
            self.lbl_borc.config(text=f"Borç Kaydı: {borc_count} adet")

            if self.selected_borc_id:
                for item in self.kesinti_listesi_tree.get_children():
                    self.kesinti_listesi_tree.delete(item)

                cursor.execute("""
                    SELECT ay_yil, kesilen_tutar, ay_sonu_kalan
                    FROM kesinti_takip WHERE borc_id = ?
                    ORDER BY ay_yil ASC, id ASC
                """, (self.selected_borc_id,))
                kesinti_satirlari = cursor.fetchall()

                for satir in kesinti_satirlari:
                    ay_yil_deger = satir[0]
                    kesilen = satir[1] if satir[1] is not None else 0
                    kalan = satir[2] if satir[2] is not None else 0
                    self.kesinti_listesi_tree.insert(
                        "", tk.END,
                        values=(ay_yil_deger, format_tl(kesilen), format_tl(kalan))
                    )

                self.lbl_kesinti.config(text=f"Kesinti Kayıtları: ({len(kesinti_satirlari)} ay)")

                cursor.execute("""
                    SELECT ay_sonu_kalan FROM kesinti_takip
                    WHERE borc_id = ?
                    ORDER BY ay_yil DESC, id DESC LIMIT 1
                """, (self.selected_borc_id,))
                row = cursor.fetchone()
                if row and row[0] is not None:
                    self.lbl_kalan.config(text=f"Güncel Kalan Borç: {format_tl(row[0])}", fg="red")
                else:
                    cursor.execute("SELECT toplam_borc FROM borc WHERE id = ?", (self.selected_borc_id,))
                    row2 = cursor.fetchone()
                    if row2:
                        self.lbl_kalan.config(text=f"Toplam Borç: {format_tl(row2[0] or 0)} (Henüz kesinti yapılmamış)", fg="orange")
                    else:
                        self.lbl_kalan.config(text="Güncel Kalan Borç: -", fg="black")
            else:
                cursor.execute("SELECT SUM(toplam_borc) FROM borc WHERE personel_id = ?", (self.selected_personel_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    self.lbl_kalan.config(text=f"Toplam Borç: {format_tl(row[0])} (Tüm borçlar)", fg="blue")
                else:
                    self.lbl_kalan.config(text="Güncel Kalan Borç: -", fg="black")

    def get_personel_data(self, personel_id):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ad_soyad, saymanlik_no, tc_no FROM personel WHERE id = ?
            """, (personel_id,))
            personel_row = cursor.fetchone()
            if not personel_row:
                return "", {}, [], [], "", ""
            
            personel_adi = personel_row[0]
            saymanlik_no = personel_row[1] or ""
            tc_no = personel_row[2] or ""

            ay = self.selected_ay or datetime.now().strftime("%Y-%m")

            cursor.execute("""
                SELECT baslangic_ay AS ay_yil, aylik_tutar, taban_aylik, ek_gosterge, yan_odeme, kidem, ozel_hizmet,
                       makam, dil, ek_odeme_666, ek_tazminat, ilave_odeme
                FROM maas_kalemleri
                WHERE personel_id = ? AND baslangic_ay <= ?
                      AND (bitis_ay IS NULL OR bitis_ay >= ?)
                ORDER BY baslangic_ay DESC, id DESC LIMIT 1
            """, (personel_id, ay, ay))
            maas_row = cursor.fetchone()

            borc_turu = 'icra'
            nafaka_tutari = 0
            if self.selected_borc_id:
                cursor.execute("SELECT borc_turu, aylik_nafaka_tutari FROM borc WHERE id = ?", (self.selected_borc_id,))
                b = cursor.fetchone()
                if b:
                    borc_turu = b[0] or 'icra'
                    nafaka_tutari = b[1] or 0

            maas_data = {}
            if maas_row:
                toplam = sum((v or 0) for v in maas_row[1:])
                haciz = nafaka_tutari if borc_turu == 'nafaka' else toplam / 4
                maas_data = {
                    'ay_yil': maas_row[0],
                    'aylik_tutar': maas_row[1] or 0,
                    'taban_aylik': maas_row[2] or 0,
                    'ek_gosterge': maas_row[3] or 0,
                    'yan_odeme': maas_row[4] or 0,
                    'kidem': maas_row[5] or 0,
                    'ozel_hizmet': maas_row[6] or 0,
                    'makam': maas_row[7] or 0,
                    'dil': maas_row[8] or 0,
                    'ek_odeme_666': maas_row[9] or 0,
                    'ek_tazminat': maas_row[10] or 0,
                    'ilave_odeme': maas_row[11] or 0,
                    'toplam': toplam,
                    'haciz': haciz,
                    'borc_turu': borc_turu
                }

            cursor.execute("""
                SELECT id, icra_daire_adi, dosya_no, toplam_borc
                FROM borc WHERE personel_id = ? ORDER BY id ASC
            """, (personel_id,))
            borc_data = []
            for row in cursor.fetchall():
                borc_data.append({
                    'id': row[0],
                    'icra_daire_adi': row[1],
                    'dosya_no': row[2],
                    'toplam_borc': row[3]
                })

            kesinti_data = []
            if self.selected_borc_id:
                cursor.execute("""
                    SELECT k.id, k.borc_id, k.ay_yil, k.onceki_kalan, k.hesaplanan_kesinti,
                           k.kesilen_tutar, k.ay_sonu_kalan, k.aciklama,
                           b.icra_daire_adi, b.dosya_no, b.toplam_borc
                    FROM kesinti_takip k
                    JOIN borc b ON b.id = k.borc_id
                    WHERE b.id = ? AND k.ay_yil = ?
                    ORDER BY k.id DESC LIMIT 1
                """, (self.selected_borc_id, ay))

                for row in cursor.fetchall():
                    cursor2 = conn.cursor()
                    cursor2.execute("""
                        SELECT SUM(kesilen_tutar) FROM kesinti_takip 
                        WHERE borc_id = ? AND ay_yil < ?
                    """, (row[1], row[2]))
                    toplam_kesinti = cursor2.fetchone()[0] or 0
                    cursor2.close()

                    kesinti_data.append({
                        'id': row[0],
                        'borc_id': row[1],
                        'ay_yil': row[2],
                        'onceki_kalan': row[3] or 0,
                        'hesaplanan_kesinti': row[4] or 0,
                        'kesilen_tutar': row[5] or 0,
                        'ay_sonu_kalan': row[6] or 0,
                        'aciklama': row[7] or '',
                        'icra_daire_adi': row[8],
                        'dosya_no': row[9],
                        'toplam_borc': row[10],
                        'toplam_kesinti': toplam_kesinti,
                        'onceki_kesinti': 0
                    })

        return personel_adi, maas_data, borc_data, kesinti_data, saymanlik_no, tc_no

    def get_kurum_bilgileri(self):
        from utils.db_repo import get_active_kurum
        kurum = get_active_kurum()
        if not kurum:
            return {
                'kurum_adi': "", 'kurum_kodu': "", 'vergi_no': "",
                'amir_adi': "", 'amir_unvan': "MÜDÜR"
            }
        return {
            'kurum_adi': kurum.get('kurum_adi') or "",
            'kurum_kodu': kurum.get('kurum_kodu') or "",
            'vergi_no': kurum.get('vergi_no') or "",
            'amir_adi': kurum.get('amir_adi') or "",
            'amir_unvan': kurum.get('amir_unvan') or "MÜDÜR"
        }

    def _check_maas_exists(self, ay):
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM maas_kalemleri 
                WHERE personel_id = ? AND baslangic_ay <= ?
                      AND (bitis_ay IS NULL OR bitis_ay >= ?)
            """, (self.selected_personel_id, ay, ay))
            return cursor.fetchone()[0] > 0

    def _confirm_if_no_maas(self, ay):
        if self._check_maas_exists(ay):
            return True
        return messagebox.askyesno("Uyarı",
            f"{ay} için maaş kaydı bulunamadı!\n\n"
            f"Rapor yine de oluşturulsun mu?\n(Maaş kalemleri boş görünecek)")

    def excel_rapor(self):
        if not self.selected_personel_id:
            messagebox.showerror("Hata", "Lütfen bir personel seçin!")
            return

        if not self.selected_borc_id:
            messagebox.showerror("Hata", "Lütfen raporlanacak bir borç seçin!")
            return

        ay = self.selected_ay or datetime.now().strftime("%Y-%m")
        if not self._confirm_if_no_maas(ay):
            return

        personel_adi, maas_data, borc_data, kesinti_data, saymanlik_no, tc_no = self.get_personel_data(self.selected_personel_id)

        if kesinti_data and self.selected_borc_id:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT onceki_kesinti FROM borc WHERE id = ?", (self.selected_borc_id,))
                row = cursor.fetchone()
                if row:
                    kesinti_data[0]['onceki_kesinti'] = row[0] or 0.0

        if not borc_data:
            messagebox.showerror("Hata", "Personelin borç kaydı bulunamadı!")
            return

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, icra_daire_adi, dosya_no, toplam_borc
                FROM borc WHERE personel_id = ? ORDER BY id ASC
            """, (self.selected_personel_id,))
            tum_borclar = [{
                'id': row[0], 'icra_daire_adi': row[1],
                'dosya_no': row[2], 'toplam_borc': row[3]
            } for row in cursor.fetchall()]

        kurum = self.get_kurum_bilgileri()

        filename = f"rapor_{personel_adi.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel dosyası", "*.xlsx")],
            initialfile=filename
        )

        if not filepath:
            return

        try:
            exporter = ExcelExporter(
                personel_adi, self.selected_personel_id, self.selected_borc_id,
                saymanlik_no, tc_no
            )
            exporter.set_kurum_bilgileri(
                kurum['kurum_adi'], kurum['kurum_kodu'], kurum['vergi_no'],
                kurum['amir_adi'], kurum['amir_unvan']
            )

            workbook = exporter.create_report(
                maas_data, borc_data, kesinti_data, tum_borclar, self.selected_ay
            )
            exporter.save(filepath)

            messagebox.showinfo("Başarılı", f"✅ Excel raporu oluşturuldu!\n\n📁 {filepath}")

        except Exception as e:
            log_exception_context("Excel rapor hatası", e)
            messagebox.showerror("Hata", f"Rapor oluşturma hatası: {str(e)}")

    def pdf_rapor(self):
        if not self.selected_personel_id:
            messagebox.showerror("Hata", "Lütfen bir personel seçin!")
            return

        if not self.selected_borc_id:
            messagebox.showerror("Hata", "Lütfen raporlanacak bir borç seçin!")
            return

        ay = self.selected_ay or datetime.now().strftime("%Y-%m")
        if not self._confirm_if_no_maas(ay):
            return

        personel_adi, maas_data, borc_data, kesinti_data, saymanlik_no, tc_no = self.get_personel_data(self.selected_personel_id)

        if kesinti_data and self.selected_borc_id:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT onceki_kesinti FROM borc WHERE id = ?", (self.selected_borc_id,))
                row = cursor.fetchone()
                if row:
                    kesinti_data[0]['onceki_kesinti'] = row[0] or 0.0

        if not borc_data:
            messagebox.showerror("Hata", "Personelin borç kaydı bulunamadı!")
            return

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, icra_daire_adi, dosya_no, toplam_borc
                FROM borc WHERE personel_id = ? ORDER BY id ASC
            """, (self.selected_personel_id,))
            tum_borclar = [{
                'id': row[0], 'icra_daire_adi': row[1],
                'dosya_no': row[2], 'toplam_borc': row[3]
            } for row in cursor.fetchall()]

        kurum = self.get_kurum_bilgileri()

        filename = f"rapor_{personel_adi.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF dosyası", "*.pdf")],
            initialfile=filename
        )

        if not filepath:
            return

        temp_file = None
        try:
            exporter = PDFExporter(
                personel_adi, self.selected_personel_id, self.selected_borc_id,
                saymanlik_no, tc_no
            )
            exporter.set_kurum_bilgileri(
                kurum['kurum_adi'], kurum['kurum_kodu'], kurum['vergi_no'],
                kurum['amir_adi'], kurum['amir_unvan']
            )

            temp_file = exporter.create_report(
                maas_data, borc_data, kesinti_data, tum_borclar, self.selected_ay
            )
            shutil.copy2(temp_file, filepath)

            messagebox.showinfo("Başarılı", f"✅ PDF raporu oluşturuldu!\n\n📁 {filepath}")

        except Exception as e:
            log_exception_context("PDF rapor hatası", e)
            messagebox.showerror("Hata", f"PDF rapor oluşturma hatası: {str(e)}")
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x550")
    app = RaporIslemleri(root)
    root.mainloop()