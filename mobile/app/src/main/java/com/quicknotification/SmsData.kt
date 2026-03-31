package com.quicknotification

import com.google.gson.Gson

data class SmsData(
    val sender: String,
    val content: String,
    val timestamp: String
) {
    fun toJson(): String {
        return Gson().toJson(this)
    }
}
