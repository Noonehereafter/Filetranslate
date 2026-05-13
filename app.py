import streamlit as st
import os
from src.utils.config_manager import load_settings, save_settings
from src.agent.pdf_agent import PDFAgent
from src.mock_run import run_mock_agent
import sys
import io
from contextlib import redirect_stdout

st.set_page_config(page_title="PDF to EPUB AI", page_icon="📚", layout="wide")

# --- Initialize Session State ---
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()

if "logs" not in st.session_state:
    st.session_state.logs = ""

if "is_running" not in st.session_state:
    st.session_state.is_running = False

if "result_epub" not in st.session_state:
    st.session_state.result_epub = None

# --- Sidebar: Settings ---
st.sidebar.title("⚙️ Cấu Hình Hệ Thống")

# We don't use form here so we can have interactive buttons (like fetch models)
api_key = st.sidebar.text_input("API Key (OpenAI/Gemini)", value=st.session_state.settings["api_key"], type="password")
base_url = st.sidebar.text_input("Base URL", value=st.session_state.settings["base_url"])

import requests

if "available_models" not in st.session_state:
    st.session_state.available_models = []

col_fetch, col_clear = st.sidebar.columns(2)
with col_fetch:
    if st.button("🔄 Lấy Models"):
        if not api_key:
            st.error("Thiếu API Key")
        else:
            try:
                headers = {"Authorization": f"Bearer {api_key}"}
                # Check if base_url has trailing slash and fix it
                b_url = base_url.rstrip('/')
                res = requests.get(f"{b_url}/models", headers=headers, timeout=5)
                if res.status_code == 200:
                    models_data = res.json()
                    st.session_state.available_models = [m["id"] for m in models_data.get("data", [])]
                    st.success("Lấy Model thành công!")
                else:
                    st.error(f"Lỗi {res.status_code}: {res.text}")
            except Exception as e:
                st.error(f"Không thể kết nối: {e}")

manual_input = st.sidebar.checkbox("Nhập Model thủ công", value=not bool(st.session_state.available_models))

if manual_input or not st.session_state.available_models:
    model_name = st.sidebar.text_input("Tên Model", value=st.session_state.settings["model_name"])
else:
    # Set default index if current model exists in the list
    default_index = 0
    if st.session_state.settings["model_name"] in st.session_state.available_models:
        default_index = st.session_state.available_models.index(st.session_state.settings["model_name"])

    model_name = st.sidebar.selectbox("Chọn Model", options=st.session_state.available_models, index=default_index)

st.sidebar.markdown("---")
batch_size = st.sidebar.number_input("Số trang mỗi Batch", min_value=1, max_value=20, value=st.session_state.settings["batch_size"])
max_pages = st.sidebar.number_input("Tổng số trang muốn dịch", min_value=1, max_value=2000, value=st.session_state.settings["max_pages"])

mock_mode = st.sidebar.checkbox("Chế độ Giả lập (Mock Mode - Không tốn API)", value=st.session_state.settings["mock_mode"])

if st.sidebar.button("💾 Lưu Cấu Hình", use_container_width=True):
    st.session_state.settings = {
        "api_key": api_key,
        "base_url": base_url,
        "model_name": model_name,
        "batch_size": batch_size,
        "max_pages": max_pages,
        "mock_mode": mock_mode
    }
    save_settings(st.session_state.settings)
    st.sidebar.success("Đã lưu cấu hình!")

# --- Main UI ---
st.title("📚 PDF to EPUB AI Translator")
st.markdown("Công cụ tự động phân tích và dịch sách PDF sang định dạng ePub bằng công nghệ AI Vision, giữ nguyên bảng biểu và hình ảnh gốc.")

uploaded_file = st.file_uploader("Tải lên file PDF cần dịch", type=["pdf"])

if uploaded_file is not None:
    # Save uploaded file temporarily
    temp_pdf_path = "temp_upload.pdf"
    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.info(f"Đã tải lên: {uploaded_file.name} - Sẵn sàng xử lý.")

    col1, col2 = st.columns([1, 5])
    with col1:
        start_btn = st.button("🚀 Bắt đầu Dịch", disabled=st.session_state.is_running, use_container_width=True)

    if start_btn:
        st.session_state.is_running = True
        st.session_state.logs = "Bắt đầu tiến trình...\n"

        # We use an expander or text area to show logs
        log_container = st.empty()

        try:
            # Progress bar setup
            progress_bar = st.progress(0, text="Đang khởi tạo quá trình dịch...")
            total_pages = st.session_state.settings['max_pages']

            def update_progress(current_page: int):
                # Ensure progress doesn't exceed 100%
                percent_complete = min(1.0, current_page / total_pages)
                progress_bar.progress(percent_complete, text=f"Đang xử lý PDF... Hoàn thành {current_page}/{total_pages} trang.")

            with st.spinner('Đang chạy nền AI Agent... Vui lòng xem Log để biết chi tiết.'):
                if st.session_state.settings["mock_mode"]:
                    st.session_state.logs += "[INFO] Đang chạy chế độ Giả lập...\n"
                    # To capture stdout from mock run
                    f = io.StringIO()
                    with redirect_stdout(f):
                        run_mock_agent(temp_pdf_path)
                    st.session_state.logs += f.getvalue()
                    # Mock run uses a fixed title inside init_epub for safety
                    st.session_state.result_epub = "output/Compensation_Test_Hybrid_Pipeline/Compensation_Test_Hybrid_Pipeline.epub"
                else:
                    if not st.session_state.settings["api_key"]:
                        st.error("Vui lòng nhập API Key trong phần Cấu hình!")
                        st.session_state.is_running = False
                        st.stop()

                    st.session_state.logs += "[INFO] Khởi động AI Agent...\n"
                    agent = PDFAgent(
                        api_key=st.session_state.settings["api_key"],
                        base_url=st.session_state.settings["base_url"],
                        model_name=st.session_state.settings["model_name"]
                    )

                    instruction = f"""
                    Hãy xử lý file PDF sau: {temp_pdf_path}.
                    Tên file gốc: {uploaded_file.name}
                    1. Đọc metadata và khởi tạo Epub.
                    2. Đọc và dịch {st.session_state.settings['max_pages']} trang đầu tiên. Phân theo batch {st.session_state.settings['batch_size']} trang/lần.
                    3. Xử lý semantic parsing cho bảng biểu, trích xuất ảnh thật và nhúng bằng markdown.
                    4. Đóng gói epub khi hoàn tất.
                    """

                    f = io.StringIO()
                    with redirect_stdout(f):
                        agent.run(
                            initial_instruction=instruction,
                            max_iterations=st.session_state.settings['max_pages']*2,
                            progress_callback=update_progress
                        )
                    st.session_state.logs += f.getvalue()

                    # Ensure progress bar hits 100% at the end
                    progress_bar.progress(1.0, text="Hoàn tất việc đọc file. Đang đóng gói Epub...")

                    # Find the most recently generated epub in the output directory
                    output_dir = "output"
                    found_epub = None
                    if os.path.exists(output_dir):
                        # Sort directories by modification time to get the latest workspace
                        dirs = [os.path.join(output_dir, d) for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
                        if dirs:
                            latest_dir = max(dirs, key=os.path.getmtime)
                            # Find the epub file inside the latest workspace
                            epub_files = [f for f in os.listdir(latest_dir) if f.endswith(".epub")]
                            if epub_files:
                                found_epub = os.path.join(latest_dir, epub_files[0])

                    if found_epub:
                        st.session_state.result_epub = found_epub
                    else:
                        st.warning("Không tìm thấy file ePub. Vui lòng kiểm tra Log để xem AI có gặp lỗi không.")

                st.success("Hoàn thành!")
        except Exception as e:
            st.error(f"Có lỗi xảy ra: {e}")
        finally:
            st.session_state.is_running = False
            # Dọn dẹp file PDF tạm
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    # Display Logs
    if st.session_state.logs:
        with st.expander("📝 Xem Log Chi Tiết", expanded=True):
            st.text_area("", value=st.session_state.logs, height=300, disabled=True)

    # Display Download Button if available
    if st.session_state.result_epub and os.path.exists(st.session_state.result_epub):
        with open(st.session_state.result_epub, "rb") as file:
            st.download_button(
                label="⬇️ Tải xuống file ePub",
                data=file,
                file_name=os.path.basename(st.session_state.result_epub),
                mime="application/epub+zip"
            )
