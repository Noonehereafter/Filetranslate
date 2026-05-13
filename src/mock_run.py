import os
import json
from src.tools.pdf_tools import get_pdf_metadata, get_page_images
from src.tools.epub_tools import init_epub, append_chapter_to_epub, finish_epub_build

def run_mock_agent():
    pdf_path = "Compensation - Gerhart, Barry;Newman, Jerry;Mi.pdf"

    print("--- [MOCK AI] Bắt đầu quá trình ---")

    # BƯỚC 1: Lấy metadata
    print("[MOCK AI] Đang gọi get_pdf_metadata...")
    meta_json = get_pdf_metadata(pdf_path)
    meta = json.loads(meta_json)
    print(f"Metadata nhận được: {meta.get('title', 'N/A')} - Tổng số trang: {meta.get('total_pages', 0)}")

    # BƯỚC 2: Khởi tạo ePub
    print("[MOCK AI] Đang gọi init_epub...")
    init_epub("Compensation (Bản dịch Mẫu 20 trang)", "Barry Gerhart & AI")

    # BƯỚC 3: Giả lập quá trình đọc và dịch 20 trang (chia làm 4 batch, mỗi batch 5 trang)
    total_pages_to_process = 20
    batch_size = 5

    for start_page in range(0, total_pages_to_process, batch_size):
        end_page = start_page + batch_size - 1

        # 3a. Gọi hàm lấy hình ảnh
        print(f"\n[MOCK AI] Đang gọi get_page_images từ trang {start_page} đến {end_page}...")
        img_res = json.loads(get_page_images(pdf_path, start_page, end_page))

        if "error" in img_res:
            print(f"Lỗi khi lấy ảnh: {img_res['error']}")
            continue

        images_count = len(img_res.get('pages', []))
        print(f"[MOCK AI] Đã nhận được {images_count} hình ảnh để đọc bằng Vision AI.")

        # 3b. Giả lập AI suy nghĩ và sinh ra văn bản dịch (kèm markdown format)
        print(f"[MOCK AI] Đang phân tích và dịch nội dung...")
        mock_translated_markdown = f"""## Chương: Trang {start_page} đến {end_page}

Đây là nội dung văn bản giả lập được AI *dịch* từ hình ảnh của trang **{start_page}** đến **{end_page}**.

### 1. Giới thiệu
Nội dung này được tạo ra để chứng minh rằng luồng giao tiếp giữa AI và Tool đang hoạt động trơn tru.

| Cột A | Cột B |
|-------|-------|
| Dữ liệu {start_page} | Giá trị {end_page} |

> "Sự thành công của một cuốn sách không chỉ nằm ở nội dung, mà còn ở cách nó được trình bày."

*(Hình ảnh / Sơ đồ được AI tóm tắt: Sơ đồ cấu trúc lương thưởng)*
"""

        # 3c. Lưu vào ePub
        print(f"[MOCK AI] Đang gọi append_chapter_to_epub cho batch này...")
        append_res = json.loads(append_chapter_to_epub(f"Phần {start_page}-{end_page}", mock_translated_markdown))
        print(f"Kết quả lưu chương: {append_res}")

    # BƯỚC 4: Hoàn thành và đóng gói
    print("\n[MOCK AI] Đã xử lý xong 20 trang. Đang gọi finish_epub_build...")
    os.makedirs("output", exist_ok=True)
    finish_res = finish_epub_build("output/mock_book.epub")
    print(f"Kết quả đóng gói: {finish_res}")
    print("--- [MOCK AI] Kết thúc ---")

if __name__ == "__main__":
    run_mock_agent()
