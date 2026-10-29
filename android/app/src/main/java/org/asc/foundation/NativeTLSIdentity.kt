package org.asc.foundation

import android.util.Base64
import org.bouncycastle.asn1.x500.X500Name
import org.bouncycastle.asn1.x509.BasicConstraints
import org.bouncycastle.asn1.x509.ExtendedKeyUsage
import org.bouncycastle.asn1.x509.Extension
import org.bouncycastle.asn1.x509.KeyPurposeId
import org.bouncycastle.asn1.x509.KeyUsage
import org.bouncycastle.cert.jcajce.JcaX509CertificateConverter
import org.bouncycastle.cert.jcajce.JcaX509v3CertificateBuilder
import org.bouncycastle.jce.provider.BouncyCastleProvider
import org.bouncycastle.operator.jcajce.JcaContentSignerBuilder
import org.json.JSONObject
import java.math.BigInteger
import java.security.KeyPairGenerator
import java.security.MessageDigest
import java.security.SecureRandom
import java.security.spec.ECGenParameterSpec
import java.util.Date

/** Standard X.509/EC library, private in-process provider, NEVER an IPC method.
 * Software TLS key is AES-GCM sealed by ApplicationVault; no hardware TLS-key
 * claim, OS provider registration, external OpenSSL, disk PEM or Termux import.
 */
class NativeTLSIdentity {
    fun generate():String {
        val provider=BouncyCastleProvider();val random=SecureRandom()
        val keys=KeyPairGenerator.getInstance("EC",provider).apply {
            initialize(ECGenParameterSpec("secp256r1"),random)
        }.generateKeyPair()
        val subject=X500Name("CN=ASC Native Storage")
        val now=System.currentTimeMillis()
        val builder=JcaX509v3CertificateBuilder(subject,BigInteger(159,random).setBit(158),
            Date(now-300000),Date(now+365L*86400000),subject,keys.public)
        builder.addExtension(Extension.basicConstraints,true,BasicConstraints(false))
        builder.addExtension(Extension.keyUsage,true,KeyUsage(KeyUsage.digitalSignature))
        builder.addExtension(Extension.extendedKeyUsage,false,ExtendedKeyUsage(KeyPurposeId.id_kp_serverAuth))
        val signer=JcaContentSignerBuilder("SHA256withECDSA").setProvider(provider).build(keys.private)
        val cert=JcaX509CertificateConverter().setProvider(provider).getCertificate(builder.build(signer))
        cert.verify(keys.public,provider)
        fun pem(label:String,bytes:ByteArray):String {
            val body=Base64.encodeToString(bytes,Base64.NO_WRAP).chunked(64).joinToString("\n")
            return "-----BEGIN $label-----\n$body\n-----END $label-----\n"
        }
        return JSONObject().put("format",1).put("certificate",pem("CERTIFICATE",cert.encoded))
            .put("private_key",pem("PRIVATE KEY",keys.private.encoded))
            .put("pin",MessageDigest.getInstance("SHA-256").digest(cert.encoded).joinToString(""){"%02x".format(it)}).toString()
    }
}
