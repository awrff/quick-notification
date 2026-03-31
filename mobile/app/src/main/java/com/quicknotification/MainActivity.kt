package com.quicknotification

import android.Manifest
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.util.DisplayMetrics
import android.view.LayoutInflater
import android.view.WindowManager
import android.widget.ImageButton
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.content.res.ResourcesCompat
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.charset.StandardCharsets

class MainActivity : AppCompatActivity() {
    
    private lateinit var btnConnect: ImageButton
    private lateinit var btnSettings: ImageButton
    private lateinit var btnLog: ImageButton
    private lateinit var tvStatus: TextView
    private val messageLog = StringBuilder()
    private val handler = Handler(Looper.getMainLooper())
    private var isScanning = false
    private var serverAddress: String? = null
    private var isConnected = false
    private var logDialog: AlertDialog? = null
    
    companion object {
        const val PERMISSION_REQUEST_CODE = 100
        var messageLogCallback: ((String) -> Unit)? = null
        var connectionStateCallback: ((Boolean) -> Unit)? = null
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        initViews()
        checkPermissions()
        setupListeners()
    }
    
    private fun initViews() {
        btnConnect = findViewById(R.id.btnConnect)
        btnSettings = findViewById(R.id.btnSettings)
        btnLog = findViewById(R.id.btnLog)
        tvStatus = findViewById(R.id.tvStatus)
        
        updateButtonState(ButtonState.DISCONNECTED)
        
        messageLogCallback = { message ->
            handler.post {
                messageLog.append("$message\n")
                updateLogDialog()
            }
        }
        
        connectionStateCallback = { connected ->
            handler.post {
                isConnected = connected
                if (connected) {
                    tvStatus.text = "已连接"
                    updateButtonState(ButtonState.CONNECTED)
                } else {
                    tvStatus.text = "未连接"
                    updateButtonState(ButtonState.DISCONNECTED)
                }
            }
        }
    }
    
    private fun updateLogDialog() {
        if (logDialog?.isShowing == true) {
            val tvDialogMessageLog = logDialog?.findViewById<TextView>(R.id.tvDialogMessageLog)
            tvDialogMessageLog?.text = messageLog.toString()
            val scrollView = logDialog?.findViewById<ScrollView>(R.id.scrollViewLog)
            scrollView?.post { scrollView.fullScroll(ScrollView.FOCUS_DOWN) }
        }
    }
    
    private fun showLogDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_log, null)
        val tvDialogMessageLog = dialogView.findViewById<TextView>(R.id.tvDialogMessageLog)
        val btnCopyLog = dialogView.findViewById<ImageButton>(R.id.btnCopyLog)
        val btnClose = dialogView.findViewById<android.widget.Button>(R.id.btnClose)
        
        tvDialogMessageLog.text = messageLog.toString()
        
        btnCopyLog.setOnClickListener {
            copyLogToClipboard()
        }
        
        btnClose.setOnClickListener {
            logDialog?.dismiss()
        }
        
        logDialog = AlertDialog.Builder(this)
            .setView(dialogView)
            .setCancelable(true)
            .create()
        
        logDialog?.setOnDismissListener {
            logDialog = null
        }
        
        logDialog?.show()
        
        val displayMetrics = DisplayMetrics()
        windowManager.defaultDisplay.getMetrics(displayMetrics)
        val screenHeight = displayMetrics.heightPixels
        val screenWidth = displayMetrics.widthPixels
        val dialogHeight = (screenHeight * 0.55).toInt()
        val dialogWidth = (screenWidth * 0.9).toInt()
        
        logDialog?.window?.setLayout(
            dialogWidth,
            dialogHeight
        )
        
        val scrollView = dialogView.findViewById<ScrollView>(R.id.scrollViewLog)
        scrollView?.post { scrollView.fullScroll(ScrollView.FOCUS_DOWN) }
    }
    
    private fun copyLogToClipboard() {
        if (messageLog.isEmpty()) {
            Toast.makeText(this, "日志为空", Toast.LENGTH_SHORT).show()
            return
        }
        
        try {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("消息日志", messageLog.toString())
            clipboard.setPrimaryClip(clip)
            Toast.makeText(this, "日志已复制到剪贴板", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(this, "复制失败: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }
    
    private enum class ButtonState {
        DISCONNECTED,
        SCANNING,
        CONNECTED
    }
    
    private fun updateButtonState(state: ButtonState) {
        when (state) {
            ButtonState.DISCONNECTED -> {
                btnConnect.setImageResource(R.drawable.ic_connect)
                btnConnect.setBackgroundResource(R.drawable.btn_connect_bg)
                btnConnect.isEnabled = true
                tvStatus.setTextColor(ResourcesCompat.getColor(resources, R.color.status_disconnected, null))
            }
            ButtonState.SCANNING -> {
                btnConnect.setImageResource(R.drawable.ic_scanning)
                btnConnect.setBackgroundResource(R.drawable.btn_scanning_bg)
                btnConnect.isEnabled = false
                tvStatus.setTextColor(ResourcesCompat.getColor(resources, R.color.status_scanning, null))
            }
            ButtonState.CONNECTED -> {
                btnConnect.setImageResource(R.drawable.ic_disconnect)
                btnConnect.setBackgroundResource(R.drawable.btn_disconnect_bg)
                btnConnect.isEnabled = true
                tvStatus.setTextColor(ResourcesCompat.getColor(resources, R.color.status_connected, null))
            }
        }
    }
    
    private fun checkPermissions() {
        val permissions = mutableListOf(
            Manifest.permission.RECEIVE_SMS,
            Manifest.permission.READ_SMS,
            Manifest.permission.INTERNET,
            Manifest.permission.ACCESS_NETWORK_STATE
        )
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        
        val missingPermissions = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        
        if (missingPermissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                this,
                missingPermissions.toTypedArray(),
                PERMISSION_REQUEST_CODE
            )
        }
    }
    
    private fun openAppSettings() {
        try {
            val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                data = Uri.parse("package:$packageName")
            }
            startActivity(intent)
        } catch (e: Exception) {
            Toast.makeText(this, "无法打开设置页面", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun setupListeners() {
        btnConnect.setOnClickListener {
            if (isConnected) {
                disconnect()
            } else {
                scanServers()
            }
        }
        
        btnSettings.setOnClickListener {
            openAppSettings()
        }
        
        btnLog.setOnClickListener {
            showLogDialog()
        }
    }
    
    private fun scanServers() {
        if (isScanning) return
        
        isScanning = true
        tvStatus.text = "正在扫描..."
        updateButtonState(ButtonState.SCANNING)
        
        Thread {
            try {
                val socket = DatagramSocket(12345)
                socket.soTimeout = 10000
                
                val buffer = ByteArray(1024)
                val packet = DatagramPacket(buffer, buffer.size)
                
                while (isScanning) {
                    try {
                        socket.receive(packet)
                        val message = String(packet.data, 0, packet.length, StandardCharsets.UTF_8)
                        if (message.startsWith("SMS_FORWARDER_PORT:")) {
                            val port = message.substringAfter(":").toInt()
                            val ip = packet.address.hostAddress
                            serverAddress = "$ip:$port"
                            
                            handler.post {
                                tvStatus.text = "已连接"
                                messageLogCallback?.invoke("找到服务器: $serverAddress")
                                connectToServer(serverAddress!!)
                            }
                            break
                        }
                    } catch (e: Exception) {
                        handler.post {
                            tvStatus.text = "扫描超时"
                            messageLogCallback?.invoke("扫描超时，未找到服务器")
                            updateButtonState(ButtonState.DISCONNECTED)
                            isScanning = false
                        }
                    }
                }
                
                socket.close()
            } catch (e: Exception) {
                handler.post {
                    tvStatus.text = "扫描失败"
                    messageLogCallback?.invoke("扫描失败: ${e.message}")
                    updateButtonState(ButtonState.DISCONNECTED)
                    isScanning = false
                }
            }
        }.start()
    }
    
    private fun connectToServer(serverAddress: String) {
        val intent = Intent(this, WebSocketService::class.java)
        intent.action = WebSocketService.ACTION_CONNECT
        intent.putExtra(WebSocketService.EXTRA_SERVER_ADDRESS, serverAddress)
        startService(intent)
        isScanning = false
    }
    
    private fun disconnect() {
        val intent = Intent(this, WebSocketService::class.java)
        intent.action = WebSocketService.ACTION_DISCONNECT
        startService(intent)
        tvStatus.text = "已断开连接"
        updateButtonState(ButtonState.DISCONNECTED)
        isConnected = false
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            if (grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                Toast.makeText(this, "权限已授予", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "权限被拒绝，应用可能无法正常工作", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    override fun onDestroy() {
        isScanning = false
        logDialog?.dismiss()
        super.onDestroy()
    }
}
