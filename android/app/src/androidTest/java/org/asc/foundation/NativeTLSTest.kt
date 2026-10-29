package org.asc.foundation

import android.content.ContextWrapper
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.chaquo.python.Python
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID

@RunWith(AndroidJUnit4::class)
class NativeTLSTest {
    @Test fun actualAnonymousTlsPlatformCapabilities() {
        EmbeddedEngine(InstrumentationRegistry.getInstrumentation().targetContext)
        val p=Python.getInstance();val globals=p.getModule("builtins").callAttr("dict")
        p.getModule("builtins").callAttr("exec","""
import os,fcntl,json,ctypes
from asc.node.tls import _sealed_bytes
result={'python_memfd':hasattr(os,'memfd_create'),'os_flags':all(hasattr(os,k) for k in ('MFD_CLOEXEC','MFD_ALLOW_SEALING')),
        'fcntl_seals':all(hasattr(fcntl,k) for k in ('F_ADD_SEALS','F_SEAL_SEAL','F_SEAL_SHRINK','F_SEAL_GROW','F_SEAL_WRITE'))}
try:result['bionic_memfd']=hasattr(ctypes.CDLL('libc.so'),'memfd_create')
except Exception:result['bionic_memfd']=False
with _sealed_bytes(b'actual-owned-anonymous-marker') as fd:
    assert os.pread(fd,1024,0)==b'actual-owned-anonymous-marker'
    assert fcntl.fcntl(fd,fcntl.F_GETFD)&fcntl.FD_CLOEXEC
    seals=fcntl.fcntl(fd,fcntl.F_GET_SEALS)
    assert seals & (fcntl.F_SEAL_SEAL|fcntl.F_SEAL_SHRINK|fcntl.F_SEAL_GROW|fcntl.F_SEAL_WRITE)==15
    denied=False
    try:os.write(fd,b'cannot-mutate-sealed-memory')
    except PermissionError:denied=True
    assert denied
try:os.fstat(fd)
except OSError:result['closed_after_use']=True
else:result['closed_after_use']=False
proof=json.dumps(result)
""".trimIndent(),globals)
        val proof=JSONObject(globals.callAttr("get","proof").toString())
        assertTrue("actual anonymous TLS platform proof: $proof",proof.getBoolean("fcntl_seals") && proof.getBoolean("closed_after_use") &&
            ((proof.getBoolean("python_memfd") && proof.getBoolean("os_flags")) || proof.getBoolean("bionic_memfd")))
    }
    @Test fun standardX509ProviderGeneratesActualSelfSignedCertificate() {
        val identity=JSONObject(NativeTLSIdentity().generate())
        assertTrue(identity.getString("private_key").startsWith("-----BEGIN PRIVATE KEY-----\n"))
        val cert=java.security.cert.CertificateFactory.getInstance("X.509").generateCertificate(identity.getString("certificate").byteInputStream()) as java.security.cert.X509Certificate
        cert.verify(cert.publicKey)
        assertEquals("EC",cert.publicKey.algorithm)
        val pin=java.security.MessageDigest.getInstance("SHA-256").digest(cert.encoded).joinToString(""){"%02x".format(it)}
        assertEquals(pin,identity.getString("pin"))
        NativeTLSLoader().load(identity.getString("certificate"),identity.getString("private_key"))
        val other=JSONObject(NativeTLSIdentity().generate())
        assertThrows(Exception::class.java) {NativeTLSLoader().load(identity.getString("certificate"),other.getString("private_key"))}
        assertThrows(Exception::class.java) {NativeTLSLoader().load(identity.getString("certificate"),"invalid synthetic key")}
    }
    @Test fun platformDefaultTrustRejectsUntrustedSelfSignedPeer() {
        val identity=JSONObject(NativeTLSIdentity().generate())
        val tls=NativeTLSLoader().load(identity.getString("certificate"),identity.getString("private_key"))
        val server=tls.serverSocketFactory.createServerSocket(0,1,java.net.InetAddress.getByName("127.0.0.1")) as javax.net.ssl.SSLServerSocket
        server.enabledProtocols=server.supportedProtocols.filter {it in setOf("TLSv1.2","TLSv1.3")}.toTypedArray()
        server.soTimeout=15000
        val errors=mutableListOf<String>()
        val worker=Thread {
            try {(server.accept() as javax.net.ssl.SSLSocket).use {peer ->
                peer.soTimeout=15000;peer.startHandshake()
                check(peer.inputStream.read()==-1) // No application bytes from rejected client.
            }} catch(_:javax.net.ssl.SSLException) { /* Expected untrusted-client TLS alert. */ }
            catch(e:Throwable){errors.add(e.javaClass.simpleName)}
        }.apply {isDaemon=true;start()}
        try {
            val client=tls.socketFactory.createSocket("127.0.0.1",server.localPort) as javax.net.ssl.SSLSocket
            client.soTimeout=15000
            assertThrows(javax.net.ssl.SSLHandshakeException::class.java) {client.use {it.startHandshake()}}
            worker.join(20000);assertFalse(worker.isAlive);assertEquals(emptyList<String>(),errors)
        } finally {server.close();worker.join(20000)}
    }
    @Test fun missingTlsCredentialOrWrappingKeyNeverRegeneratesIdentity() {
        val base=InstrumentationRegistry.getInstrumentation().targetContext
        for(fault in listOf("missing-record","missing-witness","lost-key")) {
            val folder=File(base.filesDir.canonicalFile,"tls-loss-test-"+UUID.randomUUID())
            assertTrue(folder.mkdir());android.system.Os.chmod(folder.absolutePath,448)
            val context=object:ContextWrapper(base) {override fun getFilesDir():File=folder}
            val vault=ApplicationVault(context,"tls-loss-"+UUID.randomUUID());vault.provision()
            val node=NativeNodeContext(context,vault);node.initialize();node.prepareTls()
            val metadata=File(vault.root,"application.json").readBytes()
            val anchor=File(folder,"native-runtime-v1/native-node-v1/context.json");val before=anchor.readBytes()
            when(fault) {
                "missing-record" -> assertTrue(File(vault.root,"node-context.json").renameTo(File(vault.root,"held-record.json")))
                "missing-witness" -> assertTrue(File(vault.root,"node-context-required.json").renameTo(File(vault.root,"held-witness.json")))
                "lost-key" -> java.security.KeyStore.getInstance("AndroidKeyStore").apply {load(null);deleteEntry(vault.alias)}
            }
            assertThrows(Exception::class.java) {node.prepareTls()};assertThrows(Exception::class.java) {node.status()}
            assertArrayEquals(before,anchor.readBytes());assertArrayEquals(metadata,File(vault.root,"application.json").readBytes())
            if(fault=="missing-record")assertFalse(File(vault.root,"node-context.json").exists())
            if(fault=="missing-witness")assertFalse(File(vault.root,"node-context-required.json").exists())
            if(fault=="lost-key")assertEquals("IDENTITY_LOCKED",vault.state().getString("state"))
        }
    }
    @Test fun actualStandardX509KeystoreSealingAnonymousTlsAndPinRefusal() {
        val base=InstrumentationRegistry.getInstrumentation().targetContext
        val folder=File(base.filesDir.canonicalFile,"native-tls-test-"+UUID.randomUUID())
        assertTrue(folder.mkdir());android.system.Os.chmod(folder.absolutePath,448)
        val context=object:ContextWrapper(base) {override fun getFilesDir():File=folder}
        val vault=ApplicationVault(context,"native-tls-"+UUID.randomUUID());val app=vault.provision().getString("app_id")
        val node=NativeNodeContext(context,vault);node.initialize()
        val identity=node.prepareTls();val pin=identity.getString("tls_pin")
        assertTrue(pin.matches(Regex("[a-f0-9]{64}")));assertEquals("IDENTITY_READY",identity.getString("tls"))
        assertTrue(identity.isNull("node_id"));assertTrue(identity.isNull("cluster_id"))
        assertFalse(identity.has("private_key"));assertFalse(identity.has("certificate"))
        val ciphertext=File(vault.root,"node-context.json").readBytes()
        val restarted=NativeNodeContext(context,ApplicationVault(context,vault.root.name))
        assertEquals(pin,restarted.prepareTls().getString("tls_pin"))
        assertEquals(app,restarted.status().getString("application_id"))
        assertArrayEquals(ciphertext,File(vault.root,"node-context.json").readBytes())
        // Actual Android JSSE TLS server; canonical Python pin verifier is the
        // client. Explicit guest loopback only, NOT LAN or a joined Node.
        val tls=node.serverTLSContext().toJava(javax.net.ssl.SSLContext::class.java)
        val listener=tls.serverSocketFactory.createServerSocket(0,2,java.net.InetAddress.getByName("127.0.0.1")) as javax.net.ssl.SSLServerSocket
        listener.enabledProtocols=listener.supportedProtocols.filter {it in setOf("TLSv1.2","TLSv1.3")}.toTypedArray()
        listener.soTimeout=15000
        val expected="actual-native-tls-synthetic-only".toByteArray()
        val received=mutableListOf<String>();val errors=mutableListOf<String>()
        val worker=Thread {
            try {
                repeat(2) {attempt ->
                    val raw=listener.accept() as javax.net.ssl.SSLSocket
                    raw.soTimeout=15000
                    try {raw.use {peer ->
                        peer.startHandshake()
                        val input=peer.inputStream;val bytes=ByteArray(expected.size);var count=0
                        while(count<bytes.size) {val n=input.read(bytes,count,bytes.size-count);if(n<0)break;count+=n}
                        if(count==0)received.add("EOF") else {
                            check(attempt==1 && count==expected.size && bytes.contentEquals(expected))
                            received.add("VALID_BODY")
                            val hash=java.security.MessageDigest.getInstance("SHA-256").digest(bytes).joinToString(""){"%02x".format(it)}
                            peer.outputStream.write(hash.toByteArray());peer.outputStream.flush()
                        }
                    }} catch(e:java.io.IOException) {
                        if(attempt!=0)throw e
                        received.add("CLOSED_BEFORE_DATA")
                    }
                }
            } catch(e:Throwable){errors.add(e.javaClass.simpleName)}
        }.apply {isDaemon=true;start()}
        val python=Python.getInstance();val globals=python.getModule("builtins").callAttr("dict")
        python.getModule("builtins").callAttr("exec","""
import hashlib,json
from asc.client import connect_pinned,ClientError
def prove(port,pin):
    origin='https://127.0.0.1:'+str(port);rejected=False
    try:connect_pinned(origin,'0'*64,timeout=12)
    except ClientError:rejected=True
    assert rejected
    conn=connect_pinned(origin,pin,timeout=12)
    body=b'actual-native-tls-synthetic-only'
    try:
        conn.sock.sendall(body);reply=b''
        while len(reply)<64:
            chunk=conn.sock.recv(64-len(reply))
            if not chunk:break
            reply+=chunk
        assert reply==hashlib.sha256(body).hexdigest().encode()
        return json.dumps({'state':'ACTUAL_LOCAL_TLS_PASS','wrong_pin_rejected':rejected,'sha256_match':True})
    finally:conn.close()
""".trimIndent(),globals)
        try {
            val proof=JSONObject(globals.callAttr("get","prove").call(listener.localPort,pin).toString())
            assertEquals("ACTUAL_LOCAL_TLS_PASS",proof.getString("state"));assertTrue(proof.getBoolean("wrong_pin_rejected"))
            worker.join(20000);assertFalse(worker.isAlive);assertEquals(emptyList<String>(),errors)
            assertEquals(2,received.size);assertTrue(received[0] in listOf("EOF","CLOSED_BEFORE_DATA"));assertEquals("VALID_BODY",received[1])
        } finally {listener.close();worker.join(20000)}
        for(file in folder.walkTopDown().filter {it.isFile}) {
            assertFalse(file.name.endsWith(".key") || file.name.endsWith(".pem"))
            assertFalse(file.readText().contains("-----BEGIN PRIVATE KEY-----"))
        }
        val record=File(vault.root,"node-context.json")
        record.writeText("{}")
        assertThrows(Exception::class.java) {restarted.prepareTls()}
        assertEquals("{}",record.readText())
        record.writeBytes(ciphertext) // ONLY this isolated, controlled fault fixture.
        assertEquals(pin,restarted.prepareTls().getString("tls_pin"))
    }
}
