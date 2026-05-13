import os
import json
from src.tools.pdf_tools import get_pdf_metadata, get_page_images
from src.tools.epub_tools import init_epub, append_chapter_to_epub, finish_epub_build

def run_mock_agent(pdf_path: str = "Compensation - Gerhart, Barry;Newman, Jerry;Mi.pdf"):
    print("--- [MOCK AI] Bắt đầu quá trình ---")

    # BƯỚC 1: Lấy metadata
    print("[MOCK AI] Đang gọi get_pdf_metadata...")
    meta_json = get_pdf_metadata(pdf_path)
    meta = json.loads(meta_json)
    print(f"Metadata nhận được: {meta.get('title', 'N/A')} - Tổng số trang: {meta.get('total_pages', 0)}")

    # BƯỚC 2: Khởi tạo ePub
    print("[MOCK AI] Đang gọi init_epub...")
    init_res = json.loads(init_epub("Compensation Test Hybrid Pipeline", "Barry Gerhart & AI"))
    workspace_dir = init_res.get("workspace")
    images_dir = init_res.get("images_dir")
    print(f"Khởi tạo workspace tại: {workspace_dir}")

    import fitz
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()
    except Exception as e:
        print(f"Lỗi khi đọc file PDF: {e}")
        return

    # BƯỚC 3: Giả lập quá trình đọc
    # Nếu file PDF có đủ trang thì đọc trang 75-76 (chứa bảng/ảnh mẫu). Nếu file ngắn hơn, đọc 2 trang cuối hoặc trang có sẵn.
    if total_pages >= 77:
        start_page = 75
        end_page = 76
    else:
        start_page = 0
        end_page = min(1, total_pages - 1)

    # 3a. Gọi hàm lấy hình ảnh
    print(f"\n[MOCK AI] Đang gọi get_page_images từ trang {start_page} đến {end_page}...")
    img_res = json.loads(get_page_images(pdf_path, start_page, end_page))

    if "error" in img_res:
        print(f"Lỗi khi lấy ảnh: {img_res['error']}")
        return

    images_count = len(img_res.get('pages', []))
    print(f"[MOCK AI] Đã nhận được {images_count} hình ảnh để đọc bằng Vision AI.")

    # 3b. Gọi extract_page_assets để bóc tách ảnh gốc (giả định có ảnh ở trang 75)
    from src.tools.pdf_tools import extract_page_assets
    print(f"[MOCK AI] Đang gọi extract_page_assets tại trang {start_page}...")
    assets_res = json.loads(extract_page_assets(pdf_path, start_page, images_dir))
    extracted_images = assets_res.get("extracted_images", [])

    # Mô phỏng AI quyết định lấy ảnh đầu tiên
    img_markdown = f"![Sơ đồ Lương thưởng]({extracted_images[0]})" if extracted_images else "*(Không tìm thấy ảnh gốc)*"

    # 3c. Giả lập AI nhận diện và dịch (có chèn ảnh vật lý):
    print(f"[MOCK AI] Đang phân tích Vision và tạo nội dung Markdown (Hybrid Pipeline)...")
    mock_translated_markdown = f"""## Chương 2: Chiến lược lương thưởng (Trang {start_page}-{end_page})

Dưới đây là ví dụ về cách AI Semantic Engine phân tích bảng biểu phức tạp và chèn hình ảnh vật lý vào file.

### Hình ảnh minh họa

{img_markdown}

> **Nhận xét của AI:** Tôi đã sử dụng tool `extract_page_assets` để lưu ảnh gốc và chèn nó vào Markdown thành công. Thay vì đọc mờ nhòe hay chỉ dùng caption chay, giờ đây ảnh gốc đã nằm trong `.epub`.

### Bảng biểu: Cơ cấu thu nhập theo cấp bậc (Xử lý Semantic Parsing)

Trong trang {start_page}, tác giả có đề cập đến một bảng dữ liệu chi tiết. AI đã nhận diện và chuyển đổi nó thành bảng Markdown sau:

| Cấp bậc | Lương Cơ Bản (USD) | Thưởng Hiệu Suất (Max %) | Trợ cấp |
|:---|---:|---:|:---|
| Nhân viên Mới (Entry) | $45,000 | 10% | Cơm trưa, Gửi xe |
| Chuyên viên (Mid-level) | $65,000 | 15% | Bảo hiểm sức khỏe+ |
| Quản lý (Manager) | $90,000 | 25% | Cổ phiếu ESOP, Trợ cấp đi lại |
| Giám đốc (Director) | $150,000 | 40% | Cổ phiếu ESOP, Xe đưa đón |

Như chúng ta thấy ở bảng trên, khi nhân viên thăng tiến, tỷ trọng của các khoản thưởng hiệu suất và phúc lợi phi tiền mặt tăng lên đáng kể so với lương cơ bản. Điều này phản ánh chiến lược trả lương chú trọng vào... (tiếp tục nội dung dịch văn bản).
"""

    # 3d. Lưu vào File Markdown (thông qua append_chapter_to_epub)
    print(f"[MOCK AI] Đang gọi append_chapter_to_epub...")
    append_res = json.loads(append_chapter_to_epub(f"Phân tích trang {start_page}-{end_page}", mock_translated_markdown))
    print(f"Kết quả ghi Markdown: {append_res}")

    # BƯỚC 4: Hoàn thành và đóng gói thành Epub
    print("\n[MOCK AI] Đã xử lý xong. Đang gọi finish_epub_build...")
    finish_res = finish_epub_build()
    print(f"Kết quả đóng gói: {finish_res}")
    print("--- [MOCK AI] Kết thúc ---")

if __name__ == "__main__":
    run_mock_agent()
