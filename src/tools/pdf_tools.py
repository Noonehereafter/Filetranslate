import fitz  # PyMuPDF
import base64
import os
import json
from typing import List, Dict, Any, Optional

def get_pdf_metadata(pdf_path: str) -> str:
    """
    Get basic metadata of the PDF including total pages and TOC (if exists).
    This helps the AI plan its processing batch.
    """
    try:
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()
        metadata = {
            "total_pages": len(doc),
            "toc": toc,
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", "")
        }
        doc.close()
        return json.dumps(metadata, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

def get_page_images(pdf_path: str, start_page: int, end_page: int) -> str:
    """
    Render a range of pages to base64 images (JPEG) so the Vision AI can read them.
    Pages are 0-indexed.
    Returns a JSON string containing a list of base64 strings.
    """
    try:
        doc = fitz.open(pdf_path)
        total = len(doc)
        if start_page < 0 or start_page >= total:
            return json.dumps({"error": "start_page out of bounds"})

        end_page = min(end_page, total - 1)

        images = []
        # Zoom factor for better quality for Vision AI (e.g. 2.0 = 144 DPI)
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)

        for page_num in range(start_page, end_page + 1):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            # Get raw image bytes as jpeg
            img_bytes = pix.tobytes("jpeg")
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            images.append({
                "page_number": page_num,
                "image_base64": img_b64
            })

        doc.close()
        return json.dumps({"pages": images})
    except Exception as e:
        return json.dumps({"error": str(e)})

def extract_page_assets(pdf_path: str, page_number: int, output_dir: str) -> str:
    """
    Extract original image assets from a specific PDF page.
    Saves them to output_dir and returns their local paths relative to workspace (e.g., 'images/file.jpg').
    This is useful for the AI to embed images using standard markdown: ![caption](images/file.jpg)
    """
    try:
        doc = fitz.open(pdf_path)
        if page_number < 0 or page_number >= len(doc):
            return json.dumps({"error": "page_number out of bounds"})

        os.makedirs(output_dir, exist_ok=True)
        page = doc.load_page(page_number)
        image_list = page.get_images(full=True)

        extracted_files = []
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            if image_ext == "jpeg": image_ext = "jpg"

            filename = f"page_{page_number}_img_{img_index}.{image_ext}"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            # Return relative path for Markdown embedding
            extracted_files.append(f"images/{filename}")

        doc.close()
        return json.dumps({"extracted_images": extracted_files})
    except Exception as e:
        return json.dumps({"error": str(e)})
