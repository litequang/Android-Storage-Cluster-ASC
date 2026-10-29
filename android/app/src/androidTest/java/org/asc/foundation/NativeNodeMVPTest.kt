package org.asc.foundation

import android.content.*
import android.os.IBinder
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.core.app.ActivityScenario
import com.chaquo.python.Python
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/** Actual existing enrolled app +Binder/JSSE/Core Engine. Task-owned AVD ONLY.
 * Operator fixture contains synthetic owner grant credentials, never APK assets. */
@RunWith(AndroidJUnit4::class)
class NativeNodeMVPTest {
    @Test fun retainedNodeAndFileAfterFreshProcess() {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        EmbeddedEngine(c)
        val node=NativeNodeSession(c,ApplicationVault(c))
        val python=Python.getInstance();val scope=python.builtins.callAttr("dict")
        scope.callAttr("__setitem__","context",NativeNodeContext(c,ApplicationVault(c)).engineContext())
        scope.callAttr("__setitem__","fixture",python.getModule("json").callAttr("loads",File(c.filesDir,"native-mvp-network-fixture.json").readText()))
        scope.callAttr("__setitem__","proof",python.getModule("json").callAttr("loads",File(c.filesDir,"native-mvp-proof.json").readText()))
        try {
            assertEquals("RUNNING",node.start("127.0.0.1",9443).getString("state"))
            python.builtins.callAttr("exec","""
import hashlib,io
from asc.client import request_json
from asc.storage.client import StorageClient
record=context.load()
for key in ('app_id','context_id'):
    assert record[key]==proof[key]
assert record['node']['node_id']==proof['node_id']
assert record['node']['cluster_id']==proof['cluster_id']
assert hashlib.sha256(record['node']['token'].encode()).hexdigest()==proof['token_sha256']
assert record['tls']['pin']==proof['tls_pin']
assert record['storage']['volume_id']==proof['volume_id']
grant=request_json(fixture['origin'],fixture['pin'],'POST','/api/v1/admin/storage-grant',
    {'node_id':proof['node_id'],'volume_id':proof['volume_id'],'operations':['read']},fixture['owner_token'])['grant']
output=io.BytesIO()
StorageClient('https://127.0.0.1:9443',proof['tls_pin'],grant,proof['volume_id']).download(
    proof['file_id'],output,proof['size'],proof['sha256'])
assert hashlib.sha256(output.getvalue()).hexdigest()==proof['sha256']
""".trimIndent(),scope)
        } finally {node.close()}
    }
    @Test fun actualBinderNodeTlsFileShaHeartbeatAndRestart() {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        assertTrue(NativeDeviceGate.allowed())
        val fixture=File(c.filesDir,"native-mvp-network-fixture.json").readText()
        c.getSharedPreferences("local-consent",Context.MODE_PRIVATE).edit().putBoolean("granted",true).commit()
        val activity=ActivityScenario.launch(MainActivity::class.java)
        var api:ILocalEngine?=null;val ready=CountDownLatch(1)
        val connection=object:ServiceConnection {
            override fun onServiceConnected(name:ComponentName,binder:IBinder) {api=ILocalEngine.Stub.asInterface(binder);ready.countDown()}
            override fun onServiceDisconnected(name:ComponentName) {api=null}
        }
        assertTrue(c.bindService(Intent(c,EngineService::class.java),connection,Context.BIND_AUTO_CREATE))
        try {
            assertTrue(ready.await(15,TimeUnit.SECONDS));EmbeddedEngine(c)
            val python=Python.getInstance();val scope=python.builtins.callAttr("dict")
            scope.callAttr("__setitem__","api",api!!)
            scope.callAttr("__setitem__","context",NativeNodeContext(c,ApplicationVault(c)).engineContext())
            scope.callAttr("__setitem__","fixture",python.getModule("json").callAttr("loads",fixture))
            scope.callAttr("__setitem__","files",c.filesDir.canonicalPath)
            python.builtins.callAttr("exec","""
import hashlib,io,json,time,uuid
from pathlib import Path
from asc.client import request_json
from asc.storage.client import StorageClient
before=context.load()
assert before['node']['node_id']==fixture['node_id']
assert before['node']['cluster_id']==fixture['cluster_id']
assert before['node']['controller']==fixture['origin'] and before['node']['pin']==fixture['pin']
def call(op):return json.loads(str(api.request(1,str(uuid.uuid4()),op,'','','','','',False)))
configured=json.loads(str(api.configureNodeStorage(1,str(uuid.uuid4()),256*1024**2,0)))
assert configured['state']=='LOCAL_VOLUME_READY',configured
volume=configured['storage']['volumes'][0]
assert volume['writable'] is True and volume['fsync_tested'] is True
started=json.loads(str(api.startNode(1,str(uuid.uuid4()),'127.0.0.1',9443)))
assert started['state']=='RUNNING',started
deadline=time.monotonic()+20
while time.monotonic()<deadline:
    status=call('node_status')
    if status['controller']=='ONLINE':break
    time.sleep(.1)
assert status['controller']=='ONLINE',status
grant=request_json(fixture['origin'],fixture['pin'],'POST','/api/v1/admin/storage-grant',
    {'node_id':before['node']['node_id'],'volume_id':volume['volume_id'],
     'operations':['read','write','list','verify']},fixture['owner_token'])['grant']
client=StorageClient('https://127.0.0.1:9443',before['tls']['pin'],grant,volume['volume_id'])
data=bytes(range(256))*1024;sha=hashlib.sha256(data).hexdigest()
session=client.initiate('android_native_mvp_1','native/mvp.bin',len(data),sha)
if session['state']!='COMMITTED':client.upload(session['session_id'],io.BytesIO(data),len(data))
saved=client.commit(session['session_id'])
assert client.json('POST','files/'+saved['file_id']+'/verify',{})['state']=='COMMITTED'
assert call('stop_owned')['state']=='STOPPED'
assert json.loads(str(api.startNode(1,str(uuid.uuid4()),'127.0.0.1',9443)))['state']=='RUNNING'
output=io.BytesIO();client.download(saved['file_id'],output,len(data),sha)
assert output.getvalue()==data
after=context.load()
for key in ('app_id','context_id','binding','device_binding','node','tls','pending'):
    assert before[key]==after[key],'existing identity changed'
assert after['storage']['volume_id']==volume['volume_id']
proof={'format':1,'app_id':after['app_id'],'context_id':after['context_id'],
    'node_id':after['node']['node_id'],'cluster_id':after['node']['cluster_id'],
    'tls_pin':after['tls']['pin'],'token_sha256':hashlib.sha256(after['node']['token'].encode()).hexdigest(),
    'volume_id':volume['volume_id'],'file_id':saved['file_id'],'size':len(data),'sha256':sha,
    'scope':'actual API35 Binder/JSSE/Engine, explicit dev reverse; not direct LAN, not two replicas/FGS'}
(Path(files)/'native-mvp-proof.json').write_text(json.dumps(proof))
assert call('stop_owned')['state']=='STOPPED'
""".trimIndent(),scope)
        } finally {
            try {api?.request(1,java.util.UUID.randomUUID().toString(),"stop_owned","","","","","",false)}catch(_:Exception){}
            c.unbindService(connection)
            activity.close()
        }
    }
}
