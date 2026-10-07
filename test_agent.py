"""Script kiểm tra hoạt động của Agent với Groq API và các công cụ tra cứu file."""

import json
import os
import sys
import urllib.request
from pathlib import Path

# Đảm bảo hiển thị UTF-8 trên Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 1. Đọc cấu hình từ file .env
env_vars = {}
env_path = Path(".env")
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()

API_KEY = env_vars.get("OPENAI_API_KEY") or env_vars.get("GROQ_API_KEY", "")
BASE_URL = env_vars.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = env_vars.get("MODEL_NAME", "openai/gpt-oss-120b")

if not API_KEY:
    print("❌ Lỗi: Không tìm thấy API key trong file .env!")
    sys.exit(1)

print("=" * 60)
print(f"🚀 Kết nối Groq API: {BASE_URL}")
print(f"🤖 Model: {MODEL_NAME}")
print("=" * 60)

WORKSPACE = Path(".").resolve()

# 2. Định nghĩa các tool tương thích với môi trường
def tool_list_files(path: str) -> dict:
    target = (WORKSPACE / path).resolve()
    if not target.exists() or not target.is_dir():
        return {"ok": False, "error": f"Không tìm thấy thư mục: {path}"}
    entries = [{"name": p.name, "is_dir": p.is_dir()} for p in sorted(target.iterdir())]
    return {"ok": True, "path": path, "entries": entries}

def tool_read_file(path: str) -> dict:
    target = (WORKSPACE / path).resolve()
    if not target.exists() or not target.is_file():
        return {"ok": False, "error": f"Không tìm thấy file: {path}"}
    return {"ok": True, "path": path, "content": target.read_text(encoding="utf-8")}

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Liệt kê danh sách các file trong một thư mục của workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Đường dẫn thư mục tương đối, ví dụ: data/policies"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Đọc nội dung của một file văn bản trong workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Đường dẫn file tương đối, ví dụ: data/policies/policy-before-oct.md"}
                },
                "required": ["path"],
            },
        },
    },
]

def chat_completion(messages: list) -> dict:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "tools": tools_schema,
        "tool_choice": "auto",
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_scenario(user_query: str):
    print(f"\n[Người dùng hỏi]: {user_query}\n")
    messages = [
        {
            "role": "system",
            "content": (
                "Bạn là trợ lý chính sách hoàn tiền. Bạn phải luôn dùng tool `list_files` và `read_file` "
                "để tra cứu tài liệu chính sách trong thư mục `data/policies` trước khi trả lời. Tuyệt đối không tự suy đoán."
            ),
        },
        {"role": "user", "content": user_query},
    ]

    for step in range(1, 6):
        res = chat_completion(messages)
        message = res["choices"][0]["message"]
        messages.append(message)

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            print("[Trợ lý trả lời]:")
            print(message.get("content"))
            break

        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            raw_args = tc["function"]["arguments"]
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            call_id = tc["id"]
            print(f"👉 Bước {step}: Agent gọi tool [{fn_name}] -> tham số: {args}")

            if fn_name == "list_files":
                out = tool_list_files(args.get("path", ""))
            elif fn_name == "read_file":
                out = tool_read_file(args.get("path", ""))
            else:
                out = {"ok": False, "error": "Unknown tool"}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(out, ensure_ascii=False),
                }
            )

if __name__ == "__main__":
    test_query = "Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, sản phẩm chưa kích hoạt. Tôi có được hoàn không?"
    run_scenario(test_query)
