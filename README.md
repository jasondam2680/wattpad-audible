# 📚 Wattpad AI Audiobook (Web & Android)

Ứng dụng chuyển đổi truyện chữ trên Wattpad thành sách nói (Audiobook) chuyên nghiệp với giọng đọc AI thông minh. Người dùng có thể tùy biến toàn bộ câu chuyện: chọn chuyển đổi tất cả hoặc từng chương tùy ý, tùy chỉnh giọng đọc, biểu cảm cảm xúc (bình thản, kịch tính, truyền cảm, vui vẻ, trầm buồn, thì thầm), tone giọng và tốc độ đọc.

---

## ✨ Tính năng nổi bật

- 🔗 **Tải truyện thông minh**: Nhập link truyện Wattpad (`https://www.wattpad.com/story/...`) hoặc link chương cụ thể. Tự động tải tên truyện, tác giả, ảnh bìa và danh sách toàn bộ các chương.
- 🎙️ **Động cơ AI Voice đa dạng (Dual Engine)**:
  - 🦜 **VieNeu-TTS v3 Turbo via ONNX (Khuyên dùng)**:
    - Mô hình AI Neural tiếng Việt mới nhất, chạy **On-device CPU bằng ONNX Runtime**, cho âm thanh **48kHz Studio Quality**.
    - **23 giọng đọc tự nhiên** thuộc đầy đủ 3 miền Bắc, Trung, Nam với phong cách: *Kể chuyện/Sách nói* (Thái Sơn, Ngọc Linh, Thanh Bình, Thục Đoan, Mỹ Duyên, Quỳnh Anh...), *Tự nhiên* (Phạm Tuyên, Trúc Ly, Quang Sơn, Adam...), và *Tin tức*.
    - **Thẻ cảm xúc ngữ điệu (Emotion Cues)**: Tự do chèn biểu cảm sinh động như `[cười]`, `[thở dài]`, `[hắng giọng]`.
  - ☁️ **Microsoft Edge Neural TTS**:
    - Giọng đọc đám mây tốc độ cao: Hoài My (Nữ), Nam Minh (Nam), Jenny, Guy.
    - 6 Preset Biểu cảm & Cảm xúc: Bình thản, Truyền cảm, Hồi hộp/Kịch tính, Vui vẻ, Trầm buồn, Thì thầm.
    - Tinh chỉnh Pitch (+/-20Hz) và Speed (0.7x - 1.4x).
  - Nút **"Nghe thử giọng đọc"** giúp nghe trước câu mẫu trong 3 giây.
- 📑 **Lựa chọn chương linh hoạt & Điều khiển tiến trình nâng cao**:
  - Chọn chuyển đổi toàn bộ hoặc tick chọn từng chương tùy thích.
  - ⏸️ **Tạm dừng (Pause)** và ▶️ **Tiếp tục (Resume)** tiến trình chuyển đổi bất kỳ lúc nào ngay trên thanh thông báo.
  - ❌ **Hủy bỏ (Cancel)** tác vụ an toàn khi muốn đổi giọng hoặc dừng lại.
  - Theo dõi tiến trình chuyển đổi % theo thời gian thực.
- 🎧 **Trình phát sách nói chuyên nghiệp (Audiobook Player)**:
  - Tua 15s trước/sau, chỉnh tốc độ phát lại (1x, 1.25x, 1.5x, 2x).
  - Tự động chuyển tiếp chương kế tiếp khi nghe hết chương.
  - **Tích hợp MediaSession**: Điều khiển Play/Pause/Next trực tiếp trên màn hình khóa điện thoại Android hoặc thanh thông báo hệ thống.
  - Tải file MP3 từng chương hoặc tải file ZIP trọn bộ các chương đã chuyển đổi (chuẩn RFC 6266 / UTF-8 không lỗi font tiếng Việt).
- 📱 **Tương thích hoàn hảo Web & Android**:
  - Chạy mượt mà trên trình duyệt máy tính và điện thoại.
  - Chuẩn **PWA (Progressive Web App)**: Cài đặt trực tiếp lên màn hình chính Android chỉ với 1 chạm.
  - Kèm mã nguồn dự án **Android Studio (Kotlin WebView)** trong thư mục `android/`.
- 🛡️ **Dự phòng (Fallback)**: Hỗ trợ tạo sách nói từ văn bản nhập tay trực tiếp nếu gặp link Wattpad bị chặn IP.

---

## 🚀 Hướng dẫn khởi động

### 1. Khởi động nhanh (Khuyên dùng)

Mở Terminal tại thư mục dự án và chạy:

```bash
./run.sh
```

Hệ thống sẽ tự động kiểm tra thư viện và bật server tại:
- **Trên máy tính**: `http://localhost:8000`
- **Trên điện thoại Android (chung Wi-Fi)**: `http://<IP_MÁY_TÍNH>:8000` (địa chỉ IP sẽ hiển thị rõ trên terminal).

### 2. Sử dụng trên điện thoại Android

- Mở trình duyệt **Chrome trên Android**, truy cập vào địa chỉ IP của máy tính (ví dụ: `http://192.168.1.15:8000`).
- Bấm nút **"Cài App Android"** trên góc phải (hoặc menu 3 chấm của Chrome > **Cài đặt ứng dụng** / **Thêm vào màn hình chính**).
- Ứng dụng sẽ xuất hiện như app native, hỗ trợ chạy ngầm và hiển thị điều khiển phát nhạc khi tắt màn hình.
- Chi tiết về dự án Android Studio xem tại: [android/README.md](android/README.md).

---

## 🛠️ Cấu trúc thư mục

```
wattpad-reader/
├── backend/
│   ├── main.py             # FastAPI App, API routes, Static mounting & bảo vệ Path Traversal
│   ├── database.py         # SQLite WAL mode, schema quan hệ, auto-migration, băm mật khẩu
│   ├── auth.py             # Xác thực người dùng, bảo mật phiên token HMAC
│   ├── scraper.py          # Bộ cào dữ liệu truyện & chương Wattpad
│   ├── tts_engine.py       # Bộ máy Edge-TTS & VieNeu v3, xử lý âm thanh, biểu cảm & ID3
│   ├── tasks.py            # Quản lý hàng đợi tác vụ, giới hạn concurrency & resume tiến trình
│   ├── models.py           # Định nghĩa cấu trúc dữ liệu Pydantic
│   ├── requirements.txt    # Các thư viện Python phụ thuộc
│   └── data/               # Lưu trữ file MP3, mẫu audio và metadata
├── frontend/
│   ├── index.html          # Giao diện chính Single Page App & PWA
│   ├── reader.html         # Giao diện đọc truyện độc lập với Screen Wake Lock
│   ├── manifest.json       # Cấu hình PWA cho Android & Web App Shortcuts
│   ├── sw.js               # Service worker v2 (Stale-While-Revalidate)
│   ├── css/style.css       # Giao diện Glassmorphism & equalizer animation
│   ├── js/app.js           # Xử lý tương tác, audio player, haptic feedback và MediaSession
│   ├── js/reader.js        # Điều khiển trình đọc truyện, phông chữ và giữ sáng màn hình
│   └── icons/              # App icon kích thước 192x192 và 512x512
├── android/                # Dự án Android Studio (Kotlin WebView, Foreground Service, Dynamic IP)
├── run.sh                  # Script khởi động tự động
└── README.md
```
