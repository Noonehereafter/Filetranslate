# ROADMAP: AI PDF to EPUB Agent

Dựa trên quá trình nghiên cứu và tham khảo các giải pháp hiện tại (`overcuriousity/pdf2epub`, `jkecb/pdf-to-epub-ai`, `eulixir/pdf2epub`, v.v.), dưới đây là các tính năng nâng cao được đề xuất cho phiên bản tương lai của dự án này, nhằm giúp hệ thống tự động, chính xác và tiết kiệm chi phí hơn.

## 1. Tối ưu hóa Tiền xử lý (Preprocessing) & OCR
**Vấn đề hiện tại:** MVP sử dụng Vision AI để đọc toàn bộ trang PDF thành ảnh. Điều này linh hoạt nhưng tốn rất nhiều chi phí (Tokens) và chậm đối với các trang chỉ có text (không có biểu đồ).
**Giải pháp tham khảo:**
- Tích hợp **`marker-pdf`** (giống `overcuriousity/pdf2epub`): Sử dụng Machine Learning nội bộ (PyTorch) để trích xuất text, phát hiện bảng biểu, và render phương trình toán học (Math/Latex).
- Tích hợp **OCR chuyên dụng (như Surya OCR)** (giống `jkecb/pdf-to-epub-ai`): Chỉ gọi OCR khi trang là ảnh scan hoàn toàn, hoặc trang bị lỗi font.
- **Agent Quyết định:** AI Agent ban đầu sẽ không cần đọc Vision toàn bộ 100%. Code sẽ trích xuất text trước. Nếu AI phát hiện đoạn text bị lỗi font (Garbage text) hoặc thiếu hình ảnh/bảng, AI mới gọi Tool `get_page_images` để nhờ Vision đọc trang đó. Tiết kiệm đến 80% chi phí.

## 2. Quản lý Chi phí và Tốc độ (Cost Tracking & Concurrency)
**Vấn đề hiện tại:** Xử lý tuần tự và không có giới hạn chi phí có thể dẫn đến việc tiêu tốn rất nhiều API Credit.
**Giải pháp tham khảo:**
- Giống `jkecb/pdf-to-epub-ai`: Cung cấp tham số `--max-cost`, tự động tracking Tokens usage (Input/Output). Nếu dự kiến vượt mức cho phép, tool sẽ pause và hỏi ý kiến người dùng.
- **Xử lý Đa luồng (Async/Concurrency):** PDF có thể được chia thành nhiều đoạn độc lập (chunks). Các API calls (ví dụ: gpt-4o) có thể được gọi đồng thời qua `asyncio`, giúp giảm thời gian dịch 1 quyển sách từ hàng giờ xuống vài chục phút.

## 3. Kiến trúc Microservice (API / Web UI)
**Vấn đề hiện tại:** Chỉ chạy qua CLI, người dùng non-tech khó tiếp cận.
**Giải pháp tham khảo:**
- Giống `eulixir/pdf2epub`: Đưa toàn bộ Logic Agent hiện tại thành các Background Worker (vd: Celery / Redis).
- Expose REST API bằng `FastAPI`.
- Cho phép người dùng Upload file PDF qua giao diện Web (Streamlit hoặc React), theo dõi thanh tiến trình (progress bar), xem chi phí dự kiến, và bấm nút tải ePub về khi hoàn thành.

## 4. Xử lý Cấu trúc Sách thông minh (Smart Chaptering)
**Vấn đề hiện tại:** AI phải tự chia batch cố định (ví dụ 5 trang/lần) dẫn đến việc một chương hoặc một câu bị cắt ngang giữa hai batch.
**Giải pháp tham khảo:**
- Sử dụng mô hình Heuristic hoặc Text Classification để nhận diện đâu là tiêu đề chương (Chapter Heading), Mục lục (Table of Contents).
- Chia file PDF theo Logic (ví dụ: Batch = Từ đầu chương 1 đến hết chương 1), giúp AI dịch mượt mà hơn và không mất ngữ cảnh câu văn.

## 5. Xử lý Ảnh và Trình bày (Images & Fixed-Layout)
**Vấn đề hiện tại:** Hình ảnh được "dịch" thành đoạn văn miêu tả (Caption). Không có ảnh gốc trong Epub.
**Giải pháp nâng cao:**
- Sử dụng tool `extract_page_assets` (đã viết sẵn) để bóc tách ảnh gốc, nén lại và chèn `<img src>` trực tiếp vào ePub.
- Tùy chọn **Fixed Layout ePub** (như `dodeeric/pdf2epubEX`) cho các tạp chí, sách thiết kế đặc thù (giữ nguyên gốc hoàn toàn, không reflowable).

---
*Roadmap này sẽ là kim chỉ nam để dự án phát triển từ một MVP Agent đơn giản thành một sản phẩm PDF-to-EPUB toàn diện nhất.*