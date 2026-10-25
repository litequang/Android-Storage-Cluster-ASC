package org.asc.foundation
import android.app.Activity
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.os.Bundle
import android.os.IBinder
import android.widget.*
import java.util.UUID

class MainActivity : Activity() {
    private var engine: ILocalEngine?=null
    private var bound=false
    private lateinit var state:TextView
    private val connection=object:ServiceConnection {
        override fun onServiceConnected(name:ComponentName,service:IBinder) {
            engine=ILocalEngine.Stub.asInterface(service);refresh()
        }
        override fun onServiceDisconnected(name:ComponentName) {engine=null;state.text="Service UNKNOWN · Engine NOT SUPPORTED"}
    }
    override fun onCreate(saved:Bundle?) {
        super.onCreate(saved)
        val layout=LinearLayout(this).apply {orientation=LinearLayout.VERTICAL;setPadding(24,48,24,24)}
        layout.addView(TextView(this).apply {text="ASC Native Foundation";textSize=24f})
        state=TextView(this).apply {text="Engine NOT SUPPORTED · Controller/Node UNKNOWN";textSize=17f}
        layout.addView(state)
        layout.addView(CheckBox(this).apply {
            text="Tôi cho phép thao tác nền tảng trong vùng riêng của ứng dụng. Không truy cập Termux."
            isChecked=getSharedPreferences("local-consent",MODE_PRIVATE).getBoolean("granted",false)
            setOnCheckedChangeListener {_,checked ->getSharedPreferences("local-consent",MODE_PRIVATE).edit().putBoolean("granted",checked).commit()}
        })
        layout.addView(Button(this).apply {text="Đọc trạng thái";setOnClickListener {refresh()}})
        layout.addView(TextView(this).apply {text="Chưa có Node native được nghiệm thu. Không khởi tạo hoặc sao chép danh tính Termux."})
        setContentView(ScrollView(this).apply {addView(layout)})
        bound=bindService(Intent(this,EngineService::class.java),connection,Context.BIND_AUTO_CREATE)
    }
    private fun refresh() {
        try {state.text=engine?.request(1,UUID.randomUUID().toString(),"status","","","","","",false) ?: "UNKNOWN"}
        catch (_:Exception) {state.text="Service UNKNOWN"}
    }
    override fun onDestroy() {if(bound)unbindService(connection);super.onDestroy()}
}
