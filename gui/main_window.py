# gui/main_window.py - Ana program penceresi (V.3.2.0 - İkon Destekli)

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import db_connection, init_database
from utils.theme import ThemeManager
from utils.navigation import NavigationBar
from utils.kurum_context import KurumContext
from utils.logger import show_error_report_dialog, log_exception_context
from utils.backup import yedek_al, yedekleri_listele, yedekten_geri_yukle
from utils.updater import check_for_updates

import version as _v  # V.3.0

class MainWindow:
    def __init__(self, root):
        self.root = root
        
        # V.2.0: Versiyon başlıkta
        self.root.title(_v.APP_TITLE)
        
        # --- İKON YÜKLEME KODU ---
        # EXE veya normal Python çalışması için güvenli yol bulma
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        icon_path = os.path.join(base_dir, "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception as e:
                print(f"İkon yüklenemedi: {e}")
        # -------------------------

        self._pencereyi_boyutlandir()
        self.root.minsize(1000, 700)
        self.root.resizable(True, True)

        # Sağ üstteki X butonuna basıldığında da (Alt+F4 dahil) yedekleme sorulsun.
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_request)

        self.current_page = None
        self.current_page_instance = None
        self.nav_bar = None
        self.kurum_bar = None
        self._kurum_callback = self._on_kurum_changed

        # Aktif kurum değişikliklerini dinle
        KurumContext.register(self._kurum_callback)

        # Temayı uygula
        self.apply_theme()

        # Veritabanını kontrol et
        self.check_database()

        # Ana menüyü oluştur
        self.create_menu()

        # Ana çerçeveyi oluştur
        self.create_main_frame()

        # Hoş geldin mesajı
        self.show_welcome()

        # --- GÜNCELLEME KONTROLÜ EKLEMESİ ---
        from utils.updater import check_for_updates
        check_for_updates(self.root)
   

    def _pencereyi_boyutlandir(self):
        """Pencereyi ekran çözünürlüğüne göre boyutlandırır ve ortalar."""
        ekran_w = self.root.winfo_screenwidth()
        ekran_h = self.root.winfo_screenheight()

        hedef_w = max(1000, min(1400, int(ekran_w * 0.78)))
        hedef_h = max(700, min(850, int(ekran_h * 0.78)))

        x = (ekran_w - hedef_w) // 2
        y = (ekran_h - hedef_h) // 2
        self.root.geometry(f"{hedef_w}x{hedef_h}+{x}+{y}")

    def apply_theme(self):
        """Temayı uygula"""
        theme = ThemeManager.get_theme()
        self.root.configure(bg=theme['bg'])

    def get_theme(self):
        """Mevcut temayı döndür"""
        return ThemeManager.get_theme()

    def check_database(self):
        """Veritabanı kontrolü"""
        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

            if len(tables) < 5:
                init_database()
                messagebox.showinfo("Bilgi", "Veritabanı oluşturuldu!")
        except Exception as e:
            log_exception_context("Veritabanı kontrol hatası", e)
            messagebox.showerror("Hata", f"Veritabanı hatası: {str(e)}")

    def create_menu(self):
        """Menü çubuğunu oluştur"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Dosya Menüsü
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        file_menu.add_command(label="Kurum Bilgileri", command=self.show_kurum)
        file_menu.add_separator()
        file_menu.add_command(label="💾 Yedek Al", command=self.yedek_al_manuel)
        file_menu.add_command(label="📂 Yedekten Geri Yükle", command=self.yedekten_geri_yukle_penceresi)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self._on_close_request)

        # İşlemler Menüsü
        islem_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="İşlemler", menu=islem_menu)
        islem_menu.add_command(label="Personel İşlemleri", command=self.show_personel)
        islem_menu.add_command(label="Maaş Kalemleri", command=self.show_maas)
        islem_menu.add_command(label="Borç İşlemleri", command=self.show_borc)
        islem_menu.add_command(label="Kesinti Yap", command=self.show_kesinti)
        islem_menu.add_separator()
        islem_menu.add_command(label="Maaş Değişiklik İşlemleri", command=self.show_maas_degisiklik)

        # Rapor Menüsü
        rapor_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Raporlar", menu=rapor_menu)
        rapor_menu.add_command(label="Rapor Oluştur (Excel / PDF)", command=self.show_rapor)

        # Yardım Menüsü
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Yardım", menu=help_menu)
        help_menu.add_command(label="Kullanım Kılavuzu", command=self.show_help)
        help_menu.add_command(label="Hata Raporu Gönder", command=self.show_error_report)
        help_menu.add_separator()
        help_menu.add_command(label="Hakkında", command=self.show_about)

    def create_main_frame(self):
        """Ana çerçeveyi oluştur"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def clear_frame(self):
        """Ana çerçeveyi temizle"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.nav_bar = None
        self.kurum_bar = None
        self.current_page = None
        self.current_page_instance = None

    def _on_kurum_changed(self, kurum_id):
        """Aktif kurum değişince üst çubuğu güncelle."""
        self._update_kurum_bar()
        if hasattr(self, 'welcome_kurum_label'):
            try:
                if self.welcome_kurum_label.winfo_exists():
                    self.welcome_kurum_label.config(text=KurumContext.get_status_text())
            except Exception:
                pass
        if self.current_page_instance and hasattr(self.current_page_instance, '_refresh_kurum'):
            try:
                self.current_page_instance._refresh_kurum()
            except Exception:
                pass

    def _update_kurum_bar(self):
        if self.kurum_bar and self.kurum_bar.winfo_exists():
            label = getattr(self, '_kurum_bar_label', None)
            if label and label.winfo_exists():
                label.config(text=KurumContext.get_status_text())

    def create_kurum_bar(self, parent):
        """Aktif kurum bilgi çubuğu + sağda versiyon."""
        theme = self.get_theme()
        self.kurum_bar = tk.Frame(parent, bg=theme['header_bg'], height=36)
        self.kurum_bar.pack(fill=tk.X, pady=(0, 8))
        self.kurum_bar.pack_propagate(False)

        self._kurum_bar_label = tk.Label(
            self.kurum_bar,
            text=KurumContext.get_status_text(),
            font=("Segoe UI", 10, "bold"),
            bg=theme['header_bg'],
            fg=theme['header_fg']
        )
        self._kurum_bar_label.pack(side=tk.LEFT, padx=15, pady=6)

        # V.2.0: Sağ tarafta versiyon
        self._versiyon_label = tk.Label(
            self.kurum_bar,
            text=f"⚡ {_v.get_display_version()}",
            font=("Segoe UI", 9, "bold"),
            bg=theme['header_bg'],
            fg=theme['header_sub']
        )
        self._versiyon_label.pack(side=tk.RIGHT, padx=15, pady=6)

    def show_with_nav(self, page_id, page_class):
        """Navigasyonlu sayfa göster"""
        self.clear_frame()
        self.current_page = page_id

        # Aktif kurum çubuğu
        self.create_kurum_bar(self.main_frame)

        # Ana içerik - content_frame (sayfa içeriği için)
        content_frame = tk.Frame(self.main_frame, bg=self.get_theme()['frame_bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Sayfa içeriği - parent olarak content_frame ver
        try:
            self.current_page_instance = page_class(content_frame)
        except Exception as e:
            log_exception_context(f"Sayfa yükleme hatası ({page_id})", e)
            messagebox.showerror("Hata", f"Sayfa yüklenirken hata oluştu: {str(e)}")
            return

        # Navigasyon çubuğu - main_frame'in altına
        self.nav_bar = NavigationBar(self.main_frame, self, page_id)

    def show_welcome(self):
        """Hoş geldin mesajını göster"""
        self.clear_frame()
        self.current_page = 'home'

        theme = self.get_theme()
        container = tk.Frame(self.main_frame, bg=theme['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        # Üst bölüm
        header_frame = tk.Frame(container, bg=theme['header_bg'], height=100)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        header_frame.pack_propagate(False)

        title = tk.Label(
            header_frame,
            text="🏫 İCRA/NAFAKA/MAAŞ DEĞİŞİKLİK TAKİP PROGRAMI",
            font=("Segoe UI", 24, "bold"),
            bg=theme['header_bg'],
            fg=theme['header_fg']
        )
        title.pack(pady=(20, 5))

        subtitle = tk.Label(
            header_frame,
            text=_v.APP_SUBTITLE,
            font=("Segoe UI", 12),
            bg=theme['header_bg'],
            fg=theme['header_sub']
        )
        subtitle.pack()

        # Aktif kurum bilgisi
        kurum_text = KurumContext.get_status_text()
        self.welcome_kurum_label = tk.Label(
            header_frame,
            text=kurum_text,
            font=("Segoe UI", 10, "bold"),
            bg=theme['header_bg'],
            fg=theme['header_sub']
        )
        self.welcome_kurum_label.pack(pady=(8, 10))

        # Buton grid
        grid_frame = tk.Frame(container, bg=theme['bg'])
        grid_frame.pack(pady=15, padx=30, fill=tk.BOTH, expand=True)

        # Grid ayarları (2 sütun, 4 satır - son satırda tek buton iki sütunu kapsar)
        for i in range(2):
            grid_frame.grid_columnconfigure(i, weight=1, minsize=180)
        for i in range(4):
            grid_frame.grid_rowconfigure(i, weight=1, minsize=140)

        colors = {
            "kurum": "#1565C0",
            "personel": "#2E7D32",
            "maas": "#E65100",
            "borc": "#AD1457",
            "kesinti": "#6A1B9A",
            "rapor": "#BF360C",
            "maas_degisiklik": "#00838F"
        }

        buttons = [
            ("🏢 Kurum Bilgileri", self.show_kurum, colors["kurum"]),
            ("👤 Personel İşlemleri", self.show_personel, colors["personel"]),
            ("💰 Maaş Kalemleri", self.show_maas, colors["maas"]),
            ("📄 Borç İşlemleri", self.show_borc, colors["borc"]),
            ("✏️ Kesinti Girişi", self.show_kesinti, colors["kesinti"]),
            ("📊 Rapor Oluştur", self.show_rapor, colors["rapor"]),
            ("📝 Maaş Değişiklik İşlemleri", self.show_maas_degisiklik, colors["maas_degisiklik"])
        ]

        # İlk 6 buton 2'şerli grid'e dizilir
        for i, (text, cmd, color) in enumerate(buttons[:-1]):
            self.create_home_button(grid_frame, text, cmd, color, i // 2, i % 2)

        # SON BUTON (Maaş Değişiklik) - iki sütunu birden kapsar!
        self.create_home_button(grid_frame, buttons[-1][0], buttons[-1][1], buttons[-1][2], 3, 0, span=2)

        # Alt bilgi
        info_frame = tk.Frame(container, bg=theme['bg'])
        info_frame.pack(pady=10)

        info = tk.Label(
            info_frame,
            text="📌 Sol üst menüden veya butonlardan tüm işlemlere ulaşabilirsiniz",
            font=("Segoe UI", 10),
            fg=theme['label_secondary'],
            bg=theme['bg']
        )
        info.pack()

        # V.2.0: Versiyon alt bilgide
        version = tk.Label(
            info_frame,
            text=f"Versiyon {_v.VERSION} | © 2026 MEB | 📅 {_v.VERSION_DATE}",
            font=("Segoe UI", 8),
            fg=theme['label_secondary'],
            bg=theme['bg']
        )
        version.pack()

    def create_home_button(self, parent, text, command, color, row, col, span=1):
        """Ana sayfa butonu - kartın tamamı tıklanabilir"""
        frame = tk.Frame(
            parent,
            bg=color,
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        frame.grid(row=row, column=col, columnspan=span, padx=15, pady=15, sticky="nsew")

        inner = tk.Frame(frame, bg=color, cursor="hand2")
        inner.pack(expand=True, fill=tk.BOTH)

        icon = text.split()[0]
        label_text = text.replace(icon, "").strip()

        icon_label = tk.Label(
            inner,
            text=icon,
            font=("Segoe UI", 40),
            bg=color,
            fg="white",
            cursor="hand2"
        )
        icon_label.pack(expand=True, pady=(15, 0))

        text_label = tk.Label(
            inner,
            text=label_text,
            font=("Segoe UI", 16, "bold"),
            bg=color,
            fg="white",
            cursor="hand2"
        )
        text_label.pack(expand=True, pady=(5, 15))

        tiklanabilir_parcalar = [frame, inner, icon_label, text_label]

        acik_renk = self._renk_acart(color)

        def on_enter(e):
            frame.config(relief=tk.SUNKEN, bd=3, bg=acik_renk)
            inner.config(bg=acik_renk)
            icon_label.config(bg=acik_renk)
            text_label.config(bg=acik_renk)

        def on_leave(e):
            frame.config(relief=tk.RAISED, bd=2, bg=color)
            inner.config(bg=color)
            icon_label.config(bg=color)
            text_label.config(bg=color)

        def on_click(e):
            command()

        for parca in tiklanabilir_parcalar:
            parca.bind("<Enter>", on_enter)
            parca.bind("<Leave>", on_leave)
            parca.bind("<Button-1>", on_click)

        parent.grid_rowconfigure(row, weight=1)
        parent.grid_columnconfigure(col, weight=1)

    def _renk_acart(self, hex_renk, miktar=25):
        """Hover efekti için bir rengi biraz açar"""
        hex_renk = hex_renk.lstrip('#')
        r, g, b = int(hex_renk[0:2], 16), int(hex_renk[2:4], 16), int(hex_renk[4:6], 16)
        r = min(255, r + miktar)
        g = min(255, g + miktar)
        b = min(255, b + miktar)
        return f"#{r:02x}{g:02x}{b:02x}"

    def yedek_al_manuel(self):
        """Dosya menüsünden istenildiği an elle yedek almak için."""
        try:
            yedek_yolu = yedek_al()
            if yedek_yolu:
                messagebox.showinfo("Yedekleme Tamamlandı", f"Veritabanı yedeği alındı:\n\n{yedek_yolu}")
            else:
                messagebox.showinfo("Bilgi", "Henüz bir veritabanı dosyası bulunmadığı için yedek alınmadı.")
        except Exception as e:
            log_exception_context("Elle yedekleme hatası", e)
            messagebox.showerror("Hata", f"Yedek alınırken hata oluştu:\n\n{str(e)}")

    def yedekten_geri_yukle_penceresi(self):
        """'yedekler' klasöründeki yedekleri listeler; seçilen yedeği geri yükler."""
        yedekler = yedekleri_listele()

        pencere = tk.Toplevel(self.root)
        pencere.title("Yedekten Geri Yükle")
        pencere.geometry("560x420")
        pencere.grab_set()

        tk.Label(
            pencere,
            text="⚠️ Geri yükleme, MEVCUT verilerin üzerine yazar!\n"
                 "(Geri yüklemeden hemen önce mevcut durumun otomatik güvenlik yedeği alınır.)",
            fg="#b71c1c", font=("Segoe UI", 9, "bold"), justify="left"
        ).pack(padx=10, pady=(10, 5), anchor="w")

        if not yedekler:
            tk.Label(pencere, text="Henüz hiç yedek alınmamış.", font=("Segoe UI", 10)).pack(pady=20)
            return

        columns = ("dosya", "tarih", "boyut")
        tree = ttk.Treeview(pencere, columns=columns, show="headings", height=12)
        tree.heading("dosya", text="Yedek Dosyası")
        tree.heading("tarih", text="Tarih / Saat")
        tree.heading("boyut", text="Boyut (KB)")
        tree.column("dosya", width=260)
        tree.column("tarih", width=150, anchor="center")
        tree.column("boyut", width=90, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        yol_haritasi = {}
        for dosya_adi, tam_yol, tarih_str, boyut_kb in yedekler:
            tree.insert("", tk.END, iid=tam_yol, values=(dosya_adi, tarih_str, boyut_kb))
            yol_haritasi[tam_yol] = dosya_adi

        def secili_yedegi_geri_yukle():
            secim = tree.selection()
            if not secim:
                messagebox.showwarning("Uyarı", "Lütfen listeden bir yedek seçin.", parent=pencere)
                return

            secilen_yol = secim[0]
            secilen_ad = yol_haritasi.get(secilen_yol, secilen_yol)

            if not messagebox.askyesno(
                "Onay",
                f"'{secilen_ad}' yedeği geri yüklenecek.\n\n"
                "Bu işlem, şu andaki tüm verilerin üzerine yazacak!\n"
                "(Mevcut durumun güvenlik yedeği otomatik alınacak.)\n\n"
                "Devam etmek istiyor musunuz?",
                parent=pencere
            ):
                return

            try:
                yedekten_geri_yukle(secilen_yol)
                messagebox.showinfo(
                    "Geri Yükleme Tamamlandı",
                    "Seçilen yedek başarıyla geri yüklendi.\n\n"
                    "Değişikliklerin düzgün yansıması için program şimdi kapanacak.\n"
                    "Lütfen programı tekrar açın.",
                    parent=pencere
                )
                pencere.destroy()
                self.root.destroy()
            except Exception as e:
                log_exception_context("Yedekten geri yükleme hatası", e)
                messagebox.showerror("Hata", f"Geri yükleme sırasında hata oluştu:\n\n{str(e)}", parent=pencere)

        btn_frame = tk.Frame(pencere)
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame, text="♻️ Seçili Yedeği Geri Yükle", command=secili_yedegi_geri_yukle,
            bg="#b71c1c", fg="white", font=("Segoe UI", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Kapat", command=pencere.destroy).pack(side=tk.LEFT, padx=5)

    def _on_close_request(self):
        """Pencere kapatılmak istendiğinde (X butonu / Alt+F4) çağrılır."""
        cevap = messagebox.askyesnocancel(
            "Programdan Çıkış",
            "Programdan çıkmak üzeresiniz.\n\n"
            "Çıkmadan önce veritabanının yedeğini almak ister misiniz?\n\n"
            "Evet: Yedek alır ve programı kapatır\n"
            "Hayır: Yedek almadan programı kapatır\n"
            "İptal: Programda kalır"
        )

        if cevap is None:
            return

        if cevap:
            try:
                yedek_yolu = yedek_al()
                if yedek_yolu:
                    messagebox.showinfo(
                        "Yedekleme Tamamlandı",
                        f"Veritabanı yedeği başarıyla alındı:\n\n{yedek_yolu}"
                    )
                else:
                    messagebox.showinfo(
                        "Bilgi",
                        "Henüz bir veritabanı dosyası bulunmadığı için yedek alınmadı."
                    )
            except Exception as e:
                log_exception_context("Çıkışta yedekleme hatası", e)
                if not messagebox.askyesno(
                    "Yedekleme Hatası",
                    f"Yedek alınırken bir hata oluştu:\n\n{str(e)}\n\n"
                    "Yine de programdan çıkılsın mı?"
                ):
                    return

        self.root.destroy()

    # Sayfa gösterim metodları
    def show_kurum(self):
        from gui.kurum import KurumIslemleri
        self.show_with_nav('kurum', KurumIslemleri)

    def show_personel(self):
        from gui.personel import PersonelIslemleri
        self.show_with_nav('personel', PersonelIslemleri)

    def show_maas(self):
        from gui.maas import MaasIslemleri
        self.show_with_nav('maas', MaasIslemleri)

    def show_borc(self):
        from gui.borc import BorcIslemleri
        self.show_with_nav('borc', BorcIslemleri)

    def show_kesinti(self):
        from gui.kesinti import KesintiIslemleri
        self.show_with_nav('kesinti', KesintiIslemleri)

    def show_rapor(self):
        from gui.rapor import RaporIslemleri
        self.show_with_nav('rapor', RaporIslemleri)

    def show_maas_degisiklik(self):
        from gui.maas_degisiklik import MaasDegisiklikIslemleri
        self.show_with_nav('maas_degisiklik', MaasDegisiklikIslemleri)

    def show_error_report(self):
        show_error_report_dialog(self.root)

    def show_help(self):
        """Kullanım kılavuzu"""
        pencere = tk.Toplevel(self.root)
        pencere.title(f"Yardım - {_v.get_display_version()}")
        pencere.geometry("820x620")
        pencere.minsize(600, 400)

        notebook = ttk.Notebook(pencere)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        sekme1 = tk.Frame(notebook)
        sekme2 = tk.Frame(notebook)
        notebook.add(sekme1, text="📖 Kullanım Kılavuzu")
        notebook.add(sekme2, text="🛠️ Sık Karşılaşılan Sorunlar")

        self._yardim_metin_widgeti_olustur(sekme1, self._kullanim_kilavuzu_metni())
        self._yardim_metin_widgeti_olustur(sekme2, self._sss_metni())

        tk.Button(pencere, text="Kapat", command=pencere.destroy, width=14).pack(pady=(0, 8))

    def _yardim_metin_widgeti_olustur(self, parent, icerik):
        cerceve = tk.Frame(parent)
        cerceve.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(cerceve)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        metin = tk.Text(cerceve, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                         font=("Segoe UI", 10), padx=10, pady=10, relief=tk.FLAT)
        metin.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=metin.yview)

        metin.tag_configure("baslik", font=("Segoe UI", 13, "bold"), foreground="#0d47a1", spacing3=6)
        metin.tag_configure("altbaslik", font=("Segoe UI", 10, "bold"), foreground="#1565c0", spacing1=8, spacing3=2)
        metin.tag_configure("uyari", font=("Segoe UI", 10, "bold"), foreground="#b71c1c")
        metin.tag_configure("normal", font=("Segoe UI", 10), spacing3=2)

        for tur, satir in icerik:
            metin.insert(tk.END, satir + "\n", tur)

        metin.config(state=tk.DISABLED)

    def _kullanim_kilavuzu_metni(self):
        return [
            ("baslik", f"📖 İCRA / NAFAKA TAKİP PROGRAMI — KULLANIM KILAVUZU ({_v.get_display_version()})"),
            ("normal", "Program, ekrandaki navigasyon çubuğunu kullanarak adım adım ilerleyecek şekilde tasarlanmıştır. Aşağıdaki sıra önerilir."),
            ("normal", ""),

            ("altbaslik", "1) 🏢 Kurum Bilgileri"),
            ("normal", "Kurum adı, saymanlık kodu, vergi no, banka şubesi, IBAN ve amir bilgilerini buradan girin. Diğer tüm ekranlar aktif kuruma bağlı çalışır; önce bu ekrandan bir kurum seçili/kayıtlı olmalıdır."),

            ("altbaslik", "2) 👤 Personel İşlemleri"),
            ("normal", "Ad-soyad, TC kimlik no, sicil no ve saymanlık no ile personel eklersiniz. TC kimlik no benzersiz olmak zorundadır."),
            ("normal", "• 🗑️ Sil (Kalıcı): Kaydı veritabanından tamamen siler. Geri alınamaz."),
            ("normal", "• 🚪 Kurumdan Ayrıldı: Personeli SİLMEDEN pasife alır. Borç/kesinti geçmişi korunur."),
            ("normal", "• ♻️ Geri Aktif Et: Pasif personeli tekrar aktif yapar."),

            ("altbaslik", "3) 💰 Maaş Kalemleri"),
            ("normal", "Personelin maaşına ait kalemleri yönetirsiniz. Başlangıç ve Bitiş ayı aralığı verilir. Bitiş boş bırakılırsa maaş 'aktif' kabul edilir."),

            ("altbaslik", "4) 📄 Borç İşlemleri"),
            ("normal", "Bir personel için icra dairesi adı, dosya no, toplam borç tutarı gibi bilgilerle borç kaydı oluşturursunuz. İcra + Nafaka gibi birden fazla dosya olabilir."),

            ("altbaslik", "5) ✏️ Kesinti Girişi"),
            ("normal", "Sadece BORCU OLAN personeller bu ekrana gelir. Seçtiğiniz ay-yıl döneminde ne kadar kesinti yapıldığını işlersiniz. Otomatik olarak önceki ayın kalan borcu bulunur."),

            ("altbaslik", "6) 📝 Maaş Değişiklik İşlemleri"),
            ("normal", "Her ay için Naklen Geldi/Gitti, Ücretsiz İzin, Uzman/Baş Öğretmen gibi bilgileri ve Haciz/Nafaka ile Sağlık/Hayat Sigortası İndirimi tutarlarını girip 'Değişiklik Ekle' ile listeye eklersiniz."),
            ("normal", "• 📥 Son Aydan Devret: Bir önceki ayın kutusundaki değeri baz alır; bu ayki değişikliklere göre düzeltip cari ay kutusuna yazar."),
            ("normal", "• MEB Excel Raporu Oluştur: Resmi MEB şablonuna göre Excel dosyası üretir."),

            ("altbaslik", "7) 📊 Rapor Oluştur (Excel / PDF)"),
            ("normal", "Borcu olan personel seçtiğinizde; o borca ait güncel kalan tutar ve hangi aylara ait kesinti işlendiğini gösteren bir liste görürsünüz. Excel/PDF rapor üretebilirsiniz."),

            ("altbaslik", "8) 💾 Yedekleme"),
            ("normal", "• Program kapatılırken yedek almak isteyip istemediğiniz sorulur."),
            ("normal", "En fazla 30 yedek tutulur; aşılırsa en eskiler silinir."),
        ]

    def _sss_metni(self):
        return [
            ("baslik", "🛠️ SIK KARŞILAŞILAN SORUNLAR VE ÇÖZÜMLERİ"),
            ("normal", ""),

            ("altbaslik", "❓ Kesinti Maaş Değişiklik ekranında otomatik gelmiyor"),
            ("normal", "Dönem kutusunu değiştirdikten sonra Enter'a basın veya Tab ile çıkın. Otomatik çekim sadece bu durumda tetiklenir."),

            ("altbaslik", "❓ 'Son Aydan Devret' kutuya beklediğim sayıyı yazmıyor"),
            ("normal", "Dönem kutusunun doğru ayı gösterdiğinden emin olun. Önceki ayın kutucuğu boşsa, o ayın arşivlenmiş verisi aranır."),

            ("altbaslik", "❓ Yeni Sağlık/Hayat Sigortası alanı Excel'e yansımıyor"),
            ("normal", "Şablon dosyanızın (MAAŞ_BİLGİ_FORMU_SABLON.xlsx) T ve U sütunlarının AYRI olduğundan emin olun. Eski bir şablon kullanıyorsanız, yenisini templates klasörüne koyun."),

            ("altbaslik", "❓ Kurumda kayıtlı personel sayısı fazla görünüyor"),
            ("normal", "Ayrılan personeli 'Kurumdan Ayrıldı' ile pasife almadıysanız hâlâ sayılıyor. Silmek yerine pasife alın, geçmiş korunur."),

            ("altbaslik", "❓ Placeholder (örnek) metinler veritabanına yazılıyor mu?"),
            ("normal", "Hayır. V.2.0'dan itibaren placeholder metinler kayıt sırasında otomatik filtrelenir."),

            ("altbaslik", "❓ Aynı ay için ikinci kez kesinti girmeye çalışınca uyarı alıyorum"),
            ("normal", "Kasıtlı bir korumadır. Mevcut kaydı 'Kesinti Geçmişi' ekranından düzenleyin."),

            ("altbaslik", "❓ 'Veritabanı bulunamadı' hatası"),
            ("uyari", "Programı exe'nin bulunduğu klasörden çalıştırın. data/, logs/, templates/, yedekler/ klasörleri exe ile AYNI yerde olmalıdır."),

            ("altbaslik", "❓ Yanlış yedeği geri yükledim, eski hale dönebilir miyim?"),
            ("normal", "Evet. Her geri yüklemeden önce 'GERIYUKLEME_ONCESI' etiketli güvenlik yedeği alınır. Listeden onu seçip tekrar geri yükleyin."),

            ("altbaslik", "❓ Excel/PDF rapor hata veriyor"),
            ("normal", "templates klasörünün exe ile aynı yerde olduğundan emin olun. Ayrıca Masaüstü gibi yazma izniniz olan bir klasöre kaydedin."),

            ("altbaslik", "❓ Başka bir sorunla karşılaşırsam?"),
            ("normal", "Yardım menüsündeki 'Hata Raporu Gönder' seçeneğini kullanın. Hatanın hangi ekranda, hangi işlemden sonra olduğunu not edin."),
        ]

    def show_about(self):
        messagebox.showinfo(f"Hakkında - {_v.get_display_version()}", _v.get_about_text())

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()