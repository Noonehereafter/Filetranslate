# PDF to ePub AI Translator (MVP)

Công cụ này cho phép sử dụng các mô hình AI tiên tiến (như GPT-4o, Gemini Pro Vision) để tự động hóa việc đọc một file PDF (bao gồm cả scan), nhận diện cấu trúc, dịch toàn bộ nội dung sang tiếng Việt và đóng gói thành file ePub hoàn chỉnh.

## Kiến trúc
Dự án được xây dựng theo mô hình **AI Agent (Tool Calling)**. AI hoạt động như một "Bộ não", còn các đoạn code Python đóng vai trò "Culi" xử lý file vật lý.
- AI sẽ tự xem xét số lượng trang của PDF.
- Tự quyết định cắt từng phần nhỏ (ví dụ 5 trang/lần) ra thành hình ảnh.
- Dịch và xử lý layout (bảng biểu thành markdown tables, ảnh thành caption).
- Tự động gọi hàm thêm chương vào ePub và đóng gói kết quả cuối cùng.

## Cài đặt

1. Yêu cầu Python 3.9+
2. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```
3. Cấu hình môi trường:
   - Copy file `.env.example` thành `.env`
   - Điền API Key của OpenAI hoặc nền tảng tương thích (ví dụ: Gemini thông qua proxy/wrapper).

   ```env
   OPENAI_API_KEY=your_api_key
   OPENAI_BASE_URL=https://api.openai.com/v1
   MODEL_NAME=gpt-4o  # Khuyến nghị dùng model hỗ trợ Vision mạnh như gpt-4o
   ```

## Chạy thử nghiệm

Chạy file main để AI bắt đầu quá trình đọc, dịch và xuất ePub:

```bash
python src/main.py
```

*Lưu ý: Trong file `src/main.py`, lệnh prompt mẫu đang được giới hạn chỉ chạy 2 trang đầu tiên để làm MVP (tránh tốn nhiều chi phí API và thời gian). Bạn có thể sửa đổi biến `instruction` để AI chạy toàn bộ quyển sách.*

## Khó khăn đã giải quyết trong MVP
- **PDF Scan Xóa/Phức Tạp**: Chuyển trang thành hình ảnh độ phân giải cao và sử dụng Vision AI để đọc thay vì dùng thư viện bóc text vật lý dễ gây lỗi font.
- **Bảng biểu / Cấu trúc**: Prompt yêu cầu AI trả về Markdown tables cho bảng biểu và thêm Caption để mô tả các sơ đồ phức tạp. EbookLib sẽ tự render Markdown sang HTML chuẩn.
- **Dung lượng lớn / Token Limit**: AI được thiết kế để xử lý theo "batch" thông qua các tham số `start_page`, `end_page` do chính AI quyết định.
