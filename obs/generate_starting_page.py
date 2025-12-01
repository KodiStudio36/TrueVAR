import fitz
import re

# --- CONFIGURATION FOR CUSTOM FONTS ---
REGULAR_FONT_FILE = "obs/MomoTrustSans-Regular.ttf"
BOLD_FONT_FILE = "obs/MomoTrustDisplay-Regular.ttf"
CUSTOM_FONT_NAME = "MomoTrustFamily"
# -------------------------------------


def strip_html(text):
    return re.sub(r"<.*?>", "", text)


def pdf_to_png_transparent(pdf_path, output_png_path, dpi=64):
    """Renders the first page of a PDF file to a PNG image with a transparent background."""
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=True)
        pix.save(output_png_path)
        doc.close()
        print(f"Converted '{pdf_path}' → '{output_png_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")

def is_multiline_text(page, html, fontsize, max_width):
    """Calculates if text exceeds max_width using the font metrics."""
    plain = strip_html(html)
    
    # Use the actual custom font for accurate measurement
    try:
        font = fitz.Font(fontfile=REGULAR_FONT_FILE)
    except Exception:
        # Fallback to standard font if custom file not found
        font = fitz.Font("helv")

    # use .text_length() on the font object
    width = font.text_length(plain, fontsize=fontsize)
    
    return width > max_width


def create_starting_soon_graphics(
    input_pdf_path,
    output_pdf_path,
    output_png_path,
    title,
    location,
    court_number,
):
    """
    Inserts title, location, and court number into a PDF template,
    saves a new PDF, and exports it as transparent PNG.
    """

    doc = fitz.open(input_pdf_path)
    page = doc[0]
    MAX_WIDTH = 800

    # Prepare dynamic insertion data
    INSERTION_DATA = [
        {
            "html_text": f"<p><b>{title}</b></p>",
            "start_point": (434, 244),
            "fontsize": 48
        },
        {
            "html_text": f"<p>{location}</p>",
            "start_point": (434, 374),
            "fontsize": 48
        },
        {
            "html_text": f"<p><b>{court_number}</b></p>",
            "start_point": (434, 610),
            "fontsize": 48
        },
    ]

    if not is_multiline_text(page, INSERTION_DATA[0]["html_text"], INSERTION_DATA[0]["fontsize"], MAX_WIDTH):
        INSERTION_DATA[0] = {
            "html_text": f"<p><b><br>{title}</b></p>",
            "start_point": (434, 244),
            "fontsize": 48
        }

    print(INSERTION_DATA)

    # Global CSS with custom fonts
    CSS_STRING = f"""
    @font-face {{
        font-family: "{CUSTOM_FONT_NAME}";
        src: url("{REGULAR_FONT_FILE}");
        font-weight: normal;
        font-style: normal;
    }}
    @font-face {{
        font-family: "{CUSTOM_FONT_NAME}";
        src: url("{BOLD_FONT_FILE}");
        font-weight: bold;
        font-style: normal;
    }}

    p {{
        font-family: "{CUSTOM_FONT_NAME}";
        color: #ffffff;
        font-weight: normal;
    }}
    b {{
        font-weight: bold;
    }}
    """

    # Insert text blocks
    for item in INSERTION_DATA:
        x, y = item["start_point"]
        insertion_rect = fitz.Rect(x, y, x + MAX_WIDTH,
                                   y + item["fontsize"] * 1.5 * 2.5)

        current_css = CSS_STRING + f"p {{ font-size: {item['fontsize']}pt; }}"

        page.insert_htmlbox(
            insertion_rect,
            item["html_text"],
            css=current_css,
        )

        print(f"Inserted: {item['html_text']} at {item['start_point']}")

    # Save new PDF
    doc.save(output_pdf_path, garbage=4, deflate=True, clean=True)
    doc.close()
    print(f"PDF saved → {output_pdf_path}")

    # Convert to PNG
    pdf_to_png_transparent(output_pdf_path, output_png_path)
    print(f"PNG saved → {output_png_path}")

create_starting_soon_graphics(
    input_pdf_path="obs/starting_soon_template.pdf",
    output_pdf_path="obs/starting_soon_updated.pdf",
    output_png_path="obs/starting_soon.png",
    title="Majstrovstvá Slovenskej Republiky 2025",
    location="PALACKÉHO KOŠICE, SLOVAKIA",
    court_number="COURT 1"
)
