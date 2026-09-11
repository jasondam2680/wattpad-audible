package com.wattpad.audiobook

import android.annotation.SuppressLint
import android.app.AlertDialog
import android.app.DownloadManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.ViewGroup
import android.view.WindowManager
import android.webkit.*
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    companion object {
        const val PREFS_NAME = "wattpad_audiobook_prefs"
        const val KEY_SERVER_URL = "server_url"
        const val DEFAULT_SERVER_URL = "http://192.168.31.149:8000"
        const val EMULATOR_SERVER_URL = "http://10.0.2.2:8000"
    }

    fun getServerUrl(): String {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_SERVER_URL, null) ?: DEFAULT_SERVER_URL
    }

    fun saveServerUrl(newUrl: String) {
        val cleanUrl = newUrl.trim()
        val formattedUrl = when {
            cleanUrl.startsWith("http://") || cleanUrl.startsWith("https://") -> cleanUrl.trimEnd('/')
            else -> "http://${cleanUrl.trimEnd('/')}"
        }
        getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_SERVER_URL, formattedUrl)
            .apply()
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Cấu hình Edge-to-edge tương thích chuẩn từ Android 5 đến Android 16
        try {
            WindowCompat.setDecorFitsSystemWindows(window, false)
            val insetsController = WindowCompat.getInsetsController(window, window.decorView)
            insetsController.isAppearanceLightStatusBars = false
            insetsController.isAppearanceLightNavigationBars = false
        } catch (e: Exception) {
            e.printStackTrace()
        }

        // Xin quyền gửi thông báo (Android 13+ / API 33+) để Foreground Service hiển thị trạng thái chuyển đổi
        checkNotificationPermission()

        try {
            webView = WebView(this).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                )
            }
            setContentView(webView)

            setupWebView()
            setupBackNavigation()

            // Tải ứng dụng từ địa chỉ server cấu hình
            webView.loadUrl(getServerUrl())
        } catch (e: Exception) {
            e.printStackTrace()
            Toast.makeText(this, "Lỗi khởi tạo WebView: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }

    private fun checkNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 101)
            }
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        val settings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.allowFileAccess = true
        settings.cacheMode = WebSettings.LOAD_DEFAULT

        // Cho phép phát âm thanh tự động và chạy ngầm
        settings.mediaPlaybackRequiresUserGesture = false

        // Đăng ký Javascript Bridge kết nối giữa Web Frontend và Android Native
        webView.addJavascriptInterface(AndroidBridge(this), "AndroidBridge")

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val url = request?.url?.toString() ?: return false
                if (url.contains("/download") || url.endsWith(".zip")) {
                    try {
                        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                        startActivity(intent)
                        return true
                    } catch (e: Exception) {
                        return false
                    }
                }
                return false
            }

            override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {
                super.onReceivedError(view, request, error)
                if (request?.isForMainFrame == true) {
                    val currentUrl = getServerUrl()
                    showServerSettingsDialog(
                        "Không thể kết nối đến máy chủ: $currentUrl.\n\nVui lòng đảm bảo bạn đã chạy './run.sh' trên máy tính, hoặc đổi địa chỉ IP Wi-Fi dưới đây:"
                    )
                }
            }
        }

        webView.webChromeClient = WebChromeClient()

        // Hỗ trợ tải file trực tiếp trên Android qua DownloadManager
        webView.setDownloadListener { url, userAgent, contentDisposition, mimetype, _ ->
            try {
                val request = DownloadManager.Request(Uri.parse(url))
                request.setMimeType(mimetype)
                val cookies = CookieManager.getInstance().getCookie(url)
                if (cookies != null) {
                    request.addRequestHeader("cookie", cookies)
                }
                request.addRequestHeader("User-Agent", userAgent)
                request.setDescription("Đang tải file sách nói Wattpad...")

                val filename = URLUtil.guessFileName(url, contentDisposition, mimetype)
                request.setTitle(filename)
                request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, filename)

                val dm = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                dm.enqueue(request)
                Toast.makeText(applicationContext, "Đang tải $filename vào thư mục Downloads...", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                try {
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                    startActivity(intent)
                } catch (ex: Exception) {
                    Toast.makeText(applicationContext, "Lỗi tải file: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun setupBackNavigation() {
        // Điều hướng nút Back chuẩn Android 13/14/15/16 (Predictive Back Gesture)
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (::webView.isInitialized && webView.canGoBack()) {
                    webView.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })
    }

    fun showServerSettingsDialog(messagePrompt: String? = null) {
        runOnUiThread {
            val context = this
            val currentUrl = getServerUrl()

            val input = EditText(context).apply {
                setText(currentUrl)
                setSingleLine(true)
                setSelection(text.length)
                hint = "http://192.168.1.15:8000"
            }

            val container = LinearLayout(context).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(50, 20, 50, 20)
                addView(input)
            }

            AlertDialog.Builder(context)
                .setTitle("Cài đặt Máy chủ (Server URL)")
                .setMessage(messagePrompt ?: "Nhập địa chỉ IP Wi-Fi hoặc domain máy chủ backend:")
                .setView(container)
                .setPositiveButton("Lưu & Kết nối") { _, _ ->
                    val newUrl = input.text.toString().trim()
                    if (newUrl.isNotEmpty()) {
                        saveServerUrl(newUrl)
                        val updatedUrl = getServerUrl()
                        Toast.makeText(context, "Đang kết nối: $updatedUrl", Toast.LENGTH_SHORT).show()
                        webView.loadUrl(updatedUrl)
                    }
                }
                .setNeutralButton("Dùng Emulator (10.0.2.2)") { _, _ ->
                    saveServerUrl(EMULATOR_SERVER_URL)
                    webView.loadUrl(EMULATOR_SERVER_URL)
                }
                .setNegativeButton("Hủy", null)
                .show()
        }
    }

    fun startBackgroundService(title: String, message: String) {
        try {
            AudiobookForegroundService.startService(this, title, message)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun updateBackgroundService(title: String, message: String) {
        try {
            AudiobookForegroundService.updateService(this, title, message)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun stopBackgroundService() {
        try {
            AudiobookForegroundService.stopService(this)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    override fun onResume() {
        super.onResume()
        if (::webView.isInitialized) {
            webView.onResume()
        }
    }

    override fun onPause() {
        // QUAN TRỌNG: Không gọi webView.onPause() để tránh WebView tạm dừng JavaScript execution và timers
        // khi người dùng chuyển sang ứng dụng khác hoặc ra màn hình Home.
        super.onPause()
    }

    override fun onDestroy() {
        stopBackgroundService()
        if (::webView.isInitialized) {
            webView.destroy()
        }
        super.onDestroy()
    }

    // Lớp cầu nối JavaScript Interface
    class AndroidBridge(private val activity: MainActivity) {

        @JavascriptInterface
        fun isAndroidApp(): Boolean = true

        @JavascriptInterface
        fun startBackground(title: String?, message: String?) {
            activity.runOnUiThread {
                activity.startBackgroundService(
                    title ?: "Wattpad Sách Nói AI",
                    message ?: "Tiến trình chuyển đổi đang chạy ngầm..."
                )
            }
        }

        @JavascriptInterface
        fun updateBackground(title: String?, message: String?) {
            activity.runOnUiThread {
                activity.updateBackgroundService(
                    title ?: "Wattpad Sách Nói AI",
                    message ?: "Đang chuyển đổi chương..."
                )
            }
        }

        @JavascriptInterface
        fun stopBackground() {
            activity.runOnUiThread {
                activity.stopBackgroundService()
            }
        }

        @JavascriptInterface
        fun showToast(message: String?) {
            activity.runOnUiThread {
                if (!message.isNullOrEmpty()) {
                    Toast.makeText(activity, message, Toast.LENGTH_SHORT).show()
                }
            }
        }

        @JavascriptInterface
        fun vibrate(durationMs: Long) {
            activity.runOnUiThread {
                try {
                    val dur = if (durationMs in 1..2000) durationMs else 25L
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                        val vibratorManager = activity.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                        vibratorManager?.defaultVibrator?.vibrate(
                            VibrationEffect.createOneShot(dur, VibrationEffect.DEFAULT_AMPLITUDE)
                        )
                    } else {
                        @Suppress("DEPRECATION")
                        val vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            vibrator?.vibrate(VibrationEffect.createOneShot(dur, VibrationEffect.DEFAULT_AMPLITUDE))
                        } else {
                            @Suppress("DEPRECATION")
                            vibrator?.vibrate(dur)
                        }
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }

        @JavascriptInterface
        fun setKeepScreenOn(enabled: Boolean) {
            activity.runOnUiThread {
                try {
                    if (enabled) {
                        activity.window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                    } else {
                        activity.window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }

        @JavascriptInterface
        fun openServerConfig() {
            activity.runOnUiThread {
                activity.showServerSettingsDialog()
            }
        }

        @JavascriptInterface
        fun getServerUrl(): String = activity.getServerUrl()

        @JavascriptInterface
        fun getAppVersion(): String {
            return try {
                val pInfo = activity.packageManager.getPackageInfo(activity.packageName, 0)
                pInfo.versionName ?: "1.0.0"
            } catch (e: Exception) {
                "1.0.0"
            }
        }
    }
}
