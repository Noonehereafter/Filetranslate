import os
from dotenv import load_dotenv
from src.agent.pdf_agent import PDFAgent

def main():
    # Load environment variables
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model_name = os.getenv("MODEL_NAME", "gpt-4-vision-preview")

    if not api_key or api_key == "your_api_key_here":
        print("Vui lòng cấu hình OPENAI_API_KEY trong file .env")
        return

    # PDF path
    pdf_path = "Compensation - Gerhart, Barry;Newman, Jerry;Mi.pdf"

    if not os.path.exists(pdf_path):
        print(f"Không tìm thấy file: {pdf_path}")
        return

    print(f"Khởi tạo AI Agent với model: {model_name}")
    agent = PDFAgent(api_key=api_key, base_url=base_url, model_name=model_name)

    instruction = f"""
    Hãy xử lý file PDF sau: {pdf_path}.
    Đây là một cuốn sách lớn, hãy làm theo các bước sau:
    1. Lấy metadata của file PDF.
    2. Khởi tạo Epub với tiêu đề và tác giả lấy từ metadata (hoặc tự đặt tên nếu không có).
    3. Đọc 2 trang đầu tiên (trang 0 và trang 1) để lấy ví dụ (MVP) và dịch nó. (Bỏ qua nếu trang bìa không có chữ, dịch từ trang có chữ).
    4. Trình bày lại các bảng biểu (nếu có) bằng Markdown table, thêm caption cho ảnh.
    5. Lưu chương dịch vào Epub.
    6. Do đây là bản test MVP, sau khi dịch xong 2 trang đầu, hãy đóng gói Epub ngay (lưu tại output/book.epub) và hoàn thành công việc.
    """

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    agent.run(initial_instruction=instruction, max_iterations=20)
    print("Run finished. Check 'output/book.epub'.")

if __name__ == "__main__":
    main()
