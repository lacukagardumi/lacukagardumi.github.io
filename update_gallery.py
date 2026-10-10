#!/usr/bin/env python3
"""
Lāčuka Gardumi - Galerijas automātiskais atjauninātājs.
Nolasa datus no 'galerija.csv' un bildes no 'galerija/' mapes,
optimizē uz WebP un automātiski ģenerē karuseli failā 'index.html'.
"""

import os
import re
import csv
import sys
from PIL import Image, ImageEnhance, ImageFilter

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "galerija.csv")
GALERIJA_DIR = os.path.join(BASE_DIR, "galerija")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
INDEX_PATH = os.path.join(BASE_DIR, "index.html")

SVG_INSTA = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2">'
    '<rect x="3" y="3" width="18" height="18" rx="5"/>'
    '<circle cx="12" cy="12" r="4"/>'
    '</svg>'
)

SVG_HEART = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="#e5465e">'
    '<path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 '
    '4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 '
    '19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>'
    '</svg>'
)

def find_image_file(nr):
    extensions = [".jpg", ".jpeg", ".png", ".webp", ".heic", ".HEIC", ".PNG", ".JPG"]
    for ext in extensions:
        candidate = os.path.join(GALERIJA_DIR, f"{nr}{ext}")
        if os.path.exists(candidate):
            return candidate
    return None

def optimize_image(src_path, dst_path):
    # Only re-process if destination doesn't exist or source is newer
    if os.path.exists(dst_path):
        if os.path.getmtime(dst_path) >= os.path.getmtime(src_path):
            return

    with Image.open(src_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        # Center square crop
        dim = min(w, h)
        left = (w - dim) // 2
        top = (h - dim) // 2
        crop = im.crop((left, top, left + dim, top + dim))
        sq = crop.resize((640, 640), Image.Resampling.LANCZOS)
        
        # Gentle enhancement
        sq = ImageEnhance.Color(sq).enhance(1.08)
        sq = ImageEnhance.Contrast(sq).enhance(1.06)
        sq = ImageEnhance.Brightness(sq).enhance(1.02)
        sq = sq.filter(ImageFilter.UnsharpMask(radius=1.2, percent=100, threshold=2))
        
        sq.save(dst_path, "WEBP", quality=86)
        print(f"  Optimizēta bilde -> {os.path.basename(dst_path)}")

def read_gallery_data():
    if not os.path.exists(CSV_PATH):
        print(f"Kļūda: Fails {CSV_PATH} nav atrasts!")
        return []

    # Detect delimiter (; or ,)
    with open(CSV_PATH, "r", encoding="utf-8-sig", errors="ignore") as f:
        first_line = f.readline()
        delimiter = ";" if ";" in first_line else ","

    entries = []
    with open(CSV_PATH, "r", encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            # Clean keys
            cleaned = {k.strip(): v.strip() for k, v in row.items() if k}
            nr = cleaned.get("Nr") or cleaned.get("Numurs") or cleaned.get("nr")
            title = cleaned.get("Nosaukums") or cleaned.get("nosaukums") or ""
            cat = cleaned.get("Kategorija") or cleaned.get("kategorija") or ""
            link = cleaned.get("Instagram_Links") or cleaned.get("Links") or cleaned.get("links") or cleaned.get("Instagram") or ""
            if nr:
                entries.append({
                    "nr": nr,
                    "title": title,
                    "cat": cat,
                    "link": link or "https://www.instagram.com/lacuka.gardumi/"
                })
    return entries

def build_slides_html(entries):
    slides = []
    for item in entries:
        nr = item["nr"]
        title = item["title"]
        cat = item["cat"]
        link = item["link"]
        
        src_img = find_image_file(nr)
        dst_img_name = f"g-{nr}.webp"
        dst_img_path = os.path.join(ASSETS_DIR, dst_img_name)
        
        if src_img:
            optimize_image(src_img, dst_img_path)
            img_rel = f"assets/{dst_img_name}"
        else:
            # Fallback to existing asset if available
            img_rel = f"assets/g-{nr}.webp"
            print(f"  Brīdinājums: bilde 'galerija/{nr}.*' nav atrasta, izmanto {img_rel}")

        slide_html = f"""          <a href="{link}" target="_blank" rel="noopener" class="carousel-slide" aria-label="{title}">
            <div class="carousel-media">
              <img src="{img_rel}" alt="{title}" width="640" height="640" loading="lazy" decoding="async">
              <div class="carousel-overlay">
                <span class="carousel-overlay-text">
                  {SVG_INSTA}
                  Instagram
                </span>
                {SVG_HEART}
              </div>
            </div>
            <div class="carousel-meta">
              <span class="carousel-caption">{title}</span>
              <span class="carousel-tag">{cat}</span>
            </div>
          </a>"""
        slides.append(slide_html)

    return "\n\n".join(slides)

def update_index_html(slides_html):
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    pattern = r'(<div class="carousel-track">).*?(</div>\s*</div>\s*<button class="carousel-btn next")'
    replacement = r'\1\n\n' + slides_html + r'\n\n        \2'
    
    new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    if new_html == html:
        print("Brīdinājums: Carousel track netika aizstāts (pārbaudi regulāro izteiksmi)!")
        return False

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(new_html)

    print("Veiksmīgi atjaunināts index.html!")
    return True

def main():
    print("=== Lāčuka Gardumi Galerijas Sinhronizācija ===")
    entries = read_gallery_data()
    print(f"Atrasti {len(entries)} ieraksti tabulā galerija.csv")
    slides_html = build_slides_html(entries)
    success = update_index_html(slides_html)
    if success:
        print("Gatavs! Galerija ir sinhronizēta ar datiem.")

if __name__ == "__main__":
    main()
