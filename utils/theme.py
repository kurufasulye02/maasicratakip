# utils/theme.py - Tema yöneticisi

class ThemeManager:
    """Açık/Koyu tema yönetimi"""
    
    # Açık Tema Renkleri
    LIGHT = {
        'bg': '#f0f4f8',
        'fg': '#1a1a2e',
        'header_bg': '#1a237e',
        'header_fg': '#ffffff',
        'header_sub': '#bbdefb',
        'card_bg': '#ffffff',
        'card_shadow': '#e0e0e0',
        'button_primary': '#4CAF50',
        'button_primary_fg': '#ffffff',
        'button_secondary': '#2196F3',
        'button_secondary_fg': '#ffffff',
        'button_danger': '#f44336',
        'button_danger_fg': '#ffffff',
        'button_warning': '#FFC107',
        'button_warning_fg': '#1a1a2e',
        'button_gray': '#9E9E9E',
        'button_gray_fg': '#ffffff',
        'label_text': '#1a1a2e',
        'label_secondary': '#666666',
        'entry_bg': '#ffffff',
        'entry_fg': '#1a1a2e',
        'entry_border': '#cccccc',
        'tree_bg': '#ffffff',
        'tree_alt_bg': '#f5f5f5',
        'tree_fg': '#1a1a2e',
        'tree_header_bg': '#e8e8e8',
        'tree_header_fg': '#1a1a2e',
        'frame_bg': '#f0f4f8',
        'nav_bg': '#ffffff',
        'nav_border': '#e0e0e0',
        'label_frame_bg': '#f8f9fa',
        'label_frame_fg': '#1a1a2e'
    }
    
    # Koyu Tema Renkleri
    DARK = {
        'bg': '#1a1a2e',
        'fg': '#e8e8e8',
        'header_bg': '#0d0d1a',
        'header_fg': '#ffffff',
        'header_sub': '#9fa8da',
        'card_bg': '#2d2d44',
        'card_shadow': '#1a1a2e',
        'button_primary': '#66BB6A',
        'button_primary_fg': '#1a1a2e',
        'button_secondary': '#42A5F5',
        'button_secondary_fg': '#1a1a2e',
        'button_danger': '#ef5350',
        'button_danger_fg': '#1a1a2e',
        'button_warning': '#FFD54F',
        'button_warning_fg': '#1a1a2e',
        'button_gray': '#78909C',
        'button_gray_fg': '#1a1a2e',
        'label_text': '#e8e8e8',
        'label_secondary': '#aaaaaa',
        'entry_bg': '#2d2d44',
        'entry_fg': '#e8e8e8',
        'entry_border': '#444466',
        'tree_bg': '#2d2d44',
        'tree_alt_bg': '#3a3a55',
        'tree_fg': '#e8e8e8',
        'tree_header_bg': '#3a3a55',
        'tree_header_fg': '#e8e8e8',
        'frame_bg': '#1a1a2e',
        'nav_bg': '#2d2d44',
        'nav_border': '#3a3a55',
        'label_frame_bg': '#252540',
        'label_frame_fg': '#e8e8e8'
    }
    
    _current_theme = 'light'
    _callbacks = []
    
    @classmethod
    def get_theme(cls):
        """Mevcut temayı döndür"""
        if cls._current_theme == 'dark':
            return cls.DARK
        return cls.LIGHT
    
    @classmethod
    def toggle_theme(cls):
        """Temayı değiştir ve callback'leri çağır"""
        cls._current_theme = 'dark' if cls._current_theme == 'light' else 'light'
        theme = cls.get_theme()
        # Tüm callback'leri çağır
        for callback in cls._callbacks[:]:  # Kopya üzerinde döngü
            try:
                callback(theme)
            except Exception as e:
                # Hata oluşursa callback'i kaldır
                cls.unregister_callback(callback)
        return theme
    
    @classmethod
    def set_theme(cls, theme_name):
        """Temayı ayarla"""
        if theme_name in ['light', 'dark']:
            cls._current_theme = theme_name
        theme = cls.get_theme()
        for callback in cls._callbacks[:]:
            try:
                callback(theme)
            except Exception as e:
                cls.unregister_callback(callback)
        return theme
    
    @classmethod
    def register_callback(cls, callback):
        """Tema değiştiğinde çağrılacak fonksiyon ekle"""
        if callback not in cls._callbacks:
            cls._callbacks.append(callback)
    
    @classmethod
    def unregister_callback(cls, callback):
        """Callback kaldır"""
        if callback in cls._callbacks:
            cls._callbacks.remove(callback)