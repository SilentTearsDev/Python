from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime
import textwrap

# -----------------------------
# Segéd: szöveg tördelés
# -----------------------------
def draw_wrapped_text(c, text, x, y, max_width, line_height=14, font_name="Helvetica", font_size=11):
    c.setFont(font_name, font_size)
    # nagyjából becsült karakterszám (ReportLab stringWidth-al pontosítunk)
    words = (text or "").split()
    if not words:
        return y

    line = ""
    lines = []
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, font_name, font_size) <= max_width:
            line = test
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)

    for ln in lines:
        c.drawString(x, y, ln)
        y -= line_height

    return y

# -----------------------------
# Diszkrét háttérminta (pöttyök)
# -----------------------------
def draw_background_pattern(c, width, height):
    c.saveState()
    c.setFillColorRGB(0.93, 0.94, 0.97)  # nagyon halvány
    step = 22
    r = 0.7
    # ritka pöttyök a teljes lapon
    y = 30
    while y < height - 30:
        x = 30
        while x < width - 30:
            c.circle(x, y, r, stroke=0, fill=1)
            x += step
        y += step
    c.restoreState()

# -----------------------------
# Szekció doboz (kártya)
# -----------------------------
def draw_section_box(c, x, y_top, w, h, title):
    c.saveState()
    # finom kitöltés + keret
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(0.82, 0.84, 0.88)
    c.setLineWidth(1)
    c.roundRect(x, y_top - h, w, h, 10, stroke=1, fill=1)

    # cím sáv
    c.setFillColorRGB(0.95, 0.96, 0.98)
    c.setStrokeColorRGB(0.90, 0.91, 0.94)
    c.roundRect(x, y_top - 32, w, 32, 10, stroke=1, fill=1)

    c.setFillColorRGB(0.12, 0.16, 0.22)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 14, y_top - 22, title)
    c.restoreState()

# -----------------------------
# Mező (label + value)
# -----------------------------
def draw_field(c, label, value, x_label, x_value, y, value_max_width, font_size=11):
    c.setFillColorRGB(0.25, 0.30, 0.38)
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(x_label, y, label)

    c.setFillColorRGB(0.08, 0.10, 0.14)
    y2 = draw_wrapped_text(
        c,
        value if value else "-",
        x_value,
        y,
        max_width=value_max_width,
        line_height=14,
        font_name="Helvetica",
        font_size=font_size
    )
    return y2

def safe_input(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        return ""

# -----------------------------
# Adatbekérés
# -----------------------------
print("=== Megrendelői lap kitoltése ===")
rendezveny_nev = safe_input("Rendezvény neve: ")
megrendelo = safe_input("Megrendelo neve: ")
rendezveny_ideje = safe_input("Rendezvény ideje (pl. 2026-02-10 19:00): ")
telefonszam = safe_input("Telefonszám: ")
erkezes_ideje = safe_input("Érkezés ideje (pl. 18:30): ")
vendegek_szama = safe_input("Vendégek száma: ")
asztal_elrendezes = safe_input("Asztal elrendezés: ")
etelek_italok = safe_input("Ételek / italok (röviden vagy listában): ")
extra_szolgaltatasok = safe_input("Extra szolgáltatások: ")

# Fájlnév (szép, időbélyeggel)
stamp = datetime.now().strftime("%Y%m%d_%H%M")
filename = f"megrendeloi_lap_{stamp}.pdf"

# -----------------------------
# PDF rajzolás
# -----------------------------
c = canvas.Canvas(filename, pagesize=A4)
W, H = A4

# Háttérminta
draw_background_pattern(c, W, H)

# Margók
M = 42

# Fejléc sáv
c.saveState()
c.setFillColorRGB(0.12, 0.16, 0.22)  # sötét fejlécekhez
c.roundRect(M, H - 110, W - 2*M, 70, 14, stroke=0, fill=1)

c.setFillColorRGB(1, 1, 1)
c.setFont("Helvetica-Bold", 20)
c.drawString(M + 18, H - 72, "MEGRENDELOI LAP")

c.setFont("Helvetica", 10)
c.setFillColorRGB(0.86, 0.90, 0.98)
c.drawString(M + 18, H - 92, f"Készült: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# jobb oldali “chip”
c.setFillColorRGB(0.20, 0.26, 0.36)
c.roundRect(W - M - 170, H - 96, 170, 36, 10, stroke=0, fill=1)
c.setFillColorRGB(1, 1, 1)
c.setFont("Helvetica-Bold", 11)
c.drawRightString(W - M - 14, H - 74, "Rendezvény / Megrendelés")
c.restoreState()

# Tartalom elrendezés: 2 oszlop felül, alul nagy mezők
content_top = H - 140

col_gap = 18
col_w = (W - 2*M - col_gap) / 2
left_x = M
right_x = M + col_w + col_gap

# 1) Alapadatok szekció (bal)
box_h = 190
draw_section_box(c, left_x, content_top, col_w, box_h, "Alapadatok")

y = content_top - 52
y = draw_field(c, "Rendezvény neve", rendezveny_nev, left_x + 16, left_x + 150, y, value_max_width=col_w - 170)
y -= 8
y = draw_field(c, "Megrendelo", megrendelo, left_x + 16, left_x + 150, y, value_max_width=col_w - 170)
y -= 8
y = draw_field(c, "Telefonszám", telefonszam, left_x + 16, left_x + 150, y, value_max_width=col_w - 170)

# 2) Időpontok / logisztika (jobb)
draw_section_box(c, right_x, content_top, col_w, box_h, "Idopontok és létszám")

y2 = content_top - 52
y2 = draw_field(c, "Rendezvény ideje", rendezveny_ideje, right_x + 16, right_x + 150, y2, value_max_width=col_w - 170)
y2 -= 8
y2 = draw_field(c, "Érkezés ideje", erkezes_ideje, right_x + 16, right_x + 150, y2, value_max_width=col_w - 170)
y2 -= 8
y2 = draw_field(c, "Vendég szám", vendegek_szama, right_x + 16, right_x + 150, y2, value_max_width=col_w - 170)

# Alsó nagy dobozok
below_top = content_top - box_h - 18

# Asztal elrendezés
big_h_1 = 120
draw_section_box(c, M, below_top, W - 2*M, big_h_1, "Asztal elrendezés")

c.setFillColorRGB(0.08, 0.10, 0.14)
text_y = below_top - 52
text_y = draw_wrapped_text(c, asztal_elrendezes if asztal_elrendezes else "-", M + 18, text_y, max_width=W - 2*M - 36, line_height=14)

# Ételek-italok
below_top2 = below_top - big_h_1 - 16
big_h_2 = 150
draw_section_box(c, M, below_top2, W - 2*M, big_h_2, "Ételek / italok")

c.setFillColorRGB(0.08, 0.10, 0.14)
text_y = below_top2 - 52
text_y = draw_wrapped_text(c, etelek_italok if etelek_italok else "-", M + 18, text_y, max_width=W - 2*M - 36, line_height=14)

# Extra szolgáltatások
below_top3 = below_top2 - big_h_2 - 16
big_h_3 = 130
draw_section_box(c, M, below_top3, W - 2*M, big_h_3, "Extra szolgáltatások")

c.setFillColorRGB(0.08, 0.10, 0.14)
text_y = below_top3 - 52
text_y = draw_wrapped_text(c, extra_szolgaltatasok if extra_szolgaltatasok else "-", M + 18, text_y, max_width=W - 2*M - 36, line_height=14)

# Aláírás + megjegyzés sáv alul
c.saveState()
footer_y = 52
c.setStrokeColorRGB(0.75, 0.78, 0.83)
c.line(M, footer_y + 40, W - M, footer_y + 40)

c.setFillColorRGB(0.25, 0.30, 0.38)
c.setFont("Helvetica", 9)
c.drawString(M, footer_y + 18, "Megrendelo aláírása:")
c.setStrokeColorRGB(0.35, 0.38, 0.45)
c.line(M + 130, footer_y + 18, W - M, footer_y + 18)

c.setFillColorRGB(0.45, 0.48, 0.55)
c.drawString(M, footer_y - 2, "Megjegyzés: A fenti adatok alapján történik a rendezvény előkészítése.")
c.restoreState()

# Mentés
c.save()
print(f"\n✅ Elkészült: {filename}")
