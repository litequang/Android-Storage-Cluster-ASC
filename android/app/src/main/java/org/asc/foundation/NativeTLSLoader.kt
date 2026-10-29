package org.asc.foundation

import android.os.Build
import android.util.Base64
import java.security.KeyFactory
import java.security.KeyStore
import java.security.SecureRandom
import java.security.Signature
import java.security.cert.CertificateFactory
import java.security.cert.X509Certificate
import java.security.spec.PKCS8EncodedKeySpec
import javax.net.ssl.KeyManagerFactory
import javax.net.ssl.SSLContext

/** Explicit Android JSSE provider. Trusted JNI ONLY, no Binder/provider selector.
 * Input is read back from sealed anonymous descriptors; all key objects and the
 * PKCS12 container stay in RAM. Never opens proc, writes a key/store, registers a
 * global security provider, changes SELinux or supplies network authority.
 */
class NativeTLSLoader {
    fun load(certificate:String,privateKey:String):SSLContext {
        check(Build.VERSION.SDK_INT>=30) {"native_tls_api_not_qualified"}
        require(certificate.length<=8192 && privateKey.length<=8192)
        val cert=CertificateFactory.getInstance("X.509").generateCertificate(certificate.byteInputStream()) as X509Certificate
        require(cert.publicKey.algorithm=="EC" && cert.basicConstraints<0)
        require(cert.extendedKeyUsage?.contains("1.3.6.1.5.5.7.3.1")==true)
        require(cert.keyUsage?.getOrNull(0)==true)
        cert.checkValidity()
        cert.verify(cert.publicKey)
        require(privateKey.startsWith("-----BEGIN PRIVATE KEY-----\n") && privateKey.endsWith("-----END PRIVATE KEY-----\n"))
        val encoded=Base64.decode(privateKey.removePrefix("-----BEGIN PRIVATE KEY-----\n")
            .removeSuffix("-----END PRIVATE KEY-----\n"),Base64.DEFAULT)
        val key=try {KeyFactory.getInstance("EC").generatePrivate(PKCS8EncodedKeySpec(encoded))}finally{encoded.fill(0)}
        // Standard signature proof detects a valid but DIFFERENT private key.
        val nonce=ByteArray(32).apply {SecureRandom().nextBytes(this)}
        val signed=Signature.getInstance("SHA256withECDSA").run {initSign(key);update(nonce);sign()}
        require(Signature.getInstance("SHA256withECDSA").run {initVerify(cert.publicKey);update(nonce);verify(signed)})
        val password=Base64.encodeToString(ByteArray(32).apply {SecureRandom().nextBytes(this)},Base64.NO_WRAP).toCharArray()
        try {
            val store=KeyStore.getInstance("PKCS12").apply {load(null,password);setKeyEntry("node",key,password,arrayOf(cert))}
            val managers=KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm()).apply {init(store,password)}
            return SSLContext.getInstance("TLS").apply {init(managers.keyManagers,null,SecureRandom())}
        } finally {password.fill('\u0000')}
    }
}
