# utils/db_repo.py - Ortak veritabanı sorguları (V.3.2.0)

from database import db_connection


def get_setting(key, default=None):
    with db_connection() as conn:
        row = conn.execute(
            "SELECT deger FROM ayarlar WHERE anahtar = ?", (key,)
        ).fetchone()
    return row['deger'] if row else default


def set_setting(key, value):
    with db_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)",
            (key, str(value))
        )


def get_active_kurum_id():
    val = get_setting('aktif_kurum_id')
    if val:
        try:
            return int(val)
        except ValueError:
            pass
    with db_connection() as conn:
        row = conn.execute("SELECT id FROM kurum ORDER BY id ASC LIMIT 1").fetchone()
    if row:
        kid = row['id']
        set_setting('aktif_kurum_id', kid)
        return kid
    return None


def set_active_kurum_id(kurum_id):
    set_setting('aktif_kurum_id', kurum_id)


def clear_active_kurum_id():
    with db_connection() as conn:
        conn.execute("DELETE FROM ayarlar WHERE anahtar = 'aktif_kurum_id'")


def get_kurum_list():
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT id, kurum_adi, kurum_kodu, vergi_no, amir_adi, amir_unvan "
            "FROM kurum ORDER BY kurum_adi"
        ).fetchall()
    return [dict(r) for r in rows]


def get_kurum_by_id(kurum_id):
    with db_connection() as conn:
        row = conn.execute(
            "SELECT id, kurum_adi, kurum_kodu, vergi_no, amir_adi, amir_unvan "
            "FROM kurum WHERE id = ?",
            (kurum_id,)
        ).fetchone()
    return dict(row) if row else None


def get_active_kurum():
    kid = get_active_kurum_id()
    return get_kurum_by_id(kid) if kid else None


def count_personel_for_kurum(kurum_id, only_active=True):
    query = "SELECT COUNT(*) AS c FROM personel WHERE kurum_id = ?"
    if only_active:
        query += " AND (aktif IS NULL OR aktif = 1)"
    with db_connection() as conn:
        row = conn.execute(query, (kurum_id,)).fetchone()
    return row['c']


def get_personel_list(kurum_id=None, search="", only_active=True, sadece_borclu=False):
    """Personel listesini döner: (id, ad_soyad, sicil_no, tc_no, saymanlik_no, aktif).
    only_active=True iken kurumdan ayrılmış personel listelenmez.
    sadece_borclu=True ise sadece borç kaydı olan personel listelenir."""
    query = (
        "SELECT id, ad_soyad, sicil_no, tc_no, saymanlik_no, aktif "
        "FROM personel WHERE 1=1"
    )
    params = []
    if kurum_id is not None:
        query += " AND kurum_id = ?"
        params.append(kurum_id)
    if only_active:
        query += " AND (aktif IS NULL OR aktif = 1)"
    if sadece_borclu:
        query += " AND id IN (SELECT personel_id FROM borc)"
    if search:
        query += " AND (ad_soyad LIKE ? OR sicil_no LIKE ? OR tc_no LIKE ?)"
        ara = f"%{search}%"
        params.extend([ara, ara, ara])
    
    with db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    sonuc = [tuple(r) for r in rows]
    from utils.helpers import turkce_sirala_anahtari
    sonuc.sort(key=lambda r: turkce_sirala_anahtari(r[1] or ""))
    return sonuc


def personel_pasife_al(personel_id):
    with db_connection() as conn:
        conn.execute("UPDATE personel SET aktif = 0 WHERE id = ?", (personel_id,))


def personel_aktif_et(personel_id):
    with db_connection() as conn:
        conn.execute("UPDATE personel SET aktif = 1 WHERE id = ?", (personel_id,))


def count_maas_for_month(personel_id, ay):
    with db_connection() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS c FROM maas_kalemleri
            WHERE personel_id = ? AND baslangic_ay <= ?
                  AND (bitis_ay IS NULL OR bitis_ay >= ?)
        """, (personel_id, ay, ay)).fetchone()
    return row['c']


def get_borc_rows_for_personel(personel_id):
    with db_connection() as conn:
        rows = conn.execute("""
            SELECT id, icra_daire_adi, dosya_no, toplam_borc
            FROM borc WHERE personel_id = ? ORDER BY id ASC
        """, (personel_id,)).fetchall()
    return [dict(r) for r in rows]