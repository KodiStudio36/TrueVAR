import fitz
import re
import os
import json
from PyQt5.QtCore import QObject, pyqtSignal

# --- CONFIGURATION ---
REGULAR_FONT_FILE = "obs/MomoTrustSans-Regular.ttf"
BOLD_FONT_FILE = "obs/MomoTrustDisplay-Regular.ttf"
CUSTOM_FONT_NAME = "MomoTrustFamily"
CACHE_FILE = "obs/asset_cache.json"

def strip_html(text):
    return re.sub(r"<.*?>", "", text)

def pdf_to_png_transparent(pdf_path, output_png_path, dpi=64):
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=True)
        pix.save(output_png_path)
        doc.close()
        print(f"[AssetWorker] Converted PDF to PNG: {output_png_path}")
    except Exception as e:
        print(f"[AssetWorker] PNG Conversion Error: {e}")
        raise e

def is_multiline_text(html, fontsize, max_width):
    plain = strip_html(html)
    try:
        font = fitz.Font(fontfile=REGULAR_FONT_FILE)
    except Exception:
        font = fitz.Font("helv")
    
    width = font.text_length(plain, fontsize=fontsize)
    return width > max_width

class AssetWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, tournament_data):
        super().__init__()
        self.data = tournament_data
        
        # Paths
        self.input_pdf = "obs/starting_soon_template.pdf"
        self.output_pdf = "obs/starting_soon_updated.pdf"
        self.output_png = "obs/starting_soon.png"

    def run(self):
        try:
            # 1. Prepare the current "Signature" of the data
            current_payload = {
                "name": str(self.data.get('name', 'N/A')).upper(),
                "location": str(self.data.get('location', 'N/A')).upper(),
                "id": str(self.data.get('id', '1'))
            }
            court_num = f"COURT {current_payload['id']}"

            # 2. Check if we can skip generation
            if self._is_cache_valid(current_payload):
                print(f"[AssetWorker] Skipping generation: Assets for '{current_payload['name']}' already exist.")
                self.finished.emit()
                return

            # 3. Generate if cache is invalid or missing
            print(f"[AssetWorker] Generating new assets for: {current_payload['name']}")
            self._generate_graphics(current_payload['name'], current_payload['location'], court_num)
            
            # 4. Save this data as the new "Last used" state
            self._update_cache(current_payload)
            
            self.finished.emit()
        except Exception as e:
            print(f"[AssetWorker] FATAL ERROR: {e}")
            self.error.emit(str(e))

    def _is_cache_valid(self, current_payload):
        """Returns True if the PNG exists and matches the current data."""
        # If the file is missing, we MUST regenerate
        if not os.path.exists(self.output_png):
            return False

        # If the cache info file is missing, we MUST regenerate
        if not os.path.exists(CACHE_FILE):
            return False

        try:
            with open(CACHE_FILE, 'r') as f:
                last_payload = json.load(f)
            
            # Compare all keys
            return all(current_payload.get(k) == last_payload.get(k) for k in current_payload)
        except Exception:
            return False

    def _update_cache(self, current_payload):
        """Saves current data to the cache file."""
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, 'w') as f:
                json.dump(current_payload, f)
        except Exception as e:
            print(f"[AssetWorker] Warning: Could not save cache file: {e}")

    def _generate_graphics(self, title, location, court_number):
        if not os.path.exists(self.input_pdf):
            raise FileNotFoundError(f"Template not found: {self.input_pdf}")

        doc = fitz.open(self.input_pdf)
        page = doc[0]
        MAX_WIDTH = 800

        INSERTION_DATA = [
            {"html_text": f"<p><b>{title}</b></p>", "start_point": (434, 244), "fontsize": 48},
            {"html_text": f"<p>{location}</p>", "start_point": (434, 374), "fontsize": 48},
            {"html_text": f"<p><b>{court_number}</b></p>", "start_point": (434, 670), "fontsize": 48},
        ]

        if not is_multiline_text(INSERTION_DATA[0]["html_text"], INSERTION_DATA[0]["fontsize"], MAX_WIDTH):
            INSERTION_DATA[0]["html_text"] = f"<p><b><br>{title}</b></p>"

        CSS_STRING = f"""
        @font-face {{ font-family: "{CUSTOM_FONT_NAME}"; src: url("{REGULAR_FONT_FILE}"); font-weight: normal; }}
        @font-face {{ font-family: "{CUSTOM_FONT_NAME}"; src: url("{BOLD_FONT_FILE}"); font-weight: bold; }}
        p {{ font-family: "{CUSTOM_FONT_NAME}"; color: #ffffff; margin: 0; padding: 0; }}
        b {{ font-weight: bold; }}
        """

        for item in INSERTION_DATA:
            x, y = item["start_point"]
            insertion_rect = fitz.Rect(x, y, x + MAX_WIDTH, y + item["fontsize"] * 3.75)
            current_css = CSS_STRING + f"p {{ font-size: {item['fontsize']}pt; }}"
            page.insert_htmlbox(insertion_rect, item["html_text"], css=current_css)

        doc.save(self.output_pdf, garbage=4, deflate=True, clean=True)
        doc.close()
        pdf_to_png_transparent(self.output_pdf, self.output_png)