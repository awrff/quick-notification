package com.smsforwarder

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import com.google.gson.Gson
import org.java_websocket.client.WebSocketClient
import org.java_websocket.handshake.ServerHandshake
import java.net.URI
import java.util.concurrent.ConcurrentLinkedQueue

class WebSocketService : Service() {
    
    companion object {
        const val ACTION_CONNECT = "com.smsforwarder.CONNECT"
        const val ACTION_SEND_SMS = "com.smsforwarder.SEND_SMS"
        const val EXTRA_SERVER_ADDRESS = "server_address"
        const val EXTRA_SMS_DATA = "sms_data"
        
        private const val CHANNEL_ID = "sms_forwarder_channel"
        private const val NOTIFICATION_ID = 1
        private const val TAG = "WebSocketService"
        
        private var webSocketClient: WebSocketClient? = null
        private val messageQueue = ConcurrentLinkedQueue<String>()
        private var currentServerAddress: String? = null
        private val reconnectHandler = Handler(Looper.getMainLooper())
        private var isConnected = false
        private var retryCount = 0
        private const val MAX_RETRIES = 3
        private var isConnecting = false
    }
    
    private val gson = Gson()
    
    private val reconnectRunnable = object : Runnable {
        override fun run() {
            if (!isConnected && currentServerAddress != null && retryCount < MAX_RETRIES && !isConnecting) {
                retryCount++
                Log.d(TAG, "尝试重新连接 ($retryCount/$MAX_RETRIES)...")
                MainActivity.messageLogCallback?.invoke("尝试重新连接 ($retryCount/$MAX_RETRIES)...")
                connectToServer(currentServerAddress!!)
            } else if (retryCount >= MAX_RETRIES) {
                Log.d(TAG, "重试次数已达上限，停止自动重试")
                MainActivity.messageLogCallback?.invoke("重试次数已达上限，请手动重新连接")
                MainActivity.connectionStateCallback?.invoke(false)
            }
        }
    }
    
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "========== WebSocketService onCreate ==========")
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, createNotification())
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_CONNECT -> {
                val serverAddress = intent.getStringExtra(EXTRA_SERVER_ADDRESS)
                if (serverAddress != null) {
                    currentServerAddress = serverAddress
                    retryCount = 0
                    // 终止上一次连接
                    webSocketClient?.close()
                    webSocketClient = null
                    isConnected = false
                    isConnecting = false
                    connectToServer(serverAddress)
                    reconnectHandler.postDelayed(reconnectRunnable, 5000)
                }
            }
            ACTION_SEND_SMS -> {
                val smsData = intent.getStringExtra(EXTRA_SMS_DATA)
                if (smsData != null) {
                    sendMessage(smsData)
                }
            }
        }
        return START_STICKY
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "短信转发服务",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "保持短信转发服务运行"
            }
            
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }
    
    private fun createNotification(): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )
        
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
                .setContentTitle("短信转发服务")
                .setContentText("正在运行中...")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentIntent(pendingIntent)
                .build()
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
                .setContentTitle("短信转发服务")
                .setContentText("正在运行中...")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentIntent(pendingIntent)
                .build()
        }
    }
    
    private fun connectToServer(serverAddress: String) {
        try {
            Log.d(TAG, "正在连接到: $serverAddress")
            MainActivity.messageLogCallback?.invoke("正在连接: $serverAddress")
            
            val uri = if (serverAddress.startsWith("ws://") || serverAddress.startsWith("wss://")) {
                URI(serverAddress)
            } else {
                URI("ws://$serverAddress")
            }
            
            // 确保终止上一次连接
            webSocketClient?.close()
            webSocketClient = null
            isConnecting = true
            
            webSocketClient = object : WebSocketClient(uri) {
                override fun onOpen(handshakedata: ServerHandshake?) {
                    Log.d(TAG, "WebSocket已打开 - HTTP状态: ${handshakedata?.httpStatus}")
                    isConnected = true
                    isConnecting = false
                    retryCount = 0
                    MainActivity.messageLogCallback?.invoke("已连接到服务器")
                    MainActivity.connectionStateCallback?.invoke(true)
                    
                    while (messageQueue.isNotEmpty()) {
                        val msg = messageQueue.poll()
                        send(msg)
                        Log.d(TAG, "发送队列消息: $msg")
                    }
                }
                
                override fun onMessage(message: String?) {
                    Log.d(TAG, "收到消息: $message")
                }
                
                override fun onClose(code: Int, reason: String?, remote: Boolean) {
                    Log.d(TAG, "连接关闭 - code: $code, reason: $reason, remote: $remote")
                    isConnected = false
                    isConnecting = false
                    MainActivity.messageLogCallback?.invoke("连接关闭: $reason (code: $code)")
                    MainActivity.connectionStateCallback?.invoke(false)
                    
                    // 重新调度重试
                    if (retryCount < MAX_RETRIES) {
                        reconnectHandler.postDelayed(reconnectRunnable, 5000)
                    }
                }
                
                override fun onError(ex: Exception?) {
                    Log.e(TAG, "连接错误", ex)
                    isConnected = false
                    isConnecting = false
                    MainActivity.messageLogCallback?.invoke("连接错误: ${ex?.javaClass?.simpleName} - ${ex?.message}")
                    MainActivity.connectionStateCallback?.invoke(false)
                    
                    // 重新调度重试
                    if (retryCount < MAX_RETRIES) {
                        reconnectHandler.postDelayed(reconnectRunnable, 5000)
                    }
                }
            }
            
            webSocketClient?.connectionLostTimeout = 10
            webSocketClient?.connect()
            
        } catch (e: Exception) {
            Log.e(TAG, "连接失败", e)
            isConnected = false
            isConnecting = false
            MainActivity.messageLogCallback?.invoke("连接失败: ${e.message}")
            MainActivity.connectionStateCallback?.invoke(false)
            
            // 重新调度重试
            if (retryCount < MAX_RETRIES) {
                reconnectHandler.postDelayed(reconnectRunnable, 5000)
            }
        }
    }
    
    private fun sendMessage(message: String) {
        if (webSocketClient != null && isConnected) {
            try {
                webSocketClient?.send(message)
                Log.d(TAG, "已发送短信: $message")
                MainActivity.messageLogCallback?.invoke("已转发短信")
            } catch (e: Exception) {
                Log.e(TAG, "发送失败", e)
                messageQueue.offer(message)
                MainActivity.messageLogCallback?.invoke("发送失败，已加入队列")
            }
        } else {
            messageQueue.offer(message)
            Log.d(TAG, "连接未就绪，消息已加入队列")
            MainActivity.messageLogCallback?.invoke("连接未就绪，消息已加入队列")
        }
    }
    
    override fun onDestroy() {
        reconnectHandler.removeCallbacks(reconnectRunnable)
        webSocketClient?.close()
        super.onDestroy()
    }
}
