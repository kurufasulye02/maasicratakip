# utils/navigation.py - Navigasyon çubuğu

import tkinter as tk
from tkinter import ttk
from utils.theme import ThemeManager

class NavigationBar:
    """Sayfa navigasyon çubuğu"""
    
    # YENİ SIRALAMA (İş akışına göre)
    PAGES = [
        {'id': 'kurum', 'name': '🏢 Kurum Bilgileri', 'order': 1},
        {'id': 'personel', 'name': '👤 Personel İşlemleri', 'order': 2},
        {'id': 'maas', 'name': '💰 Maaş Kalemleri', 'order': 3},
        {'id': 'borc', 'name': '📄 Borç İşlemleri', 'order': 4},
        {'id': 'kesinti', 'name': '✏️ Kesinti Girişi', 'order': 5},
        {'id': 'rapor', 'name': '📊 Rapor Oluştur', 'order': 6},
        {'id': 'maas_degisiklik', 'name': '📝 Maaş Değişiklik İşlemleri', 'order': 7}
    ]
    
    def __init__(self, parent, main_window, current_page):
        self.parent = parent
        self.main_window = main_window
        self.current_page = current_page
        self.frame = None
        self.create_widgets()
    
    def create_widgets(self):
        """Navigasyon çubuğunu oluştur"""
        theme = ThemeManager.get_theme()
        
        # Ana çerçeve
        self.frame = tk.Frame(
            self.parent,
            bg=theme['nav_bg'],
            relief=tk.RAISED,
            bd=1,
            highlightthickness=0
        )
        self.frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # İçerik
        inner = tk.Frame(self.frame, bg=theme['nav_bg'])
        inner.pack(pady=10, padx=20)
        
        # Geri Butonu
        self.btn_geri = self.create_nav_button(
            inner, 
            "◀ Geri", 
            self.go_back,
            "left"
        )
        self.btn_geri.pack(side=tk.LEFT, padx=5)
        
        # Ana Sayfa Butonu
        self.btn_home = self.create_nav_button(
            inner, 
            "🏠 Ana Sayfa", 
            self.go_home,
            "home"
        )
        self.btn_home.pack(side=tk.LEFT, padx=20)
        
        # İleri Butonu
        self.btn_ileri = self.create_nav_button(
            inner, 
            "İleri ▶", 
            self.go_forward,
            "right"
        )
        self.btn_ileri.pack(side=tk.LEFT, padx=5)
        
        # Sayfa bilgisi (sağda)
        page_info = tk.Label(
            inner,
            text=f"📄 {self.get_page_name(self.current_page)}",
            font=("Segoe UI", 10),
            bg=theme['nav_bg'],
            fg=theme['label_secondary']
        )
        page_info.pack(side=tk.RIGHT, padx=20)
    
    def create_nav_button(self, parent, text, command, position):
        """Navigasyon butonu oluştur"""
        theme = ThemeManager.get_theme()
        
        # Eğer sayfa geçişi uygun değilse butonu pasif yap
        is_active = True
        current_order = self.get_page_order(self.current_page)
        
        if position == 'left' and current_order <= 1:
            is_active = False
        elif position == 'right' and current_order >= len(self.PAGES):
            is_active = False
        elif position == 'home':
            is_active = True
        
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            bg=theme['button_secondary'] if is_active else theme['button_gray'],
            fg=theme['button_secondary_fg'] if is_active else theme['button_gray_fg'],
            relief=tk.FLAT,
            cursor="hand2" if is_active else "arrow",
            padx=15,
            pady=5,
            command=command if is_active else None,
            state=tk.NORMAL if is_active else tk.DISABLED
        )
        
        # Hover efekti (sadece aktifse)
        if is_active:
            def on_enter(e):
                btn.config(bg=theme['button_primary'])
            def on_leave(e):
                btn.config(bg=theme['button_secondary'])
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        return btn
    
    def get_page_order(self, page_id):
        """Sayfanın sırasını döndür"""
        for p in self.PAGES:
            if p['id'] == page_id:
                return p['order']
        return 0
    
    def get_page_name(self, page_id):
        """Sayfanın adını döndür"""
        for p in self.PAGES:
            if p['id'] == page_id:
                return p['name']
        return page_id
    
    def get_page_by_order(self, order):
        """Sıraya göre sayfa ID'sini döndür"""
        for p in self.PAGES:
            if p['order'] == order:
                return p['id']
        return None
    
    def go_back(self):
        """Geri git"""
        current_order = self.get_page_order(self.current_page)
        if current_order > 1:
            target_page = self.get_page_by_order(current_order - 1)
            self.navigate_to(target_page)
    
    def go_forward(self):
        """İleri git"""
        current_order = self.get_page_order(self.current_page)
        if current_order < len(self.PAGES):
            target_page = self.get_page_by_order(current_order + 1)
            self.navigate_to(target_page)
    
    def go_home(self):
        """Ana sayfaya git"""
        self.main_window.show_welcome()
    
    def navigate_to(self, page_id):
        """Belirtilen sayfaya git"""
        self.current_page = page_id
        if page_id == 'kurum':
            self.main_window.show_kurum()
        elif page_id == 'personel':
            self.main_window.show_personel()
        elif page_id == 'maas':
            self.main_window.show_maas()
        elif page_id == 'borc':
            self.main_window.show_borc()
        elif page_id == 'kesinti':
            self.main_window.show_kesinti()
        elif page_id == 'rapor':
            self.main_window.show_rapor()
        elif page_id == 'maas_degisiklik':
            self.main_window.show_maas_degisiklik()