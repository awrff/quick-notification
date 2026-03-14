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
            btnConnect.text = "已连接"
            btnConnect.isEnabled = false
        }
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            val allGranted = grantResults.all { it == PackageManager.PERMISSION_GRANTED }
            if (!allGranted) {
                Toast.makeText(this, "需要短信权限才能转发短信", Toast.LENGTH_LONG).show()
            }
        }
    }
    
    fun updateStatus(status: String) {
        tvStatus.text = status
    }
}
