package com.example.ndbt

import android.annotation.SuppressLint
import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.webkit.ConsoleMessage
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.webkit.WebViewAssetLoader
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : ComponentActivity() {

    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar
    private lateinit var offlineBanner: LinearLayout
    private lateinit var prefs: SharedPreferences
    private lateinit var assetLoader: WebViewAssetLoader

    private var filePathCallback: ValueCallback<Array<Uri>>? = null

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (filePathCallback != null) {
            val uris = WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data)
            filePathCallback?.onReceiveValue(uris)
            filePathCallback = null
        }
    }

    companion object {
        private const val PREFS_NAME = "ndbt_settings"
        private const val KEY_SERVER_URL = "server_url"
        private const val DEFAULT_SERVER_URL = "http://10.15.139.232:8000"
        private const val LOCAL_ASSET_URL = "https://appassets.androidplatform.net/assets/web/index.html"
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

        assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        val rootLayout = FrameLayout(this).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            setBackgroundColor(0xFF0F172A.toInt()) // Sleek slate-900 background
        }

        webView = WebView(this).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            setBackgroundColor(0xFF0F172A.toInt())
        }

        progressBar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            layoutParams = FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                8
            ).apply { gravity = Gravity.TOP }
            isIndeterminate = false
            max = 100
            visibility = View.GONE
        }

        offlineBanner = createOfflineBanner()

        rootLayout.addView(webView)
        rootLayout.addView(progressBar)
        rootLayout.addView(offlineBanner)
        setContentView(rootLayout)

        setupWebView()
        setupBackNavigation()

        loadApplication()
    }

    private fun createOfflineBanner(): LinearLayout {
        return LinearLayout(this).apply {
            layoutParams = FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            ).apply { gravity = Gravity.BOTTOM }
            orientation = LinearLayout.HORIZONTAL
            setBackgroundColor(0xEE1E293B.toInt())
            setPadding(32, 20, 32, 20)
            gravity = Gravity.CENTER_VERTICAL
            visibility = View.GONE

            val tv = TextView(this@MainActivity).apply {
                layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
                text = "⚡ Running Local NDBT | Tap Settings to link server"
                setTextColor(0xFFCBD5E1.toInt())
                textSize = 12f
            }

            val btn = Button(this@MainActivity).apply {
                text = "Settings"
                textSize = 11f
                setBackgroundColor(0xFF2563EB.toInt())
                setTextColor(0xFFFFFFFF.toInt())
                setOnClickListener { showServerConfigDialog() }
            }

            addView(tv)
            addView(btn)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        val settings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.allowFileAccess = true
        settings.allowContentAccess = true
        settings.useWideViewPort = true
        settings.loadWithOverviewMode = true
        settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        settings.cacheMode = WebSettings.LOAD_DEFAULT
        settings.userAgentString = "${settings.userAgentString} NDBT-Android-App/1.0"

        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                if (newProgress in 1..99) {
                    progressBar.visibility = View.VISIBLE
                    progressBar.progress = newProgress
                } else {
                    progressBar.visibility = View.GONE
                }
            }

            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {
                this@MainActivity.filePathCallback?.onReceiveValue(null)
                this@MainActivity.filePathCallback = filePathCallback

                val intent = fileChooserParams?.createIntent() ?: Intent(Intent.ACTION_GET_CONTENT).apply {
                    type = "*/*"
                    addCategory(Intent.CATEGORY_OPENABLE)
                }

                try {
                    filePickerLauncher.launch(intent)
                } catch (e: Exception) {
                    this@MainActivity.filePathCallback = null
                    return false
                }
                return true
            }

            override fun onConsoleMessage(consoleMessage: ConsoleMessage?): Boolean {
                return super.onConsoleMessage(consoleMessage)
            }
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView?,
                request: WebResourceRequest?
            ): WebResourceResponse? {
                val url = request?.url ?: return null
                
                // If loading from local virtual domain, forward /api/ requests to active server
                if (url.host == "appassets.androidplatform.net") {
                    if (url.path?.startsWith("/api/") == true) {
                        return forwardApiRequest(request)
                    }
                    return assetLoader.shouldInterceptRequest(url)
                }
                return super.shouldInterceptRequest(view, request)
            }

            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                super.onPageStarted(view, url, favicon)
                progressBar.visibility = View.VISIBLE
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                progressBar.visibility = View.GONE
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?
            ) {
                // If server URL failed on main frame, fall back to embedded local app
                if (request?.isForMainFrame == true) {
                    val failedUrl = request.url.toString()
                    if (failedUrl != LOCAL_ASSET_URL) {
                        offlineBanner.visibility = View.VISIBLE
                        webView.loadUrl(LOCAL_ASSET_URL)
                    }
                }
            }
        }
    }

    private fun forwardApiRequest(request: WebResourceRequest): WebResourceResponse? {
        val serverBase = getServerUrl().trimEnd('/')
        val targetUrl = serverBase + (request.url.path ?: "") + (if (request.url.query != null) "?${request.url.query}" else "")

        return try {
            val url = URL(targetUrl)
            val connection = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = request.method
                connectTimeout = 8000
                readTimeout = 12000
                request.requestHeaders?.forEach { (k, v) -> setRequestProperty(k, v) }
            }

            val statusCode = connection.responseCode
            val statusMessage = connection.responseMessage ?: "OK"
            val contentType = connection.contentType ?: "application/json"
            val mimeType = contentType.substringBefore(';').trim()
            val encoding = if (contentType.contains("charset=")) contentType.substringAfter("charset=").trim() else "utf-8"

            val stream: InputStream = if (statusCode < 400) connection.inputStream else connection.errorStream ?: connection.inputStream
            WebResourceResponse(mimeType, encoding, statusCode, statusMessage, connection.headerFields.mapValues { it.value?.firstOrNull() ?: "" }, stream)
        } catch (e: Exception) {
            null
        }
    }

    private fun setupBackNavigation() {
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })
    }

    private fun getServerUrl(): String {
        return prefs.getString(KEY_SERVER_URL, DEFAULT_SERVER_URL) ?: DEFAULT_SERVER_URL
    }

    private fun loadApplication() {
        val serverUrl = getServerUrl()
        offlineBanner.visibility = View.GONE

        // Attempt loading the server URL; onReceivedError will auto-fallback to local assets if unavailable
        webView.loadUrl(serverUrl)
    }

    private fun showServerConfigDialog() {
        val currentUrl = getServerUrl()
        val input = EditText(this).apply {
            setText(currentUrl)
            setSelection(text.length)
            hint = "e.g. http://10.15.139.232:5173 or http://10.15.139.232:8000"
        }

        AlertDialog.Builder(this)
            .setTitle("NDBT Server Settings")
            .setMessage("Enter the IP / URL of the NDBT server (ensure mobile and laptop are on the same Wi-Fi / Hotspot):")
            .setView(input)
            .setPositiveButton("Connect") { _, _ ->
                var newUrl = input.text.toString().trim()
                if (newUrl.isNotEmpty()) {
                    if (!newUrl.startsWith("http://") && !newUrl.startsWith("https://")) {
                        newUrl = "http://$newUrl"
                    }
                    prefs.edit().putString(KEY_SERVER_URL, newUrl).apply()
                    Toast.makeText(this, "Connecting to $newUrl...", Toast.LENGTH_SHORT).show()
                    offlineBanner.visibility = View.GONE
                    webView.loadUrl(newUrl)
                }
            }
            .setNeutralButton("Use Embedded App") { _, _ ->
                offlineBanner.visibility = View.VISIBLE
                webView.loadUrl(LOCAL_ASSET_URL)
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
}
