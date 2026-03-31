package com.quicknotification

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.util.Log

class SmsReceiver : BroadcastReceiver() {
    
    companion object {
        private const val TAG = "SmsReceiver"
    }
    
    override fun onReceive(context: Context, intent: Intent) {
        try {
            //过滤广播
            if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION
                && intent.action != Telephony.Sms.Intents.SMS_DELIVER_ACTION
                && intent.action != Telephony.Sms.Intents.WAP_PUSH_RECEIVED_ACTION
                && intent.action != Telephony.Sms.Intents.WAP_PUSH_DELIVER_ACTION
            ) return
            
            var from = ""
            var body = ""
            
            if (intent.action == Telephony.Sms.Intents.WAP_PUSH_RECEIVED_ACTION || intent.action == Telephony.Sms.Intents.WAP_PUSH_DELIVER_ACTION) {
                val contentType = intent.type
                if (contentType == "application/vnd.wap.mms-message") {
                    val data = intent.getByteArrayExtra("data")
                    if (data != null) {
                        // 处理收到的 MMS 数据
                        handleMmsData(context, data)
                    }
                }
                
                from = intent.getStringExtra("address") ?: ""
                Log.d(TAG, "from = $from, body = $body")
            } else {
                for (smsMessage in Telephony.Sms.Intents.getMessagesFromIntent(intent)) {
                    from = smsMessage.displayOriginatingAddress
                    body += smsMessage.messageBody
                }
            }
            
            Log.d(TAG, "收到短信 - 发送者: $from, 内容: $body")
            
            val timestamp = java.text.SimpleDateFormat(
                "yyyy-MM-dd HH:mm:ss",
                java.util.Locale.getDefault()
            ).format(java.util.Date())
            
            val smsData = SmsData(from, body, timestamp)
            
            val forwardIntent = Intent(context, WebSocketService::class.java).apply {
                action = WebSocketService.ACTION_SEND_SMS
                putExtra(WebSocketService.EXTRA_SMS_DATA, smsData.toJson())
            }
            
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                context.startForegroundService(forwardIntent)
            } else {
                context.startService(forwardIntent)
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "处理短信失败: ${e.message}", e)
        }
    }
    
    private fun handleMmsData(@Suppress("UNUSED_PARAMETER") context: Context, data: ByteArray) {
        try {
            Log.d(TAG, "收到MMS数据，长度: ${data.size}")
            // MMS处理逻辑
        } catch (e: Exception) {
            Log.e(TAG, "处理MMS失败: ${e.message}", e)
        }
    }
}
