# 📚 Wattpad AI Audiobook (Web & Android)

Ứng dụng chuyển đổi truyện chữ trên Wattpad thành sách nói (Audiobook) chuyên nghiệp với giọng đọc AI thông minh. Người dùng có thể tùy biến toàn bộ câu chuyện: chọn chuyển đổi tất cả hoặc từng chương tùy ý, tùy chỉnh giọng đọc, biểu cảm cảm xúc (bình thản, kịch tính, truyền cảm, vui vẻ, trầm buồn, thì thầm), tone giọng và tốc độ đọc.

---

## ✨ Tính năng nổi bật

- 🔗 **Tải truyện thông minh**: Nhập link truyện Wattpad (`https://www.wattpad.com/story/...`) hoặc link chương cụ thể. Tự động tải tên truyện, tác giả, ảnh bìa và danh sách toàn bộ các chương.
- 🌐 **Hệ Thống Dịch Thuật Văn Học AI (AI Literary Translation Engine)**:
  - **Tự động nhận diện ngôn ngữ (Language Detection)**: Phân tích tỷ lệ dấu thanh tiếng Việt kết hợp tần suất từ vựng, tự động xác định truyện tiếng Anh hoặc tiếng Việt.
  - **Dịch văn học tối ưu cho Audio/TTS (Master Canonical Prompt V1)**:
    - Tuân thủ nghiêm ngặt 22 điều khoản dịch thuật văn học: Văn phong mượt mà tự nhiên, giữ nguyên xưng hô nhân vật, việt hóa thành ngữ, cấm thô/dịch máy word-by-word.
    - Duy trì ngữ cảnh nhân vật (Character Context) và bảng thuật ngữ tùy biến (Custom Story Glossary).
  - **Phân đoạn ngữ pháp thông minh (Smart Sentence Segmentation)**: Bảo toàn ranh giới câu, dấu ngoặc kép thoại, phân chia khối văn bản đảm bảo không vượt quá context window.
  - **Bộ nhớ đệm dịch thuật thông minh (SHA-256 Translation Cache)**: Tránh dịch lặp lại tốn chi phí và thời gian.
  - **Không phụ thuộc nhà cung cấp (No Provider Lock-in)**: Tương thích chuẩn OpenAI API (OpenAI, OpenRouter, DeepSeek, vLLM, Ollama, LiteLLM) và Mock Provider phục vụ kiểm thử.
  - **Chặn lỗi an toàn (Fail-Safe Enforcement)**: Nếu quá trình dịch gặp sự cố hoặc vượt rate-limit, tác vụ chuyển đổi sẽ dừng an toàn và cảnh báo lỗi, tuyệt đối không gửi văn bản hỏng hoặc tiếng Anh vào TTS tiếng Việt.
- 📖 **Trình Đọc Song Ngữ (Bilingual Reader)**:
  - Cho phép người đọc chuyển đổi tức thì giữa bản dịch tiếng Việt mượt mà và văn bản gốc tiếng Anh.
  - Hỗ trợ Screen Wake Lock, điều chỉnh cỡ chữ, phông chữ và chế độ ban đêm.
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
  - Xem trước bản dịch nhanh (Translation Preview Modal) trước khi batch convert.
  - Chọn chuyển đổi toàn bộ hoặc tick chọn từng chương tùy thích.
  - ⏸️ **Tạm dừng (Pause)** và ▶️ **Tiếp tục (Resume)** tiến trình chuyển đổi bất kỳ lúc nào ngay trên thanh thông báo.
  - ❌ **Hủy bỏ (Cancel)** tác vụ an toàn khi muốn đổi giọng hoặc dừng lại.
  - Theo dõi tiến trình chuyển đổi 4 giai đoạn theo thời gian thực (Cào dữ liệu -> Nhận diện -> Dịch AI -> Tổng hợp Giọng đọc).
- 🎧 **Trình phát sách nói chuyên nghiệp (Audiobook Player)**:
  - Tua 15s trước/sau, chỉnh tốc độ phát lại (1x, 1.25x, 1.5x, 2x).
  - Tự động chuyển tiếp chương kế tiếp khi nghe hết chương.
  - **Tích hợp MediaSession**: Điều khiển Play/Pause/Next trực tiếp trên màn hình khóa điện thoại Android hoặc thanh thông báo hệ thống.
  - Tải file MP3 từng chương hoặc tải file ZIP trọn bộ các chương đã chuyển đổi (chuẩn RFC 6266 / UTF-8 không lỗi font tiếng Việt).
- 📱 **Tương thích hoàn hảo Web & Android**:
  - Chạy mượt mà trên trình duyệt máy tính và điện thoại.
  - Chuẩn **PWA (Progressive Web App)**: Cài đặt trực tiếp lên màn hình chính Android chỉ với 1 chạm.
  - Kèm mã nguồn dự án **Android Studio (Kotlin WebView)** trong thư mục `android/`.
- 🛡️ **Bảo mật & Dự phòng**:
  - Chống SSRF (Server-Side Request Forgery) trên link Wattpad.
  - SQLite WAL mode, cấu trúc bảng quan hệ, bảo mật token HMAC và phân quyền.
  - Hỗ trợ tạo sách nói từ văn bản tùy biến trực tiếp.

---

## 🚀 Hướng dẫn khởi động

### 1. Khởi động bằng Docker (Khuyên dùng - Tiện lợi & Nhanh chóng)

Chỉ cần cài đặt Docker/Docker Desktop và chạy 1 lệnh duy nhất:

```bash
docker compose up -d --build
```

- Server sẽ tự động được khởi tạo tại: `http://localhost:8000`.
- Toàn bộ dữ liệu truyện, database SQLite và file audio đã chuyển đổi được tự động mount lưu trữ an toàn tại thư mục `./backend/data`.
- Xem logs máy chủ:
  ```bash
  docker compose logs -f
  ```
- Dừng máy chủ:
  ```bash
  docker compose down
  ```

### 2. Khởi động trực tiếp trên máy (Native Python)

Mở Terminal tại thư mục dự án và chạy:

```bash
./run.sh
```

Hệ thống sẽ tự động kiểm tra thư viện và bật server tại:
- **Trên máy tính**: `http://localhost:8000`
- **Trên điện thoại Android (chung Wi-Fi)**: `http://<IP_MÁY_TÍNH>:8000` (địa chỉ IP sẽ hiển thị rõ trên terminal).

### 3. Cấu hình Dịch thuật AI (Tùy chọn)

Sao chép file `.env.example` thành `.env` và nhập API key của bạn:

```bash
cp .env.example .env
```

Thiết lập các biến môi trường:
- `TRANSLATION_API_KEY`: API Key của OpenAI hoặc OpenRouter.
- `TRANSLATION_BASE_URL`: Endpoint chuẩn OpenAI (ví dụ `https://openrouter.ai/api/v1` hoặc `http://localhost:11434/v1` cho Ollama).
- `TRANSLATION_MODEL`: Mô hình dịch thuật (mặc định: `gpt-4o-mini`).

### 3. Chạy kiểm thử tự động (Unit Test Suite)

Toàn bộ hệ thống được bảo vệ bởi bộ kiểm thử tự động 100% độc lập (sử dụng Mock Provider, không tốn phí API):

```bash
./venv/bin/python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 🛠️ Cấu trúc thư mục

```
wattpad-reader/
├── backend/
│   ├── main.py             # FastAPI App, API routes, Static mounting & SSRF validation
│   ├── database.py         # SQLite WAL mode, quan hệ bảng, translation cache & glossary
│   ├── auth.py             # Xác thực người dùng, bảo mật phiên token HMAC
│   ├── scraper.py          # Bộ cào dữ liệu truyện & chương Wattpad, SSRF validator
│   ├── tts_engine.py       # Bộ máy Edge-TTS & VieNeu v3, xử lý âm thanh, biểu cảm & ID3
│   ├── tasks.py            # Quản lý hàng đợi tác vụ, điều phối pipeline Dịch thuật -> TTS
│   ├── models.py           # Định nghĩa cấu trúc dữ liệu Pydantic
│   ├── translation/        # Translation Domain độc lập
│   │   ├── models.py       # Schema DTO cho Dịch thuật & Ngữ cảnh
│   │   ├── prompts.py      # Master Canonical Prompt V1 (22 điều khoản) & Context Builder
│   │   ├── detector.py     # Heuristic Language Detection (Dấu tiếng Việt & Stopwords)
│   │   ├── segmenter.py    # Phân đoạn văn bản giữ ranh giới hội thoại & dấu câu
│   │   ├── provider.py     # TranslationProvider: Mock & OpenAI-compatible
│   │   ├── cache.py        # SHA-256 Key Cache Engine
│   │   ├── context.py      # Quản lý Ngữ cảnh nhân vật & Diễn biến truyện
│   │   ├── glossary.py     # Quản lý Bảng thuật ngữ chuyên ngành / nhân vật
│   │   └── service.py      # TranslationService Facade chính
│   ├── requirements.txt    # Các thư viện Python phụ thuộc
│   └── data/               # Cơ sở dữ liệu SQLite & lưu trữ MP3
├── frontend/
│   ├── index.html          # Giao diện chính Single Page App, PWA & Translation Controls
│   ├── reader.html         # Giao diện đọc truyện song ngữ (VI / Gốc)
│   ├── manifest.json       # Cấu hình PWA cho Android & Web App Shortcuts
│   ├── sw.js               # Service worker v2 (Stale-While-Revalidate)
│   ├── css/style.css       # Giao diện Glassmorphism, badges & animation
│   ├── js/app.js           # Xử lý tương tác, audio player, translation preview modal
│   ├── js/reader.js        # Điều khiển trình đọc song ngữ, phông chữ và Wake Lock
│   └── icons/              # App icon kích thước 192x192 và 512x512
├── tests/                  # Bộ kiểm thử tự động toàn diện
│   ├── test_language_detector.py
│   ├── test_segmenter.py
│   ├── test_translation_provider.py
│   ├── test_cache_and_context.py
│   ├── test_task_pipeline.py
│   └── test_security_and_api.py
├── android/                # Dự án Android Studio (Kotlin WebView, Foreground Service, Dynamic IP)
├── .env.example            # Mẫu cấu hình môi trường
├── run.sh                  # Script khởi động tự động
└── README.md
```
