package com.smsforwarder

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
    
    private lateinit var etServerAddress: EditText
    private lateinit var btnConnect: Button
    private lateinit var tvStatus: TextView
    private lateinit var tvMessageLog: TextView
    
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
        etServerAddress = findViewById(R.id.etServerAddress)
        btnConnect = findViewById(R.id.btnConnect)
        tvStatus = findViewById(R.id.tvStatus)
        tvMessageLog = findViewById(R.id.tvMessageLog)
        
        messageLogCallback = { message ->
            runOnUiThread {
                tvMessageLog.append("$message\n")
            }
        }
        
        connectionStateCallback = { isConnected ->
            runOnUiThread {
                if (isConnected) {
                    tvStatus.text = "已连接"
                    btnConnect.text = "断开连接"
                    btnConnect.isEnabled = true
                } else {
                    tvStatus.text = "未连接"
                    btnConnect.text = "连接服务器"
                    btnConnect.isEnabled = true
                }
            }
        }
    }
    
    private fun checkPermissions() {
        val permissions = mutableListOf(
            Manifest.permission.RECEIVE_SMS,
            Manifest.permission.READ_SMS,
            Manifest.permission.INTERNET
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
            if (btnConnect.text == "连接服务器") {
                val serverAddress = etServerAddress.text.toString().trim()
                if (serverAddress.isEmpty()) {
                    Toast.makeText(this, "请输入服务器地址", Toast.LENGTH_SHORT).show()
                    return@setOnClickListener
                }
                
                val intent = Intent(this, WebSocketService::class.java).apply {
                    action = WebSocketService.ACTION_CONNECT
                    putExtra(WebSocketService.EXTRA_SERVER_ADDRESS, serverAddress)
                }
                
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    startForegroundService(intent)
                } else {
                    startService(intent)
                }
                
                tvStatus.text = "正在连接: $serverAddress"
                btnConnect.text = "连接中..."
                btnConnect.isEnabled = false
            } else {
                // 断开连接
                stopService(Intent(this, WebSocketService::class.java))
                tvStatus.text = "已断开连接"
                btnConnect.text = "连接服务器"
            }
        }
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
}
