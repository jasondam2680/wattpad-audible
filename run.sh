#!/bin/bash

# Script khởi động Wattpad AI Audiobook (Web & Android Server)

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo "    🚀 Đang khởi động Wattpad AI Audiobook Server...      "
echo "=========================================================="

# Kiểm tra Virtualenv (nếu không ở Codespaces / container đã có sẵn env)
if [ -z "$CODESPACES" ] && [ ! -d "venv" ]; then
    echo "📦 Đang khởi tạo môi trường Python venv..."
    python3 -m venv venv
    ./venv/bin/pip install -r backend/requirements.txt
fi

# Xác định uvicorn binary (dùng venv nếu có, fallback uvicorn hệ thống)
if [ -f "./venv/bin/uvicorn" ]; then
    UVICORN_CMD="./venv/bin/uvicorn"
else
    UVICORN_CMD="uvicorn"
fi

# Lấy địa chỉ IP mạng nội bộ (LAN IP) tương thích cả macOS và Linux/Codespaces
if [[ "$OSTYPE" == "darwin"* ]]; then
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "127.0.0.1")
else
    LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
fi

echo ""
echo "✅ Server sẵn sàng tại:"
echo "   🌐 Trình duyệt trên máy tính:  http://localhost:8000"
if [ -n "$CODESPACES" ]; then
    echo "   ☁️ GitHub Codespaces:          Mở qua tab Ports (Forwarded Port 8000)"
else
    echo "   📱 Điện thoại Android (Wi-Fi): http://${LOCAL_IP}:8000"
fi
echo ""
echo "👉 Bấm Ctrl + C để dừng server."
echo "----------------------------------------------------------"

$UVICORN_CMD backend.main:app --host 0.0.0.0 --port 8000 --reload
