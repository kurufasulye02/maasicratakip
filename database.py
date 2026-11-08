# database.py - Veritabanı işlemleri (EXE UYUMLU) - V.2.0

import sqlite3
import os
import sys
from contextlib import contextmanager

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, 'data', 'icra.db')


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_connection():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_column(cursor, table, column, definition):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_database():
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kurum (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kurum_adi TEXT NOT NULL,
                kurum_kodu TEXT,
                vergi_no TEXT,
                amir_adi TEXT,
                amir_unvan TEXT DEFAULT 'MÜDÜR',
                saymanlik_kod TEXT,
                banka_subesi TEXT,
                iban TEXT,
                amir_telefon TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kurum_id INTEGER,
                ad_soyad TEXT NOT NULL,
                sicil_no TEXT,
                tc_no TEXT UNIQUE,
                saymanlik_no TEXT,
                aktif INTEGER DEFAULT 1,
                FOREIGN KEY (kurum_id) REFERENCES kurum(id)
            )
        ''')
        _ensure_column(cursor, 'personel', 'aktif', 'INTEGER DEFAULT 1')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maas_kalemleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personel_id INTEGER,
                baslangic_ay TEXT NOT NULL,
                bitis_ay TEXT,
                aylik_tutar REAL DEFAULT 0,
                taban_aylik REAL DEFAULT 0,
                ek_gosterge REAL DEFAULT 0,
                yan_odeme REAL DEFAULT 0,
                kidem REAL DEFAULT 0,
                ozel_hizmet REAL DEFAULT 0,
                makam REAL DEFAULT 0,
                dil REAL DEFAULT 0,
                ek_odeme_666 REAL DEFAULT 0,
                ek_tazminat REAL DEFAULT 0,
                ilave_odeme REAL DEFAULT 0,
                FOREIGN KEY (personel_id) REFERENCES personel(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS borc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personel_id INTEGER,
                icra_daire_adi TEXT NOT NULL,
                dosya_no TEXT NOT NULL,
                toplam_borc REAL NOT NULL,
                onceki_kesinti REAL DEFAULT 0,
                borc_turu TEXT DEFAULT 'icra',
                aylik_nafaka_tutari REAL DEFAULT 0,
                FOREIGN KEY (personel_id) REFERENCES personel(id)
            )
        ''')
        _ensure_column(cursor, 'borc', 'onceki_kesinti', 'REAL DEFAULT 0')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kesinti_takip (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                borc_id INTEGER,
                ay_yil TEXT NOT NULL,
                onceki_kalan REAL,
                hesaplanan_kesinti REAL,
                kesilen_tutar REAL,
                ay_sonu_kalan REAL,
                aciklama TEXT,
                FOREIGN KEY (borc_id) REFERENCES borc(id),
                UNIQUE (borc_id, ay_yil)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ayarlar (
                anahtar TEXT PRIMARY KEY,
                deger TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maas_arsiv (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kurum_id INTEGER,
                arsiv_adi TEXT NOT NULL,
                donem_ay_yil TEXT NOT NULL,
                olusturma_tarihi TEXT,
                veri_json TEXT NOT NULL,
                FOREIGN KEY (kurum_id) REFERENCES kurum(id)
            )
        ''')

        # --- UNIQUE index (kesinti_takip için) ---
        try:
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_kesinti_borc_ay
                ON kesinti_takip (borc_id, ay_yil)
            ''')
        except sqlite3.OperationalError:
            pass

        # --- V.2.0: Performans index'leri ---
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_borc_personel ON borc(personel_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_maas_personel ON maas_kalemleri(personel_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_personel_kurum ON personel(kurum_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_arsiv_kurum_donem ON maas_arsiv(kurum_id, donem_ay_yil)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_kesinti_borc ON kesinti_takip(borc_id)')

        # Aktif kurum ayarı (ilk kurum varsa onu aktif yap)
        cursor.execute("SELECT deger FROM ayarlar WHERE anahtar = 'aktif_kurum_id'")
        if cursor.fetchone() is None:
            cursor.execute("SELECT id FROM kurum ORDER BY id ASC LIMIT 1")
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "INSERT INTO ayarlar (anahtar, deger) VALUES ('aktif_kurum_id', ?)",
                    (str(row[0]),)
                )

    print("Veritabani kontrol edildi (V.2.0).")
    print(f"Veritabani yolu: {DB_PATH}")


if __name__ == "__main__":
    init_database()