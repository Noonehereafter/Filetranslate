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
    init_epub("Compensation (Bản Test Bảng Biểu & Hình Ảnh)", "Barry Gerhart & AI")

    # BƯỚC 3: Giả lập quá trình đọc trang 75 và 76 (có chứa ảnh và bảng)
    start_page = 75
    end_page = 76

    # 3a. Gọi hàm lấy hình ảnh
    print(f"\n[MOCK AI] Đang gọi get_page_images từ trang {start_page} đến {end_page}...")
    img_res = json.loads(get_page_images(pdf_path, start_page, end_page))

    if "error" in img_res:
        print(f"Lỗi khi lấy ảnh: {img_res['error']}")
        return

    images_count = len(img_res.get('pages', []))
    print(f"[MOCK AI] Đã nhận được {images_count} hình ảnh để đọc bằng Vision AI.")

    # 3b. Giả lập AI nhận diện và dịch:
    print(f"[MOCK AI] Đang phân tích Vision và tạo nội dung Markdown...")
    mock_translated_markdown = f"""## Chương 2: Chiến lược lương thưởng (Trang {start_page}-{end_page})

Dưới đây là một ví dụ giả định về cách AI Vision đọc và tái tạo lại một trang sách có chứa hình ảnh và bảng biểu phức tạp. Thay vì cố gắng chụp lại mờ nhòe, AI trình bày lại bằng Markdown chuẩn.

### Hình ảnh minh họa

*(Ảnh: Biểu đồ thể hiện mối tương quan giữa sự hài lòng của nhân viên và mức lương cơ bản trong ngành IT năm 2023. Đường xu hướng đi lên rõ rệt khi vượt qua mức 20.000 USD/năm)*

> **Nhận xét của AI:** Tôi không thể chèn trực tiếp ảnh bitmap ở đây trong phiên bản MVP, nhưng tôi đã tạo một đoạn mô tả chi tiết (caption) bên trên cho người đọc nắm được ngữ cảnh.

### Bảng biểu: Cơ cấu thu nhập theo cấp bậc

Trong trang {start_page}, tác giả có đề cập đến một bảng dữ liệu chi tiết. AI đã nhận diện và chuyển đổi nó thành bảng Markdown sau:

| Cấp bậc | Lương Cơ Bản (USD) | Thưởng Hiệu Suất (Max %) | Trợ cấp |
|:---|---:|---:|:---|
| Nhân viên Mới (Entry) | $45,000 | 10% | Cơm trưa, Gửi xe |
| Chuyên viên (Mid-level) | $65,000 | 15% | Bảo hiểm sức khỏe+ |
| Quản lý (Manager) | $90,000 | 25% | Cổ phiếu ESOP, Trợ cấp đi lại |
| Giám đốc (Director) | $150,000 | 40% | Cổ phiếu ESOP, Xe đưa đón |

Như chúng ta thấy ở bảng trên, khi nhân viên thăng tiến, tỷ trọng của các khoản thưởng hiệu suất và phúc lợi phi tiền mặt tăng lên đáng kể so với lương cơ bản. Điều này phản ánh chiến lược trả lương chú trọng vào... (tiếp tục nội dung dịch văn bản).
"""

    # 3c. Lưu vào ePub
    print(f"[MOCK AI] Đang gọi append_chapter_to_epub...")
    append_res = json.loads(append_chapter_to_epub(f"Phân tích trang {start_page}-{end_page}", mock_translated_markdown))
    print(f"Kết quả lưu chương: {append_res}")

    # BƯỚC 4: Hoàn thành và đóng gói
    print("\n[MOCK AI] Đã xử lý xong. Đang gọi finish_epub_build...")
    os.makedirs("output", exist_ok=True)
    finish_res = finish_epub_build("output/test_table_image.epub")
    print(f"Kết quả đóng gói: {finish_res}")
    print("--- [MOCK AI] Kết thúc ---")

if __name__ == "__main__":
    run_mock_agent()
