#!/bin/bash

# Script khởi động Wattpad AI Audiobook (Web & Android Server)

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo "    🚀 Đang khởi động Wattpad AI Audiobook Server...      "
echo "=========================================================="

# Kiểm tra Virtualenv
if [ ! -d "venv" ]; then
    echo "📦 Đang khởi tạo môi trường Python venv..."
    python3 -m venv venv
    ./venv/bin/pip install -r backend/requirements.txt
fi

# Lấy địa chỉ IP mạng nội bộ (LAN IP) để tiện test trên điện thoại Android
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "IP_CUA_BAN")

echo ""
echo "✅ Server sẵn sàng tại:"
echo "   🌐 Trình duyệt trên máy tính:  http://localhost:8000"
echo "   📱 Điện thoại Android (Wi-Fi): http://${LOCAL_IP}:8000"
echo ""
echo "👉 Bấm Ctrl + C để dừng server."
echo "----------------------------------------------------------"

./venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
