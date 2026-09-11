# Hướng dẫn chạy ứng dụng trên thiết bị Android

Ứng dụng **Wattpad AI Audiobook** hỗ trợ 2 hình thức triển khai trên hệ điều hành Android:

---

## Cách 1: Cài đặt trực tiếp qua PWA (Khuyên dùng - Nhanh nhất, Không cần Android Studio)

Ứng dụng được thiết kế theo chuẩn **Progressive Web App (PWA)** hiện đại nhất:
1. Khởi động backend máy chủ bằng lệnh `./run.sh`.
2. Trên điện thoại Android, kết nối chung mạng Wi-Fi với máy tính.
3. Mở trình duyệt **Google Chrome** trên Android và truy cập vào:
   ```
   http://<IP_MÁY_TÍNH_CỦA_BẠN>:8000
   ```
   *(Ví dụ: `http://192.168.1.15:8000`)*
4. Bấm vào nút **"Cài App Android"** trên góc phải giao diện, hoặc bấm vào menu 3 chấm của Chrome và chọn **"Thêm vào màn hình chính" (Add to Home Screen)** / **"Cài đặt ứng dụng" (Install App)**.
5. Biểu tượng ứng dụng sẽ xuất hiện trên màn hình điện thoại như một ứng dụng native:
   - Chạy toàn màn hình (không có thanh địa chỉ trình duyệt).
   - Tự động lưu cache để mở nhanh tức thì.
   - **Tích hợp MediaSession**: Hiển thị ảnh bìa, tên chương và nút Play/Pause/Tua trực tiếp trên màn hình khóa (Lock screen) và thanh thông báo điện thoại, nghe nhạc liên tục khi tắt màn hình!

---

## Cách 2: Đóng gói và cài đặt file APK qua Android Studio

Nếu bạn muốn tạo file cài đặt `.apk` độc lập:

### Bước 1: Chuẩn bị
1. Mở phần mềm **Android Studio**.
2. Chọn **Open an Existing Project** và dẫn tới thư mục `android/` trong dự án này.

### Bước 2: Cấu hình địa chỉ Server
1. Mở file [MainActivity.kt](file:///Users/jasondam/Documents/wattpad-reader/android/app/src/main/java/com/wattpad/audiobook/MainActivity.kt).
2. Sửa dòng:
   ```kotlin
   private val appUrl = "http://10.0.2.2:8000" // Khi test trên máy ảo Android Emulator
   ```
   thành địa chỉ IP LAN của máy tính bạn (ví dụ: `http://192.168.1.15:8000`) hoặc tên miền backend đã deploy lên Cloud.

### Bước 3: Build APK
- Chọn menu **Build** > **Build Bundle(s) / APK(s)** > **Build APK(s)**.
- File APK thành phẩm sẽ nằm trong `android/app/build/outputs/apk/debug/app-debug.apk`.
- Copy file APK vào điện thoại và cài đặt.
