package com.smsforwarder

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.charset.StandardCharsets

class MainActivity : AppCompatActivity() {
    
    private lateinit var btnConnect: Button
    private lateinit var tvStatus: TextView
    private lateinit var tvMessageLog: TextView
    private val handler = Handler(Looper.getMainLooper())
    private var isScanning = false
    private var serverAddress: String? = null
    
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
        tvStatus = findViewById(R.id.tvStatus)
        tvMessageLog = findViewById(R.id.tvMessageLog)
        
        messageLogCallback = { message ->
            handler.post {
                tvMessageLog.append("$message\n")
            }
        }
        
        connectionStateCallback = { isConnected ->
            handler.post {
                if (isConnected) {
                    tvStatus.text = "已连接"
                    btnConnect.text = "断开连接"
                    btnConnect.isEnabled = true
                } else {
                    tvStatus.text = "未连接"
                    btnConnect.text = "扫描服务器"
                    btnConnect.isEnabled = true
                }
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
    
    private fun setupListeners() {
        btnConnect.setOnClickListener {
            if (btnConnect.text == "扫描服务器") {
                scanServers()
            } else {
                disconnect()
            }
        }
    }
    
    private fun scanServers() {
        if (isScanning) return
        
        isScanning = true
        tvStatus.text = "正在扫描服务器..."
        btnConnect.text = "扫描中..."
        btnConnect.isEnabled = false
        
        Thread {
            try {
                val socket = DatagramSocket(12345)
                socket.soTimeout = 10000 // 10秒超时
                
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
                                tvStatus.text = "找到服务器: $serverAddress"
                                messageLogCallback?.invoke("找到服务器: $serverAddress")
                                connectToServer(serverAddress!!)
                            }
                            break
                        }
                    } catch (e: Exception) {
                        // 超时或错误，继续扫描
                    }
                }
                
                socket.close()
            } catch (e: Exception) {
                handler.post {
                    tvStatus.text = "扫描失败: ${e.message}"
                    messageLogCallback?.invoke("扫描失败: ${e.message}")
                    btnConnect.text = "扫描服务器"
                    btnConnect.isEnabled = true
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
        stopService(intent)
        tvStatus.text = "已断开连接"
        btnConnect.text = "扫描服务器"
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
        super.onDestroy()
    }
}