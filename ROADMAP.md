# ROADMAP: AI PDF to EPUB Agent

Dựa trên quá trình nghiên cứu và tham khảo các giải pháp hiện tại (`overcuriousity/pdf2epub`, `jkecb/pdf-to-epub-ai`, `eulixir/pdf2epub`, v.v.), dưới đây là các tính năng nâng cao được đề xuất cho phiên bản tương lai của dự án này, nhằm giúp hệ thống tự động, chính xác và tiết kiệm chi phí hơn.

## 1. Tối ưu hóa Tiền xử lý (Preprocessing) & Hybrid AI Mode (State-of-the-Art)
**Vấn đề hiện tại:** MVP sử dụng Vision AI để đọc toàn bộ trang PDF thành ảnh. Điều này linh hoạt nhưng tốn rất nhiều chi phí (Tokens) cho ảnh đầu vào và đôi khi AI bỏ sót chi tiết nhỏ do ảnh bị nén.
**Giải pháp tham khảo (Từ `datalab-to/marker` & `opendataloader-pdf`):**
- **Sử dụng Datalab Marker (V2) / Opendataloader:** Các thư viện này cung cấp khả năng parse local cực mạnh. Chúng trích xuất ra file JSON chứa chi tiết Bounding Boxes, Layout, đoạn Text thô, và phát hiện chính xác vị trí của Bảng/Ảnh.
- **Hybrid AI Architecture:** AI (như Gemini 1.5 Pro / GPT-4o) sẽ không phải "nhìn" toàn bộ trang một cách mù quáng nữa. Thay vào đó, Code Python sẽ gửi cho AI:
   1. Text thô bóc được từ OCR Local.
   2. Tọa độ (Bounding box) của các bảng biểu phức tạp.
   3. Yêu cầu AI: *"Hãy đọc phần text thô này, kết hợp nhìn vào tọa độ (x,y) trên bức ảnh đính kèm để cấu trúc lại bảng bị vỡ"*.
- **Kết quả:** Giảm 90% lượng token Vision, tăng 99% độ chính xác cho Bảng/Toán học (Latex) so với việc chỉ ném ảnh cho LLM tự đoán.

### 1.1 Giải pháp Thay thế cho Máy tính Cấu hình Yếu: Distributed Architecture với `googlecolab/colab-mcp`
Thay vì tải toàn bộ file PDF lên LLM (dẫn đến tỷ lệ ảo giác/hallucination cao, khó kiểm soát chất lượng ở các trang phức tạp), giải pháp tối ưu và tiết kiệm nhất là chia tách hệ thống thông qua giao thức **MCP (Model Context Protocol)** kết hợp với **Google Colab Free GPU**, sử dụng công cụ chính thức từ Google `googlecolab/colab-mcp`:

- **Cơ chế Bán tự động (Semi-Automated WebSocket):** Bạn chỉ cần cài đặt `colab-mcp` làm công cụ cho AI Agent tại máy cá nhân. Khi Agent cần bóc tách file PDF nặng bằng AI Models chuyên dụng (như PyTorch, `marker-pdf` V2), Agent sẽ tự động bật trình duyệt web, mở một tab Google Colab.
- **Thực thi qua GPU Đám mây:** Tab Colab này kết nối ngược về Agent qua WebSocket. Agent tự động "bơm" script Python bóc tách PDF lên Colab, chạy trên con GPU T4 miễn phí của Google, và thu hồi kết quả (Text thô, Bounding box, Images) về lại máy tính của bạn.
- **LLM Context Control Tuyệt đối:** Nhờ MCP, Cloud LLM (Gemini/GPT-4o) không phải đọc mù PDF. Agent chỉ gửi cho LLM những đoạn context đã được Colab parse sạch sẽ và có tọa độ chính xác. Khắc phục triệt để lỗi ảo giác, vỡ layout, giải phóng 100% gánh nặng phần cứng máy local, mà chi phí hạ tầng = $0.

## 2. Quản lý Chi phí và Tốc độ (Cost Tracking & Concurrency)
**Vấn đề hiện tại:** Xử lý tuần tự và không có giới hạn chi phí có thể dẫn đến việc tiêu tốn rất nhiều API Credit.
**Giải pháp tham khảo:**
- Giống `jkecb/pdf-to-epub-ai`: Cung cấp tham số `--max-cost`, tự động tracking Tokens usage (Input/Output). Nếu dự kiến vượt mức cho phép, tool sẽ pause và hỏi ý kiến người dùng.
- **Xử lý Đa luồng (Async/Concurrency):** PDF có thể được chia thành nhiều đoạn độc lập (chunks). Các API calls (ví dụ: gpt-4o) có thể được gọi đồng thời qua `asyncio`, giúp giảm thời gian dịch 1 quyển sách từ hàng giờ xuống vài chục phút.

## 3. Cải tiến Trải nghiệm & Dịch thuật (Inspired by Immersive Translate)
**Vấn đề hiện tại:** Dịch thuần túy (monolingual) và chưa có tính nhất quán về thuật ngữ chuyên môn xuyên suốt các chương sách.
**Giải pháp nâng cao:**
- **Chế độ Dịch Song Ngữ (Bilingual EPUB):** Cung cấp tùy chọn sinh ra EPUB hiển thị song song đoạn văn bản gốc và bản dịch (ví dụ: đệm câu tiếng Việt ngay dưới câu tiếng Anh bằng format in nghiêng). Giúp người dùng vừa đọc sách vừa học ngoại ngữ.
- **Từ điển Thuật ngữ (Custom Glossary):** Thêm trường nhập liệu trên UI để cung cấp danh sách thuật ngữ (VD: `Equity = Cổ phần`). AI Agent sẽ được tiêm danh sách này vào System Prompt để ép buộc sự nhất quán khi dịch sách chuyên ngành (Tài chính, Y khoa...).
- **Bộ nhớ Dịch thuật (Translation Memory / Cache):** Tích hợp SQLite/LocalDB để lưu lại các đoạn đã dịch. Hỗ trợ Resume (dịch tiếp) nếu bị lỗi mạng/API, tránh việc phải trả tiền API để dịch lại từ đầu.

## 4. Kiến trúc Microservice (API / Web UI)
**Vấn đề hiện tại:** Chỉ chạy qua CLI, người dùng non-tech khó tiếp cận.
**Giải pháp tham khảo:**
- Giống `eulixir/pdf2epub`: Đưa toàn bộ Logic Agent hiện tại thành các Background Worker (vd: Celery / Redis).
- Expose REST API bằng `FastAPI`.
- Cho phép người dùng Upload file PDF qua giao diện Web (Streamlit hoặc React), theo dõi thanh tiến trình (progress bar), xem chi phí dự kiến, và bấm nút tải ePub về khi hoàn thành.

## 5. Xử lý Cấu trúc Sách thông minh (Smart Chaptering)
**Vấn đề hiện tại:** AI phải tự chia batch cố định (ví dụ 5 trang/lần) dẫn đến việc một chương hoặc một câu bị cắt ngang giữa hai batch.
**Giải pháp tham khảo:**
- Sử dụng mô hình Heuristic hoặc Text Classification để nhận diện đâu là tiêu đề chương (Chapter Heading), Mục lục (Table of Contents).
- Chia file PDF theo Logic (ví dụ: Batch = Từ đầu chương 1 đến hết chương 1), giúp AI dịch mượt mà hơn và không mất ngữ cảnh câu văn.

## 6. Xử lý Ảnh và Trình bày (Images & Fixed-Layout)
**Vấn đề hiện tại:** Hình ảnh được "dịch" thành đoạn văn miêu tả (Caption). Không có ảnh gốc trong Epub.
**Giải pháp nâng cao:**
- Sử dụng tool `extract_page_assets` (đã viết sẵn) để bóc tách ảnh gốc, nén lại và chèn `<img src>` trực tiếp vào ePub.
- Tùy chọn **Fixed Layout ePub** (như `dodeeric/pdf2epubEX`) cho các tạp chí, sách thiết kế đặc thù (giữ nguyên gốc hoàn toàn, không reflowable).

---
*Roadmap này sẽ là kim chỉ nam để dự án phát triển từ một MVP Agent đơn giản thành một sản phẩm PDF-to-EPUB toàn diện nhất.*