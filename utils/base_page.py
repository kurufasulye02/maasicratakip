# utils/base_page.py - Tüm sayfalar için temel sınıf (TEMA KALDIRILDI)

import tkinter as tk
from tkinter import ttk
from utils.theme import ThemeManager

# Tema değişikliğinde dokunulmayacak özel renkler (Hex kodları)
ACCENT_COLORS = {
    '#1a237e',  # Mavi başlık
    '#0000FF', 'blue',
    '#FF0000', 'red',
    '#008000', 'green',
    '#FFA500', 'orange',
    '#FFC107',
    '#4CAF50',
    '#2196F3',
    '#f44336',
    '#9E9E9E', # Gri
    '#795548', # Kahverengi
    '#FF9800',
    '#607D8B',
    '#9C27B0'
}

class BasePage:
    """Tüm sayfalar için temel sınıf - varsayılan açık temayı kullanır."""

    FONT = "Segoe UI"

    def __init__(self, parent):
        self.parent = parent
        self.widgets = []
        self.theme = ThemeManager.get_theme()
        self._destroyed = False

    def destroy(self):
        """Sayfa kapanırken temizlik"""
        if not self._destroyed:
            self._destroyed = True

    def styled_label(self, parent, text, bold=False, secondary=False, **kwargs):
        theme = self.theme
        font_size = kwargs.pop('font_size', 10)
        weight = "bold" if bold else "normal"
        fg = theme['label_secondary'] if secondary else theme['fg']
        if kwargs.pop('title', False):
            fg = '#1a237e'
        label = tk.Label(
            parent, text=text,
            font=(self.FONT, font_size, weight),
            bg=theme['bg'], fg=fg,
            **kwargs
        )
        return label

    def styled_entry(self, parent, width=30, **kwargs):
        theme = self.theme
        return tk.Entry(
            parent, width=width,
            font=(self.FONT, 10),
            bg=theme['entry_bg'], fg=theme['entry_fg'],
            relief=tk.SOLID, bd=1,
            **kwargs
        )

    def styled_button(self, parent, text, command, color='primary', width=12):
        theme = self.theme
        colors = {
            'primary': ('#4CAF50', 'white'),
            'secondary': ('#2196F3', 'white'),
            'warning': ('#FFC107', '#1a1a2e'),
            'danger': ('#f44336', 'white'),
            'gray': (theme['button_gray'], theme['button_gray_fg']),
        }
        bg, fg = colors.get(color, colors['primary'])
        return tk.Button(
            parent, text=text, command=command,
            font=(self.FONT, 10, "bold" if color != 'gray' else 'normal'),
            bg=bg, fg=fg, width=width, relief=tk.RAISED, bd=2, cursor="hand2"
        )

    def apply_theme(self, theme):
        self.theme = theme
        if hasattr(self, 'frame'):
            try:
                if isinstance(self.frame, tk.Frame):
                    self.frame.configure(bg=theme['bg'])
                self.update_widgets(self.frame, theme)
            except tk.TclError:
                pass

    def update_widgets(self, container, theme):
        try:
            children = container.winfo_children()
        except tk.TclError:
            return

        for widget in children:
            try:
                if isinstance(widget, tk.Label):
                    current_fg = widget.cget('fg')
                    
                    if 'bg' in widget.keys():
                        bg_val = widget['bg']
                        if bg_val not in (theme['header_bg'], '#f0f4f8', '#1a1a2e') and bg_val not in ACCENT_COLORS:
                            try:
                                widget.configure(bg=theme['bg'])
                            except tk.TclError:
                                pass
                    
                    if current_fg not in ACCENT_COLORS and current_fg != theme['header_fg']:
                        widget.configure(fg=theme['fg'])
                
                elif isinstance(widget, tk.Entry):
                    widget.configure(bg=theme['entry_bg'], fg=theme['entry_fg'])
                
                elif isinstance(widget, tk.Button):
                    if widget['bg'] in ['#9E9E9E', theme['button_gray']]:
                        widget.configure(bg=theme['button_gray'], fg=theme['button_gray_fg'])
                
                elif isinstance(widget, tk.Frame):
                    widget.configure(bg=theme['bg'])
                    self.update_widgets(widget, theme)
                
                elif isinstance(widget, (ttk.LabelFrame, ttk.Frame)):
                    self.update_widgets(widget, theme)

            except tk.TclError:
                continue

    def register_widget(self, widget):
        self.widgets.append(widget)