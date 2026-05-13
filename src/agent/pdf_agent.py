import os
import json
from openai import OpenAI
from src.tools.pdf_tools import get_pdf_metadata, get_page_images, extract_page_assets
from src.tools.epub_tools import init_epub, append_chapter_to_epub, finish_epub_build

class PDFAgent:
    def __init__(self, api_key: str, base_url: str = None, model_name: str = "gpt-4-vision-preview"):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else "https://api.openai.com/v1"
        )
        self.model_name = model_name
        self.system_prompt = """
Bạn là một AI Agent chuyên nghiệp có nhiệm vụ phân tích ngữ nghĩa, dịch một cuốn sách PDF sang tiếng Việt và tái tạo định dạng hoàn chỉnh.
Bạn đóng vai trò là "Bộ não" xử lý ngữ nghĩa sâu (Semantic Parsing) được cấp quyền gọi các công cụ (tools) vật lý.

Mục tiêu và Chiến lược của bạn (Hybrid Pipeline):
1. Đọc và hiểu metadata của PDF. Khởi tạo file Epub (bằng `init_epub`). Hệ thống sẽ tự động tạo cấu trúc: output/[Tên Sách]/ gồm file .md và folder /images.
2. Đọc nội dung PDF bằng `get_page_images`.
3. **Xử lý Bảng biểu Phức tạp (Sức mạnh cốt lõi của LLM):** Khi gặp bảng biểu (đặc biệt là bảng có merged cells, nested headers mà OCR vật lý thường làm hỏng), bạn PHẢI phân tích ngữ cảnh để hiểu cột/hàng nào liên quan đến nhau, và tái tạo lại bằng Markdown Table chuẩn xác nhất.
4. **Xử lý Hình ảnh & Sơ đồ:**
   - Gọi tool `extract_page_assets` để lưu ảnh nhúng trong file PDF.
   - Tool sẽ trả về đường dẫn vật lý (ví dụ: `images/page_75_img_0.jpg`).
   - Bạn hãy chèn ảnh này vào bản dịch bằng cú pháp Markdown: `![Mô tả ảnh](images/page_75_img_0.jpg)`.
   - Kết hợp dịch thêm phần chữ có trong sơ đồ vào ngay bên dưới ảnh để người đọc dễ hiểu.
5. Khi xử lý xong mỗi khối nội dung, gọi `append_chapter_to_epub` để lưu bản dịch (Markdown) vào file tổng.
6. Gọi `finish_epub_build` khi kết thúc. Hệ thống sẽ tự động đóng gói file Markdown và ảnh thành ePub.

LƯU Ý QUAN TRỌNG:
- Bạn phải sử dụng các công cụ (tools) được cung cấp.
- Đừng cố gắng dịch toàn bộ sách trong 1 lần gọi API. Sách rất dài. Hãy xử lý theo khối (ví dụ 5 trang một lần).
- Bạn tự chịu trách nhiệm lên lịch trình lặp lại (loop) và theo dõi xem mình đã đọc đến trang nào.
- Trả về thông báo hoàn thành hoặc lỗi chi tiết.
"""
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_pdf_metadata",
                    "description": "Lấy thông tin cơ bản của PDF (tổng số trang, mục lục).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdf_path": {"type": "string", "description": "Đường dẫn đến file PDF"}
                        },
                        "required": ["pdf_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_page_images",
                    "description": "Lấy hình ảnh của các trang PDF (dùng cho Vision). Trả về danh sách base64 images.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdf_path": {"type": "string", "description": "Đường dẫn đến file PDF"},
                            "start_page": {"type": "integer", "description": "Trang bắt đầu (index từ 0)"},
                            "end_page": {"type": "integer", "description": "Trang kết thúc (index từ 0)"}
                        },
                        "required": ["pdf_path", "start_page", "end_page"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_page_assets",
                    "description": "Trích xuất các ảnh nhúng trên 1 trang PDF ra file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pdf_path": {"type": "string"},
                            "page_number": {"type": "integer"},
                            "output_dir": {"type": "string"}
                        },
                        "required": ["pdf_path", "page_number", "output_dir"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "init_epub",
                    "description": "Khởi tạo file Epub mới. Gọi hàm này đầu tiên trước khi thêm chương.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "author": {"type": "string"}
                        },
                        "required": ["title", "author"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "append_chapter_to_epub",
                    "description": "Thêm một chương dịch (định dạng Markdown) vào Epub.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Tiêu đề của chương"},
                            "markdown_content": {"type": "string", "description": "Nội dung Markdown đã dịch sang tiếng Việt (bao gồm cả bảng biểu, text format)"}
                        },
                        "required": ["title", "markdown_content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "finish_epub_build",
                    "description": "Đóng gói Epub. Gọi hàm này sau khi tất cả các trang PDF đã được xử lý.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "output_path": {"type": "string", "description": "Đường dẫn lưu file ePub (ví dụ: output/book.epub)"}
                        },
                        "required": ["output_path"]
                    }
                }
            }
        ]

        # Tool execution map
        self.available_functions = {
            "get_pdf_metadata": get_pdf_metadata,
            "get_page_images": get_page_images,
            "extract_page_assets": extract_page_assets,
            "init_epub": init_epub,
            "append_chapter_to_epub": append_chapter_to_epub,
            "finish_epub_build": finish_epub_build
        }

    def run(self, initial_instruction: str, max_iterations: int = 50):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": initial_instruction}
        ]

        print("Bắt đầu tiến trình AI Agent...")

        for iteration in range(max_iterations):
            print(f"\n--- Iteration {iteration + 1} ---")

            # 1. Call LLM
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.2
            )

            response_message = response.choices[0].message

            # Print AI text if present
            if response_message.content:
                print(f"AI: {response_message.content}")

            # Always append the full response message to history
            messages.append(response_message)

            # 2. Check if AI wants to call tools
            tool_calls = response_message.tool_calls
            if tool_calls:

                # Collect vision messages to append AFTER all tool responses
                pending_vision_messages = []

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    print(f"AI đang gọi công cụ: {function_name} với tham số: {function_args}")

                    # Execute tool
                    function_to_call = self.available_functions.get(function_name)
                    if function_to_call:
                        try:
                            # Pass arguments to function
                            function_response = function_to_call(**function_args)

                            # Handle vision inputs specially if get_page_images was called
                            # The agent needs to see the image, not just the base64 string
                            if function_name == "get_page_images":
                                res_dict = json.loads(function_response)
                                if "pages" in res_dict:
                                    # Create a specialized message for vision
                                    content_list = [{"type": "text", "text": "Đây là hình ảnh của các trang PDF bạn vừa yêu cầu:"}]
                                    for p in res_dict["pages"]:
                                        content_list.append({
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{p['image_base64']}"
                                            }
                                        })

                                    # Standard tool response
                                    messages.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "name": function_name,
                                        "content": json.dumps({"status": "success", "message": f"Returned {len(res_dict['pages'])} images. Please analyze them in the next message."})
                                    })

                                    # Queue the actual vision payload to be added after ALL tools
                                    pending_vision_messages.append({
                                        "role": "user",
                                        "content": content_list
                                    })
                                else:
                                     messages.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "name": function_name,
                                        "content": function_response
                                    })
                            else:
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": function_name,
                                    "content": function_response
                                })
                        except Exception as e:
                            print(f"Lỗi khi chạy công cụ {function_name}: {e}")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": json.dumps({"error": str(e)})
                            })
                    else:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": json.dumps({"error": "Function not found"})
                        })

                # Append pending vision messages sequentially after ALL tool calls to avoid API errors
                for vm in pending_vision_messages:
                    messages.append(vm)
            else:
                # If no tool calls and AI thinks it's done or waiting
                if "hoàn thành" in (response_message.content or "").lower() or "finish" in (response_message.content or "").lower():
                    print("Tiến trình hoàn tất.")
                    break

                # Sometime AI needs a nudge
                # messages.append({"role": "user", "content": "Hãy tiếp tục xử lý các trang tiếp theo hoặc gọi `finish_epub_build` nếu đã xong toàn bộ."})

        print("Dừng vòng lặp Agent.")
