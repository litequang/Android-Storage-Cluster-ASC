package org.asc.foundation

import android.os.Build
import java.io.Closeable
import java.io.IOException
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.ServerSocket
import java.net.Socket
import java.net.SocketTimeoutException
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.ScheduledFuture
import java.util.concurrent.ScheduledThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import javax.net.ssl.SSLContext
import javax.net.ssl.SSLSocket

/** Private platform transport ONLY. No HTTP/Storage Engine, IPC or startup hook. */
internal class NativeTLSListener(private val tls:SSLContext,host:String,port:Int,private val deadlineMillis:Long=120000):Closeable {
    private val lifecycle=Any()
    private val closed=AtomicBoolean(false)
    private val active=ConcurrentHashMap.newKeySet<NativeTLSConnection>()
    private val watchdog=ScheduledThreadPoolExecutor(1) {r ->Thread(r,"asc-owned-tls-deadline").apply {isDaemon=true}}.apply {removeOnCancelPolicy=true}
    private val server:ServerSocket
    private val protocols:Array<String>
    init {
        check(Build.VERSION.SDK_INT>=30 && NativeDeviceGate.allowed()) {"native_tls_device_not_qualified"}
        require(port==0 || port in 1024..65535)
        require(deadlineMillis in 1000..900000)
        val address=approvedAddress(host)
        protocols=tls.supportedSSLParameters.protocols.filter {it in setOf("TLSv1.2","TLSv1.3")}.toTypedArray()
        check(protocols.isNotEmpty())
        server=ServerSocket()
        try {
            // Permit this exclusive listener to restart after accepted sockets enter
            // TCP TIME_WAIT. This is SO_REUSEADDR, never SO_REUSEPORT: a second
            // active listener on the same approved address/port still fails bind.
            server.reuseAddress=true;server.soTimeout=250
            server.bind(InetSocketAddress(address,port),32)
        } catch(e:Throwable) {server.close();watchdog.shutdownNow();throw e}
    }
    fun port():Int=server.localPort
    fun accept():NativeTLSConnection? {
        val transport=try {server.accept()}catch(_:SocketTimeoutException){return null}
        return synchronized(lifecycle) {
            if(closed.get() || active.size>=32) {transport.close();return@synchronized null}
            var peer:SSLSocket?=null
            try {
                transport.soTimeout=12000
                // Retain ONLY this accepted transport so deadline cancellation can
                // interrupt a blocked Conscrypt write before TLS close takes its
                // write lock. Never dispatch plaintext to the Core handler.
                peer=tls.socketFactory.createSocket(transport,transport.inetAddress.hostAddress,transport.port,true) as SSLSocket
                peer.useClientMode=false;peer.needClientAuth=false
                peer.soTimeout=12000;peer.enabledProtocols=protocols
                val connection=NativeTLSConnection(peer,transport) {active.remove(it)}
                active.add(connection)
                try {connection.arm(watchdog,deadlineMillis);connection}
                catch(e:Throwable){connection.close();throw e}
            } catch(e:Throwable) {try {transport.close()} finally {peer?.close()};throw e}
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
internal class NativeTLSConnection(private val peer:SSLSocket,private val transport:Socket,private val removed:(NativeTLSConnection)->Unit):Closeable {
    private val closed=AtomicBoolean(false)
    private val expired=AtomicBoolean(false)
    private val closeCompleted=CountDownLatch(1)
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
    fun isClosed():Boolean=closeCompleted.count==0L && peer.isClosed && transport.isClosed
    override fun close()=closeOwned(false)
    private fun closeOwned(byDeadline:Boolean) {
        if(!closed.compareAndSet(false,true)) {
            // A writer unblocked by the watchdog can reach finally/close before
            // the watchdog removes the connection. Return only after cleanup,
            // never just because another thread has started closing it.
            try {
                if(!closeCompleted.await(12,TimeUnit.SECONDS))throw IOException("native_tls_close_incomplete")
            } catch(e:InterruptedException) {
                Thread.currentThread().interrupt();throw IOException("native_tls_close_interrupted",e)
            }
        } else {
            if(byDeadline)expired.set(true)
            deadline?.cancel(false)
            // Socket.close interrupts actual TCP I/O. Closing the layered TLS
            // socket first can wait indefinitely for its blocked write lock.
            try {transport.close()}catch(_:IOException){} finally {
                try {peer.close()}catch(_:IOException){} finally {
                    try {removed(this)} finally {closeCompleted.countDown()}
                }
            }
        }
    }
}
