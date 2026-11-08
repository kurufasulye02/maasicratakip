# utils/kurum_context.py - Aktif kurum yönetimi

from utils.db_repo import (
    get_active_kurum_id, set_active_kurum_id, clear_active_kurum_id,
    get_kurum_by_id, get_kurum_list
)


class KurumContext:
    """Uygulama genelinde aktif kurumu yönetir."""

    _callbacks = []

    @classmethod
    def get_active_id(cls):
        return get_active_kurum_id()

    @classmethod
    def get_active(cls):
        return get_kurum_by_id(cls.get_active_id())

    @classmethod
    def get_active_name(cls):
        kurum = cls.get_active()
        if kurum and kurum.get('kurum_adi'):
            return kurum['kurum_adi']
        return "Kurum secilmedi"

    @classmethod
    def set_active(cls, kurum_id):
        if kurum_id is None:
            clear_active_kurum_id()
        else:
            set_active_kurum_id(kurum_id)
        for callback in cls._callbacks[:]:
            try:
                callback(kurum_id)
            except Exception:
                cls.unregister(callback)

    @classmethod
    def get_status_text(cls):
        """Üst çubuk için aktif kurum metni."""
        kurum = cls.get_active()
        if not kurum:
            return "⚠ Aktif kurum seçilmedi"
        text = f"🏫 {kurum['kurum_adi']}"
        if kurum.get('kurum_kodu'):
            text += f" ({kurum['kurum_kodu']})"
        if kurum.get('amir_adi'):
            unvan = kurum.get('amir_unvan') or 'MÜDÜR'
            text += f"  |  {unvan}: {kurum['amir_adi']}"
        return text

    @classmethod
    def register(cls, callback):
        if callback not in cls._callbacks:
            cls._callbacks.append(callback)

    @classmethod
    def unregister(cls, callback):
        if callback in cls._callbacks:
            cls._callbacks.remove(callback)

    @classmethod
    def list_for_combobox(cls):
        """(id, display_text) listesi döndürür."""
        return [
            (k['id'], f"{k['kurum_adi'] or '(Isimsiz)'} (ID:{k['id']})")
            for k in get_kurum_list()
        ]
