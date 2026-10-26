package org.asc.foundation

import android.app.Activity
import android.app.ActivityManager
import android.content.*
import android.graphics.Color
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.*
import android.text.InputType
import android.view.View
import android.widget.*
import org.json.JSONObject
import java.util.UUID
import java.util.concurrent.Executors

/** Vietnamese foundation UI. Only authenticated real providers or explicit UNKNOWN. */
class MainActivity : Activity() {
    private var engine:ILocalEngine?=null
    private var bound=false
    private var generation=0
    internal var networkEpoch=0
        private set
    internal var networkLosses=0
        private set
    private var observingNetwork=false
    private lateinit var connectivity:ConnectivityManager
    private lateinit var busy:TextView
    private var pending=0
    private val networkObserver=object:ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network:android.net.Network) {changed(false)}
        override fun onLost(network:android.net.Network) {changed(true)}
        private fun changed(lost:Boolean) {runOnUiThread {
            if(observingNetwork && !isFinishing) {
                networkEpoch++;generation++;pending=0;if(::busy.isInitialized)busy.text=""
                if(lost)networkLosses++;verifiedBinding=null
                if(::code.isInitialized)code.setText("")
                if(::joinResult.isInitialized)joinResult.text="Mạng thay đổi · Controller UNKNOWN. Kiểm tra lại TLS/Cluster ID, không tự tin địa chỉ mới."
            }
        }}
    }
    private val worker=Executors.newSingleThreadExecutor()
    private val pages=mutableListOf<View>()
    private lateinit var status:TextView
    private lateinit var outcome:TextView
    private lateinit var volume:TextView
    private lateinit var controller:EditText
    private lateinit var pin:EditText
    private lateinit var cluster:EditText
    private lateinit var nodeName:EditText
    private lateinit var code:EditText
    private lateinit var trust:CheckBox
    private lateinit var joinResult:TextView
    private var verifiedBinding:String?=null
    private var draftRequest=UUID.randomUUID().toString()
    private var joinRequest=UUID.randomUUID().toString()
    private val connection=object:ServiceConnection {
        override fun onServiceConnected(name:ComponentName,binder:IBinder) {engine=ILocalEngine.Stub.asInterface(binder);refresh()}
        override fun onServiceDisconnected(name:ComponentName) {engine=null;status.text="Service UNKNOWN · Node NOT SUPPORTED"}
    }
    private fun dp(value:Int)=(value*resources.displayMetrics.density).toInt()
    private fun text(value:String,size:Float=16f)=TextView(this).apply {text=value;textSize=size;setTextColor(Color.rgb(27,41,61));setPadding(0,dp(8),0,dp(8))}
    private fun panel()=LinearLayout(this).apply {orientation=LinearLayout.VERTICAL;setPadding(dp(16),dp(12),dp(16),dp(20))}
    private fun button(parent:LinearLayout,label:String,tag:String,action:()->Unit):Button = Button(this).apply {
        text=label;this.tag=tag;minHeight=dp(48);isAllCaps=false;setOnClickListener {action()};parent.addView(this)
    }
    private fun field(parent:LinearLayout,label:String,tag:String,secret:Boolean=false):EditText {
        parent.addView(text(label,14f))
        return EditText(this).apply {
            this.tag=tag;minHeight=dp(48);setSingleLine(true)
            inputType=if(secret)InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD else InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
            isSaveEnabled=false;importantForAutofill=View.IMPORTANT_FOR_AUTOFILL_NO
            parent.addView(this)
        }
    }
    override fun onCreate(saved:Bundle?) {
        super.onCreate(saved)
        val root=panel();root.setBackgroundColor(Color.rgb(247,249,252))
        root.addView(text("ASC · Nền tảng Android",24f));root.addView(text("FOUNDATION · Chưa có Node native được nghiệm thu",14f))
        val consent=CheckBox(this).apply {
            tag="consent";text="Cho phép thao tác trong vùng riêng của APK. Không đọc hoặc sao chép Termux."
            isChecked=getSharedPreferences("local-consent",MODE_PRIVATE).getBoolean("granted",false)
            setOnCheckedChangeListener {_,checked ->getSharedPreferences("local-consent",MODE_PRIVATE).edit().putBoolean("granted",checked).commit();if(!checked){code.setText("");verifiedBinding=null;call("stop_owned"){outcome.text=nodeText(it)}}}
        };root.addView(consent)
        busy=text("",13f).apply {tag="loading"};root.addView(busy)
        val tabs=LinearLayout(this);root.addView(tabs)
        val body=FrameLayout(this);root.addView(body,LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,0,1f))
        fun page(label:String):LinearLayout {
            val p=panel();val scroll=ScrollView(this).apply {addView(p);visibility=if(pages.isEmpty())View.VISIBLE else View.GONE}
            pages.add(scroll);body.addView(scroll)
            val index=pages.lastIndex;scroll.tag="page-"+index
            tabs.addView(Button(this).apply {tag="tab-"+index;text=label;textSize=12f;isAllCaps=false;minHeight=dp(54);setPadding(0,0,0,0);setOnClickListener {pages.forEachIndexed {i,v ->v.visibility=if(i==index)View.VISIBLE else View.GONE}}},LinearLayout.LayoutParams(0,dp(60),1f))
            return p
        }
        val overview=page("Tổng quan")
        status=text("Service/Controller/Node UNKNOWN").apply {tag="runtime-status"};overview.addView(status)
        val memory=ActivityManager.MemoryInfo();(getSystemService(ACTIVITY_SERVICE) as ActivityManager).getMemoryInfo(memory)
        val cm=getSystemService(CONNECTIVITY_SERVICE) as ConnectivityManager;connectivity=cm
        val caps=cm.getNetworkCapabilities(cm.activeNetwork)
        val network=when {caps==null->"OFFLINE / UNKNOWN";caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)->"Wi-Fi (không chứng minh Controller online)";caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)->"Ethernet";else->"Kết nối hệ thống, LAN UNKNOWN"}
        overview.addView(text("${Build.MANUFACTURER} ${Build.MODEL} · Android API ${Build.VERSION.SDK_INT}\nRAM đo được: ${memory.totalMem/1048576} MiB · CPU: ${Runtime.getRuntime().availableProcessors()}\nMạng: $network\nReplication: UNKNOWN · Nhiệt độ/uptime liên tục: UNKNOWN"))
        outcome=text("Chưa có thao tác được xác nhận.").apply {tag="operation-result"};overview.addView(outcome)
        button(overview,"Đọc trạng thái","refresh"){refresh()}
        button(overview,"Tạo/kiểm tra identity ứng dụng","provision"){call("app_provision") {outcome.text="Application identity: ${it.optString("state","UNKNOWN")}. Không phải Node/Cluster ID.";refresh()}}
        button(overview,"Kiểm tra thư viện Engine","engine-info"){call("engine_info") {outcome.text=if(it.optString("implementation")=="asc.storage.engine")"Thư viện Core thật có trong APK. Node runtime vẫn NOT SUPPORTED." else message(it)}}
        val join=page("Ghép")
        join.addView(text("Xác minh endpoint, TLS PIN và Cluster ID với owner trước. Enrollment dùng Core hiện có; không tự phê duyệt storage/failure domain hoặc khởi chạy Node."))
        controller=field(join,"Controller HTTPS trong LAN (kèm cổng)","controller")
        pin=field(join,"SHA-256 PIN đầy đủ do owner đối chiếu độc lập","pin")
        cluster=field(join,"Cluster ID dự kiến do owner xác minh","cluster")
        nodeName=field(join,"Tên thiết bị","node-name").apply {setText(Build.MODEL)}
        code=field(join,"Mã ghép một lần (ẩn, không lưu View state)","join-code",true)
        trust=CheckBox(this).apply {text="Tôi đã đối chiếu endpoint, PIN và Cluster ID với owner."};join.addView(trust)
        joinResult=text("Chưa xác minh Controller. Node/enrollment/approval UNKNOWN.").apply {tag="join-result"};join.addView(joinResult)
        button(join,"Kiểm tra TLS và Cluster ID","check-controller") {
            val binding=publicBinding();verifiedBinding=null
            call("check_controller",controller.text.toString().trim(),cleanPin(),cluster.text.toString().trim()) {
                val valid=it.optString("state")=="TLS_AND_CLUSTER_MATCH" && binding==publicBinding()
                if(valid)verifiedBinding=binding
                joinResult.text=if(valid)"TLS PIN và Cluster ID khớp tại thời điểm đọc. Vẫn cần owner xác minh nguồn PIN. Chưa gửi enrollment." else "Controller UNKNOWN · chưa xác minh TLS/cluster; không gửi mã."
            }
        }
        button(join,"Lưu bản nháp mã hóa — chưa gửi","save-draft") {
            if(!trust.isChecked || verifiedBinding!=publicBinding()) {joinResult.text="Cần đối chiếu owner và kiểm tra lại TLS/Cluster ID trước khi lưu.";return@button}
            call("save_join_draft",controller.text.toString().trim(),cleanPin(),cluster.text.toString().trim(),nodeName.text.toString().trim(),code.text.toString(),true,draftRequest) {
                code.setText("");joinResult.text=if(it.optString("state")=="DRAFT_NOT_SENT")"DRAFT_NOT_SENT · đã mã hóa. Chưa enrolled; storage/failure-domain approval UNKNOWN." else message(it)
            }
        }
        button(join,"Xem/khôi phục bản nháp công khai","draft-status") {call("draft_status") {
            if(it.optString("state")=="DRAFT_NOT_SENT") {
                draftRequest=it.getString("request_id");controller.setText(it.getString("controller"));pin.setText(it.getString("pin"));cluster.setText(it.getString("cluster_id"));nodeName.setText(it.getString("name"));trust.isChecked=false;verifiedBinding=null
                joinResult.text="DRAFT_NOT_SENT · khôi phục bindings; mã không hiển thị. Native enrollment vẫn BLOCKED."
            } else joinResult.text=message(it)
        }}
        button(join,"Chuẩn bị context và TLS native (API 30+)","prepare-native-join") {
            call("native_context_init") {ready ->
                if(ready.optString("state")!="CONTEXT_READY")joinResult.text=message(ready)
                else call("native_tls_prepare") {joinResult.text=if(it.optString("tls")=="IDENTITY_READY")
                    "TLS identity đã sẵn sàng. Chưa gửi enrollment; Node chưa chạy." else message(it)}
            }
        }
        button(join,"Gửi mã ghép tới Controller đã xác minh","native-join") {
            if(!trust.isChecked || verifiedBinding!=publicBinding()) {joinResult.text="Cần đối chiếu owner và kiểm tra lại TLS/Cluster ID trước khi gửi mã.";return@button}
            val secret=code.text.toString();code.setText("")
            call("quick_join",controller.text.toString().trim(),cleanPin(),cluster.text.toString().trim(),nodeName.text.toString().trim(),secret,true,joinRequest) {showEnrollment(it)}
        }
        button(join,"Đọc pending/receipt native","native-join-status") {call("native_context_status") {value ->
            if(!value.isNull("enrollment_controller")) {
                controller.setText(value.getString("enrollment_controller"));pin.setText(value.getString("enrollment_pin"))
                cluster.setText(value.getString("expected_cluster_id"));trust.isChecked=false;verifiedBinding=null
            }
            showEnrollment(value)
        }}
        button(join,"Tiếp tục pending đã lưu — không đổi identity","resume-native-join") {call("resume_join") {showEnrollment(it)}}
        button(join,"Thay mã hết hạn của pending hiện có","replace-native-code") {
            if(!trust.isChecked || verifiedBinding!=publicBinding()) {joinResult.text="Đối chiếu owner và kiểm tra lại Controller trước khi thay mã pending.";return@button}
            val secret=code.text.toString();code.setText("")
            call("replace_join_code",secret=secret,trusted=true) {showEnrollment(it)}
        }
        val setup=page("Thiết lập")
        setup.addView(text("Volume này chỉ là APP_PRIVATE_PROBE_ONLY, chưa được cụm phê duyệt. Không tự tạo failure domain, Node hoặc voter."))
        val quota=field(setup,"Quota cho vùng probe (MiB)","quota").apply {inputType=InputType.TYPE_CLASS_NUMBER;setText("8")}
        val reserve=field(setup,"Reserve free space (MiB)","reserve").apply {inputType=InputType.TYPE_CLASS_NUMBER;setText("16")}
        volume=text("Volume/durability UNKNOWN").apply {tag="volume-result"};setup.addView(volume)
        button(setup,"Cho phép volume probe riêng","approve-probe") {
            val q=quota.text.toString().toLongOrNull();val r=reserve.text.toString().toLongOrNull()
            if(q==null || r==null || q !in 1..1048576 || r !in 0..1048576){volume.text="Quota/reserve không hợp lệ.";return@button}
            task({val api=engine ?: error("unavailable");JSONObject(api.approvePrivateProbe(1,UUID.randomUUID().toString(),q*1048576,r*1048576))}) {volume.text=if(it.has("volume_id"))"Đã cho phép volume probe riêng. Quyền storage của cụm vẫn UNKNOWN." else message(it)}
        }
        button(setup,"Đo write/readback/SHA/fsync","probe-volume") {call("probe_private_volume"){volume.text=volumeText(it)}}
        button(setup,"Đọc volume (không suy ra writable)","volume-status"){call("volumes"){volume.text=volumeText(it)}}
        setup.addView(text("SAF/SD/USB: NOT SUPPORTED · fsync/identity UNKNOWN. Vai trò storage chỉ là đề xuất sau probe; không cấp quyền Leader/voter."))
        setup.addView(text("Node thử nghiệm · cần enrollment trước. Vùng Node tách khỏi volume probe. Khi chạy có thông báo và nút Dừng; không cam kết hoạt động 24/7."))
        val nodeQuota=field(setup,"Quota vùng Node (MiB)","node-quota").apply {inputType=InputType.TYPE_CLASS_NUMBER;setText("256")}
        val nodeHost=field(setup,"IP LAN của điện thoại này (loopback để thử cục bộ)","node-host").apply {setText("127.0.0.1")}
        val nodePort=field(setup,"Cổng TLS của Node","node-port").apply {inputType=InputType.TYPE_CLASS_NUMBER;setText("9443")}
        button(setup,"Cho phép vùng Node riêng","approve-node-storage") {
            val q=nodeQuota.text.toString().toLongOrNull()
            if(q==null || q !in 1..1048576){volume.text="Quota Node không hợp lệ.";return@button}
            task({JSONObject((engine ?: error("unavailable")).configureNodeStorage(1,UUID.randomUUID().toString(),q*1048576,0))}) {volume.text=nodeText(it)}
        }
        button(setup,"Chạy Storage Node","start-native-node") {
            if(Build.VERSION.SDK_INT>=33 && checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS),42)
                volume.text="Cho phép thông báo rồi bấm Chạy Storage Node. Chưa khởi chạy Node."
                return@button
            }
            val port=nodePort.text.toString().toIntOrNull()
            if(port==null || port !in 1024..65535){volume.text="Cổng Node không hợp lệ.";return@button}
            val host=nodeHost.text.toString().trim()
            task({JSONObject((engine ?: error("unavailable")).startNode(1,UUID.randomUUID().toString(),host,port))}) {volume.text=nodeText(it)}
        }
        button(setup,"Đọc trạng thái Node","native-node-status") {call("node_status"){volume.text=nodeText(it)}}
        button(setup,"Dừng Node do APK sở hữu","stop-native-node") {call("stop_owned"){volume.text=nodeText(it)}}
        val clusterPage=page("Cụm")
        clusterPage.addView(text("Danh sách node: UNKNOWN\nController/Leader: UNKNOWN\nReplica protection: UNKNOWN\nQuorum: UNKNOWN\nBackup/recovery: UNKNOWN",18f).apply {tag="cluster-status"})
        clusterPage.addView(text("Chưa cấu hình nguồn quan sát được xác thực cho APK. Tiếp tục dùng Dashboard HTTPS hiện có đã xác minh CA; không sao chép admin/node token vào trình duyệt hoặc APK. Không tạo backend/Catalog mới. Recovery staging không được cấp writer."))
        root.setOnApplyWindowInsetsListener {view,insets ->
            if(Build.VERSION.SDK_INT>=30) {
                val bars=insets.getInsets(android.view.WindowInsets.Type.systemBars())
                view.setPadding(dp(8)+bars.left,dp(8)+bars.top,dp(8)+bars.right,dp(8)+bars.bottom)
            } else view.setPadding(dp(8),dp(8)+insets.systemWindowInsetTop,dp(8),dp(8)+insets.systemWindowInsetBottom)
            insets
        }
        setContentView(root);root.requestApplyInsets()
        bound=bindService(Intent(this,EngineService::class.java),connection,Context.BIND_AUTO_CREATE)
    }
    private fun cleanPin()=pin.text.toString().replace(":","").trim().lowercase()
    private fun publicBinding()=listOf(controller.text.toString().trim(),cleanPin(),cluster.text.toString().trim()).joinToString("|")
    private fun showEnrollment(value:JSONObject) {
        if(!value.isNull("join_request_id"))joinRequest=value.getString("join_request_id")
        val state=value.optString("enrollment","UNKNOWN")
        val prefix=if(value.optBoolean("ok",true))"" else message(value)+"\n"
        joinResult.text=prefix+when(state) {
            "ENROLLED_PENDING_APPROVAL"->"Có receipt enrollment: Node ${value.optString("node_id").take(8)} · Cluster ${value.optString("cluster_id").take(8)}. Receipt lịch sử; kết nối/credential hiện tại UNKNOWN. Chờ owner phê duyệt storage và failure domain. Node chưa chạy."
            "PENDING_RECEIPT"->"PENDING_RECEIPT · giữ nguyên operation/token đã mã hóa. Có thể server đã nhận mã; dùng Tiếp tục pending, không tạo identity mới."
            "NOT_CONFIGURED"->"Chưa enrollment. Chuẩn bị context/TLS và xác minh Controller trước."
            else->"Enrollment UNKNOWN · không xác nhận thành công. Giữ state/Keystore hiện có."
        }
    }
    private fun message(value:JSONObject)=when(value.optString("error")) {
        "identity_locked"->"IDENTITY_LOCKED: giữ state/key hiện có; không tạo identity mới."
        "device_not_qualified"->"Thiết bị PROTECTED/UNKNOWN: chỉ xem audit, không tạo state hoặc chạy Engine."
        "consent_required"->"Cần consent rõ ràng cho thao tác vùng riêng của APK."
        "notification_required"->"Cần cho phép thông báo để chạy Node và dùng nút Dừng."
        "invalid_request"->"Thông tin chưa hợp lệ hoặc bindings/code chưa đúng; chưa xác nhận thành công."
        "native_runtime_unqualified"->"BLOCKED: native Node/enrollment/lifecycle chưa được nghiệm thu."
        "native_context_locked"->"Context bị khóa: giữ state/key, không tạo identity mới."
        "cluster_mismatch","binding_mismatch"->"Cluster/bindings không khớp; không thay identity."
        "invalid_or_expired_code"->"Mã hết hạn/không hợp lệ. Giữ pending; chỉ thay bằng mã mới của owner."
        "resume_required"->"Đã có pending khác. Đọc trạng thái và tiếp tục operation cũ."
        "tls_identity_required"->"Cần chuẩn bị TLS identity trước khi gửi enrollment."
        "controller_unverified","enrollment_unconfirmed"->"Chưa xác minh được kết quả qua TLS/Controller. Không coi là thành công; kiểm tra pending và thử tiếp tục."
        "no_pending_enrollment"->"Không có pending để tiếp tục hoặc thay mã."
        "unsupported_runtime"->"Runtime Controller không được hỗ trợ; không fallback sang quorum/recovery."
        else->value.optString("state","UNKNOWN · thao tác chưa được xác nhận")
    }
    private fun volumeText(value:JSONObject):String {
        val v=value.optJSONObject("volume") ?: return message(value)
        fun observed(key:String)=if(v.isNull(key))"UNKNOWN" else v.opt(key).toString()
        return "App-private volume ${v.optString("volume_id").take(8)} · ${v.optString("state","UNKNOWN")}\nQuota: ${observed("quota")} · Reserve: ${observed("reserve")}\nFree: ${observed("free_bytes")} bytes\nReadable: ${observed("readable")} · Writable: ${observed("writable")}\nFsync thực đo: ${observed("fsync_tested")}\nCluster storage/failure-domain approval: UNKNOWN"
    }
    private fun nodeText(value:JSONObject):String {
        if(value.has("error"))return message(value)
        val v=value.optJSONObject("storage")?.optJSONArray("volumes")?.optJSONObject(0)
        fun measured(key:String)=if(v==null || v.isNull(key))"UNKNOWN" else v.opt(key).toString()
        return "Node: ${value.optString("state","UNKNOWN")} · Controller: ${value.optString("controller","UNKNOWN")}\n"+
            "Node ID: ${value.optString("node_id","UNKNOWN").take(8)} · Port: ${value.opt("port") ?: "UNKNOWN"}\n"+
            "Volume: ${v?.optString("volume_id")?.take(8) ?: "UNKNOWN"} · Writable: ${measured("writable")} · Fsync: ${measured("fsync_tested")}\n"+
            "Storage/failure-domain của cụm: chờ owner duyệt. Số replica: UNKNOWN."
    }
    private fun call(op:String,endpoint:String="",fingerprint:String="",expected:String="",name:String="",secret:String="",trusted:Boolean=false,id:String=UUID.randomUUID().toString(),done:(JSONObject)->Unit) {
        task({JSONObject((engine ?: error("unavailable")).request(1,id,op,endpoint,fingerprint,expected,name,secret,trusted))},done)
    }
    private fun task(work:()->JSONObject,done:(JSONObject)->Unit) {
        val current=generation;pending++;busy.text="Đang xử lý nguồn thật · chưa xác nhận kết quả."
        worker.execute {
            val result=try {work()}catch(_:Exception){JSONObject().put("state","UNKNOWN").put("error","service_unavailable")}
            runOnUiThread {if(current==generation && !isFinishing) {pending--;busy.text=if(pending>0)"Đang xử lý nguồn thật…" else "";done(result)}}
        }
    }
    private fun refresh() {call("status") {
        val app=it.optJSONObject("application_identity")
        status.text="Service: ${it.optString("state","UNKNOWN")} · ${it.optString("device_policy","UNKNOWN")}\nApplication identity: ${app?.optString("state") ?: "UNKNOWN"}\nNode/Controller: UNKNOWN · Node runtime NOT SUPPORTED\nStorage/failure-domain approval: UNKNOWN · Writer authority: false"
    }}
    override fun onStart() {super.onStart();pending=0;if(::busy.isInitialized)busy.text=""
        if(::connectivity.isInitialized && !observingNetwork) {observingNetwork=true;connectivity.registerDefaultNetworkCallback(networkObserver)}
        if(engine!=null)refresh()
    }
    override fun onStop() {if(observingNetwork){observingNetwork=false;connectivity.unregisterNetworkCallback(networkObserver)};generation++;if(::code.isInitialized)code.setText("");verifiedBinding=null;super.onStop()}
    override fun onDestroy() {generation++;engine=null;if(bound)unbindService(connection);worker.shutdown();super.onDestroy()}
}
