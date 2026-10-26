package org.asc.foundation

import android.os.Build
import java.io.Closeable
import java.io.IOException
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.SocketTimeoutException
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ScheduledFuture
import java.util.concurrent.ScheduledThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import javax.net.ssl.SSLContext
import javax.net.ssl.SSLServerSocket
import javax.net.ssl.SSLSocket

/** Private platform transport ONLY. No HTTP/Storage Engine, IPC or startup hook. */
internal class NativeTLSListener(tls:SSLContext,host:String,port:Int,private val deadlineMillis:Long=120000):Closeable {
    private val lifecycle=Any()
    private val closed=AtomicBoolean(false)
    private val active=ConcurrentHashMap.newKeySet<NativeTLSConnection>()
    private val watchdog=ScheduledThreadPoolExecutor(1) {r ->Thread(r,"asc-owned-tls-deadline").apply {isDaemon=true}}.apply {removeOnCancelPolicy=true}
    private val server:SSLServerSocket
    init {
        check(Build.VERSION.SDK_INT>=30 && NativeDeviceGate.allowed()) {"native_tls_device_not_qualified"}
        require(port==0 || port in 1024..65535)
        require(deadlineMillis in 1000..900000)
        val address=approvedAddress(host)
        server=tls.serverSocketFactory.createServerSocket() as SSLServerSocket
        try {
            server.enabledProtocols=server.supportedProtocols.filter {it in setOf("TLSv1.2","TLSv1.3")}.toTypedArray()
            check(server.enabledProtocols.isNotEmpty())
            server.reuseAddress=false;server.needClientAuth=false;server.soTimeout=250
            server.bind(InetSocketAddress(address,port),32)
        } catch(e:Throwable) {server.close();watchdog.shutdownNow();throw e}
    }
    fun port():Int=server.localPort
    fun accept():NativeTLSConnection? {
        val peer=try {server.accept() as SSLSocket}catch(_:SocketTimeoutException){return null}
        return synchronized(lifecycle) {
            if(closed.get() || active.size>=32) {peer.close();return@synchronized null}
            try {
                peer.soTimeout=12000
                peer.enabledProtocols=peer.supportedProtocols.filter {it in setOf("TLSv1.2","TLSv1.3")}.toTypedArray()
                val connection=NativeTLSConnection(peer) {active.remove(it)}
                active.add(connection)
                try {connection.arm(watchdog,deadlineMillis);connection}
                catch(e:Throwable){connection.close();throw e}
            } catch(e:Throwable) {peer.close();throw e}
        }
    }
    fun activeConnections():Int=active.size
    fun isClosed():Boolean=closed.get() && server.isClosed
    override fun close() {synchronized(lifecycle) {
        if(closed.compareAndSet(false,true)) {
            try {server.close()} finally {
                active.toList().forEach {it.close()};active.clear();watchdog.shutdownNow()
            }
        }
    }}
    companion object {
        // Numeric RFC1918/loopback only. No wildcard, DNS, public or implicit bind.
        internal fun approvedAddress(host:String):InetAddress {
            val parts=host.split('.')
            require(parts.size==4 && parts.all {it.toIntOrNull() in 0..255 && (it=="0" || !it.startsWith('0'))})
            val values=parts.map {it.toInt()}
            require(values[0]==127 || values[0]==10 || values[0]==192 && values[1]==168 || values[0]==172 && values[1] in 16..31)
            return InetAddress.getByAddress(values.map {it.toByte()}.toByteArray())
        }
    }
}

/** Public JNI methods operate ONLY this exact accepted socket. No fd/path/PID. */
internal class NativeTLSConnection(private val peer:SSLSocket,private val removed:(NativeTLSConnection)->Unit):Closeable {
    private val closed=AtomicBoolean(false)
    private val expired=AtomicBoolean(false)
    @Volatile private var deadline:ScheduledFuture<*>?=null
    internal fun arm(watchdog:ScheduledThreadPoolExecutor,millis:Long) {
        val task=watchdog.schedule({closeOwned(true)},millis,TimeUnit.MILLISECONDS)
        deadline=task;if(closed.get())task.cancel(false)
    }
    fun read(size:Int):ByteArray {
        require(size in 1..65536)
        val bytes=ByteArray(size);var count:Int
        do {count=peer.inputStream.read(bytes)}while(count==0)
        return if(count<0)ByteArray(0) else bytes.copyOf(count)
    }
    fun write(bytes:ByteArray) {
        require(bytes.size<=65536)
        peer.outputStream.write(bytes)
    }
    fun setTimeoutMillis(millis:Int) {require(millis in 1..900000);peer.soTimeout=millis}
    fun timeoutMillis():Int=peer.soTimeout
    fun peerAddress():String=peer.inetAddress.hostAddress ?: throw IOException("native_peer_unknown")
    fun peerPort():Int=peer.port
    fun closedByDeadline():Boolean=expired.get()
    fun isClosed():Boolean=closed.get() && peer.isClosed
    override fun close()=closeOwned(false)
    private fun closeOwned(byDeadline:Boolean) {
        if(closed.compareAndSet(false,true)) {
            if(byDeadline)expired.set(true)
            deadline?.cancel(false)
            try {peer.close()}catch(_:IOException){} finally {removed(this)}
        }
    }
}
