package org.asc.foundation

import android.app.Activity
import android.os.Bundle
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        setContentView(TextView(this).apply {
            text = "ASC Native Foundation\nEngine: NOT SUPPORTED\nController: UNKNOWN\nNode: UNKNOWN\nKhông truy cập state Termux."
            textSize = 20f
            setPadding(24, 48, 24, 24)
        })
    }
}
