# utils/pdf_export.py - PDF rapor oluşturma (V.3.0 - save() eklendi)

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile


class PDFExporter:
    def __init__(self, personel_adi, personel_id, secili_borc_id=None, saymanlik_no="", tc_no=""):
        self.personel_adi = personel_adi
        self.personel_id = personel_id
        self.secili_borc_id = secili_borc_id
        self.saymanlik_no = saymanlik_no
        self.tc_no = tc_no
        self.secili_ay = None
        self.kurum_adi = ""
        self.kurum_kodu = ""
        self.vergi_no = ""
        self.mudur_adi = ""
        self.mudur_unvan = ""
        self.font_registered = False
        self._last_temp_file = None  # V.2.0: save() için

    def register_font(self):
        if self.font_registered:
            return

        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/ARIAL.TTF",
            "C:/Windows/Fonts/ariali.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/Library/Fonts/Arial.ttf",
        ]

        font_found = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('UnicodeFont', font_path))
                    bold_path = font_path.replace('.ttf', 'bd.ttf')
                    if os.path.exists(bold_path):
                        pdfmetrics.registerFont(TTFont('UnicodeFont-Bold', bold_path))
                    else:
                        pdfmetrics.registerFont(TTFont('UnicodeFont-Bold', font_path))
                    font_found = True
                    break
                except Exception:
                    continue

        if not font_found:
            pdfmetrics.registerFont(TTFont('UnicodeFont', 'Helvetica'))
            pdfmetrics.registerFont(TTFont('UnicodeFont-Bold', 'Helvetica-Bold'))

        self.font_registered = True

    def set_kurum_bilgileri(self, kurum_adi, kurum_kodu, vergi_no, mudur_adi, mudur_unvan):
        self.kurum_adi = kurum_adi
        self.kurum_kodu = kurum_kodu
        self.vergi_no = vergi_no
        self.mudur_adi = mudur_adi
        self.mudur_unvan = mudur_unvan

    def create_report(self, maas_data, borc_data, kesinti_data, tum_borclar=None, secili_ay=None):
        self.secili_ay = secili_ay
        self.register_font()
        return self.create_pdf(maas_data, borc_data, kesinti_data, tum_borclar)

    def save(self, filename):
        """V.2.0: create_report ile üretilen temp dosyayı belirtilen yola kopyalar."""
        import shutil
        if not self._last_temp_file or not os.path.exists(self._last_temp_file):
            raise FileNotFoundError("Önce create_report() çağrılmalı.")
        shutil.copy2(self._last_temp_file, filename)
        try:
            os.unlink(self._last_temp_file)
        except OSError:
            pass
        self._last_temp_file = None
        return filename

    def create_pdf(self, maas_data, borc_data, kesinti_data, tum_borclar=None):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        self._last_temp_file = temp_file.name

        doc = SimpleDocTemplate(
            temp_file.name,
            pagesize=landscape(A4),
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'],
            fontName='UnicodeFont-Bold', fontSize=16, alignment=TA_CENTER, spaceAfter=10)
        header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'],
            fontName='UnicodeFont', fontSize=10, alignment=TA_LEFT, spaceAfter=3)
        cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'],
            fontName='UnicodeFont', fontSize=9, alignment=TA_CENTER)
        cell_right_style = ParagraphStyle('CellRightStyle', parent=styles['Normal'],
            fontName='UnicodeFont', fontSize=9, alignment=TA_RIGHT)
        bold_center_style = ParagraphStyle('BoldCenterStyle', parent=styles['Normal'],
            fontName='UnicodeFont-Bold', fontSize=9, alignment=TA_CENTER)
        mudur_style = ParagraphStyle('MudurStyle', parent=styles['Normal'],
            fontName='UnicodeFont-Bold', fontSize=11, alignment=TA_RIGHT)
        unvan_style = ParagraphStyle('UnvanStyle', parent=styles['Normal'],
            fontName='UnicodeFont', fontSize=10, alignment=TA_RIGHT)
        date_style = ParagraphStyle('DateStyle', parent=styles['Normal'],
            fontName='UnicodeFont', fontSize=10, alignment=TA_RIGHT)

        if self.secili_ay:
            ay_yil = self.secili_ay
        else:
            ay_yil = kesinti_data[0].get('ay_yil', datetime.now().strftime("%Y / %B")) if kesinti_data else datetime.now().strftime("%Y / %B")

        try:
            ay_parca = ay_yil.split('-')
            if len(ay_parca) == 2:
                yil = ay_parca[0]
                ay_num = int(ay_parca[1])
                aylar = ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN",
                         "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"]
                ay_adi = aylar[ay_num - 1]
                ay_yil_formatli = f"{yil} {ay_adi}"
            else:
                ay_yil_formatli = ay_yil
        except (ValueError, IndexError):
            ay_yil_formatli = ay_yil

        story = []

        kurum_data = [
            ["KURUM / BİRİM ADI", ":", self.kurum_adi],
            ["KURUM KODU", ":", self.kurum_kodu],
            ["KURUM VERGİ NO", ":", self.vergi_no],
        ]
        kurum_table = Table(kurum_data, colWidths=[100, 6, 220])
        kurum_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'UnicodeFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))

        ay_yil_table = Table([["YIL/AY", ay_yil_formatli]], colWidths=[55, 75])
        ay_yil_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'UnicodeFont-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        ust_satir = Table([[kurum_table, ay_yil_table]], colWidths=[doc.width - 150, 150])
        ust_satir.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(ust_satir)
        story.append(Spacer(1, 5*mm))

        story.append(Paragraph("İCRA / NAFAKA EMANET LİSTESİ", title_style))
        story.append(Spacer(1, 5*mm))

        data = []
        row1 = [
            Paragraph("BORÇLUYA AİT BİLGİLER", bold_center_style), "", "",
            Paragraph("İCRA DAİRESİNE AİT BİLGİLER", bold_center_style), "",
            Paragraph("BORCA AİT BİLGİLER", bold_center_style), "", "", "", ""
        ]
        data.append(row1)

        row2 = [
            Paragraph("BORÇLUNUN ADI SOYADI", bold_center_style),
            Paragraph("SAYMANLIK NO.", bold_center_style),
            Paragraph("T.C. KİMLİK NO.", bold_center_style),
            Paragraph("İCRA DAİRE ADI", bold_center_style),
            Paragraph("İCRA DOSYA NO.", bold_center_style),
            Paragraph("T.DOSYAYA OLAN BORCU", bold_center_style),
            Paragraph("TOPLAM YAPILAN KESİNTİ MİK.", bold_center_style),
            Paragraph("KALAN BORÇ MİK.", bold_center_style),
            Paragraph("BU AY KESİLECEK OLAN", bold_center_style),
            Paragraph("BU AY SONU KALAN BORÇ", bold_center_style)
        ]
        data.append(row2)

        if kesinti_data:
            kesinti = kesinti_data[0]
            borc = next((b for b in borc_data if b['id'] == kesinti['borc_id']), {})

            row3 = [
                Paragraph(self.personel_adi, cell_style),
                Paragraph(str(self.saymanlik_no), cell_style),
                Paragraph(str(self.tc_no), cell_style),
                Paragraph(borc.get('icra_daire_adi', ''), cell_style),
                Paragraph(borc.get('dosya_no', ''), cell_style),
                Paragraph(f"{borc.get('toplam_borc', 0):,.2f}", cell_right_style),
                Paragraph(f"{kesinti.get('toplam_kesinti', 0):,.2f}", cell_right_style),
                Paragraph(f"{kesinti.get('onceki_kalan', 0):,.2f}", cell_right_style),
                Paragraph(f"{kesinti.get('kesilen_tutar', 0):,.2f}", cell_right_style),
                Paragraph(f"{kesinti.get('ay_sonu_kalan', 0):,.2f}", cell_right_style)
            ]
            data.append(row3)

        col_oranlari = [60, 30, 58, 46, 35, 45, 46, 45, 45, 45]
        oran_toplami = sum(col_oranlari)
        col_widths = [doc.width * (o / oran_toplami) for o in col_oranlari]
        table = Table(data, colWidths=col_widths)

        table_style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'UnicodeFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
            ('SPAN', (0, 0), (2, 0)),
            ('SPAN', (3, 0), (4, 0)),
            ('SPAN', (5, 0), (9, 0)),
        ])
        table.setStyle(table_style)
        story.append(table)
        story.append(Spacer(1, 5*mm))

        siradaki_borclar = []
        if tum_borclar and self.secili_borc_id:
            for b in tum_borclar:
                if b['id'] > self.secili_borc_id:
                    siradaki_borclar.append(b)

        if siradaki_borclar:
            story.append(Paragraph("SIRADAKİ İCRALAR VE KESİNTİ MİKTARLARI",
                                   ParagraphStyle('SubTitle', parent=styles['Heading2'],
                                                 fontName='UnicodeFont-Bold', fontSize=11, alignment=TA_CENTER)))
            story.append(Spacer(1, 3*mm))

            data2 = []
            data2.append([
                Paragraph("İCRA DAİRE ADI", bold_center_style),
                Paragraph("DOSYA NO", bold_center_style),
                Paragraph("TOPLAM BORÇ", bold_center_style),
                Paragraph("KESİLEN TUTAR", bold_center_style),
                Paragraph("KALAN BORÇ", bold_center_style)
            ])

            for borc in siradaki_borclar:
                toplam_kesinti = 0
                kalan_borc = borc.get('toplam_borc', 0)

                try:
                    from database import db_connection
                    referans_ay = self.secili_ay or borc.get('ay_yil') or ''

                    with db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT ay_sonu_kalan FROM kesinti_takip
                            WHERE borc_id = ? AND ay_yil <= ?
                            ORDER BY ay_yil DESC, id DESC LIMIT 1
                        """, (borc['id'], referans_ay))
                        son_kayit = cursor.fetchone()
                        if son_kayit and son_kayit[0] is not None:
                            kalan_borc = son_kayit[0]

                        cursor.execute("""
                            SELECT SUM(kesilen_tutar) FROM kesinti_takip
                            WHERE borc_id = ? AND ay_yil <= ?
                        """, (borc['id'], referans_ay))
                        toplam_satir = cursor.fetchone()
                        toplam_kesinti = (toplam_satir[0] or 0) if toplam_satir else 0
                except Exception as e:
                    from utils.logger import log_exception_context
                    log_exception_context("PDF raporu: borç durumu hesaplanamadı", e)
                    toplam_kesinti = 0
                    kalan_borc = borc.get('toplam_borc', 0)

                data2.append([
                    Paragraph(borc.get('icra_daire_adi', ''), cell_style),
                    Paragraph(borc.get('dosya_no', ''), cell_style),
                    Paragraph(f"{borc.get('toplam_borc', 0):,.2f}", cell_right_style),
                    Paragraph(f"{toplam_kesinti:,.2f}", cell_right_style),
                    Paragraph(f"{kalan_borc:,.2f}", cell_right_style)
                ])

            table2_oranlari = [80, 55, 55, 55, 55]
            table2_toplam = sum(table2_oranlari)
            table2_widths = [doc.width * (o / table2_toplam) for o in table2_oranlari]
            table2 = Table(data2, colWidths=table2_widths)
            table2_style = TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'UnicodeFont'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ])
            table2.setStyle(table2_style)
            story.append(table2)
            story.append(Spacer(1, 5*mm))

        story.append(Paragraph("NOT - 1: İcra Talimat Numaraları Mutlaka Belirtilecektir.", header_style))
        story.append(Paragraph("ÖRNEK: 2005/250 Tal", header_style))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("NOT - 2: Formun Dolduruluşu A=B=C=D=E", header_style))
        story.append(Spacer(1, 5*mm))

        story.append(Paragraph(f"Tarih: {datetime.now().strftime('%d.%m.%Y')}", date_style))
        story.append(Spacer(1, 5*mm))

        story.append(Paragraph(self.mudur_adi, mudur_style))
        story.append(Paragraph(self.mudur_unvan, unvan_style))

        doc.build(story)

        return temp_file.name