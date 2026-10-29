package org.asc.foundation

import android.content.ContextWrapper
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.chaquo.python.Python
import com.chaquo.python.PyObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.net.Socket
import java.util.UUID
import java.util.concurrent.atomic.AtomicReference
import javax.net.ssl.SSLContext

/** Real JSSE/TCP/Core pinned client/JNI streams; no mock TLS or Storage Node claim. */
@RunWith(AndroidJUnit4::class)
class NativeSocketTest {
    private fun ready(deadline:Long=120000):Triple<NativeTLSListener,String,Python> {
        val base=InstrumentationRegistry.getInstrumentation().targetContext
        val folder=File(base.filesDir,"native-socket-test-"+UUID.randomUUID())
        assertTrue(folder.mkdir());android.system.Os.chmod(folder.absolutePath,448)
        val context=object:ContextWrapper(base) {override fun getFilesDir():File=folder}
        val vault=ApplicationVault(context,"native-socket-test-"+UUID.randomUUID());vault.provision()
        val node=NativeNodeContext(context,vault);node.initialize();val state=node.prepareTls()
        val listener=NativeTLSListener(node.serverTLSContext().toJava(SSLContext::class.java),"127.0.0.1",0,deadline)
        return Triple(listener,state.getString("tls_pin"),Python.getInstance())
    }
    private fun scope(p:Python,vararg fields:Pair<String,Any>):PyObject {
        val result=p.builtins.callAttr("dict")
        fields.forEach {(key,value)->result.callAttr("__setitem__",key,value)}
        return result
    }
    private fun exec(p:Python,code:String,scope:PyObject) {p.builtins.callAttr("exec",code.trimIndent(),scope)}
    private fun accept(listener:NativeTLSListener):NativeTLSConnection {
        val deadline=System.nanoTime()+30_000_000_000L
        while(System.nanoTime()<deadline)listener.accept()?.let {return it}
        error("native_test_accept_deadline")
    }
    @Test fun actualBinaryBufferedStreamsAndWrongPinThroughCanonicalClient() {
        val (listener,pin,p)=ready();val failures=mutableListOf<String>()
        val results=mutableListOf<String>()
        val worker=Thread {
            repeat(2) {attempt ->
                try {
                    val connection=accept(listener)
                    val local=scope(p,"connection" to connection,"attempt" to attempt)
                    exec(p,"""
from asc.node.socket import NativeSocket
import hashlib
sock=NativeSocket(connection)
sock.settimeout(15)
try:
    with sock.makefile() as stream:
        try:header=stream.readline(128)
        except OSError:
            if attempt!=0:raise
            header=b''
        if attempt==0:
            assert header==b''
            result='WRONG_PIN_NO_APPLICATION_BYTES'
        else:
            assert header==b'ASC-native-stream-probe\n'
            remaining=1048576;digest=hashlib.sha256()
            while remaining:
                chunk=stream.read1(min(65536,remaining));assert chunk
                digest.update(chunk);remaining-=len(chunk)
            sock.sendall(digest.hexdigest().encode()+b'\n')
            result='BINARY_SHA_READBACK'
finally:sock.close()
""",local)
                    results.add(local.callAttr("get","result").toString())
                } catch(t:Throwable){failures.add(t.javaClass.simpleName)}
            }
        }.apply {isDaemon=true;start()}
        val client=scope(p,"origin" to "https://127.0.0.1:${listener.port()}","pin" to pin)
        try {
            exec(p,"""
from asc.client import connect_pinned,ClientError
import hashlib
bad=('a' if pin[0]!='a' else 'b')+pin[1:]
try:connect_pinned(origin,bad)
except ClientError:pass
else:raise AssertionError('wrong pin accepted')
conn=connect_pinned(origin,pin)
try:
    data=bytes(range(256))*4096
    conn.sock.sendall(b'ASC-native-stream-probe\n'+data)
    with conn.sock.makefile('rb') as reply:
        assert reply.readline(128)==hashlib.sha256(data).hexdigest().encode()+b'\n'
finally:conn.close()
""",client)
            worker.join(30000);assertFalse(worker.isAlive);assertEquals(emptyList<String>(),failures)
            assertEquals(listOf("WRONG_PIN_NO_APPLICATION_BYTES","BINARY_SHA_READBACK"),results)
            assertEquals(0,listener.activeConnections())
        } finally {listener.close();worker.join(30000)}
        assertTrue(listener.isClosed())
    }
    @Test fun absoluteDeadlineClosesActualIdleHandshakeRead() {
        val (listener,_,p)=ready(3000);val accepted=AtomicReference<NativeTLSConnection>()
        val outcome=AtomicReference<String>();val worker=Thread {
            try {
                val connection=accept(listener);accepted.set(connection)
                val local=scope(p,"connection" to connection)
                exec(p,"""
from asc.node.socket import NativeSocket
sock=NativeSocket(connection)
try:
    try:result='EOF' if sock.makefile().read(1)==b'' else 'UNEXPECTED_BYTES'
    except OSError:result='REFUSED'
finally:sock.close()
""",local)
                outcome.set(local.callAttr("get","result").toString())
            } catch(t:Throwable){outcome.set(t.javaClass.simpleName)}
        }.apply {isDaemon=true;start()}
        try {
            Socket("127.0.0.1",listener.port()).use {
                worker.join(20000);assertFalse(worker.isAlive)
                assertTrue(outcome.get() in setOf("EOF","REFUSED"))
                assertTrue(accepted.get().closedByDeadline());assertTrue(accepted.get().isClosed())
                assertEquals(0,listener.activeConnections())
            }
        } finally {listener.close();worker.join(20000)}
    }
    @Test fun absoluteDeadlineUnblocksActualWriteWhenPinnedPeerDoesNotRead() {
        val (listener,pin,p)=ready(5000);val accepted=AtomicReference<NativeTLSConnection>()
        val outcome=AtomicReference<PyObject>();val failure=AtomicReference<String>()
        val worker=Thread {
            try {
                val connection=accept(listener);accepted.set(connection)
                val local=scope(p,"connection" to connection)
                exec(p,"""
from asc.node.socket import NativeSocket
sock=NativeSocket(connection);written=0;refused=False
try:
    try:
        for _ in range(1024):
            sock.sendall(b'x'*65536);written+=65536
    except OSError:refused=True
finally:sock.close()
assert refused and written>0 and written<67108864
result=True
""",local)
                outcome.set(local.callAttr("get","result"))
            } catch(t:Throwable){failure.set(t.javaClass.simpleName)}
        }.apply {isDaemon=true;start()}
        val client=scope(p,"origin" to "https://127.0.0.1:${listener.port()}","pin" to pin)
        try {
            exec(p,"from asc.client import connect_pinned\nconn=connect_pinned(origin,pin)",client)
            // Keep the real pinned TLS peer open WITHOUT consuming application bytes.
            worker.join(20000);assertFalse(worker.isAlive);assertNull(failure.get())
            assertTrue(outcome.get().toBoolean());assertTrue(accepted.get().closedByDeadline())
            assertTrue(accepted.get().isClosed());assertEquals(0,listener.activeConnections())
        } finally {exec(p,"conn=globals().get('conn')\nif conn is not None:conn.close()",client);listener.close();worker.join(20000)}
    }
}
