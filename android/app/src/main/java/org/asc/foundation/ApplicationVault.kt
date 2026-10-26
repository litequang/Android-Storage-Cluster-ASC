package org.asc.foundation

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.AtomicFile
import android.util.Base64
import org.json.JSONObject
import java.io.File
import java.security.KeyStore
import java.security.MessageDigest
import java.util.UUID
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class IdentityLocked : IllegalStateException("identity_locked")

/** App identity only. Never creates/imports Core node keys, IDs or credentials. */
class ApplicationVault(context:Context, namespace:String="identity-v1") {
    init {require(namespace.matches(Regex("[a-zA-Z0-9-]{1,80}")))}
    internal val root=File(context.filesDir.canonicalFile,namespace)
    internal val alias="asc.application.aes.v1."+MessageDigest.getInstance("SHA-256").digest(namespace.toByteArray()).joinToString(""){"%02x".format(it)}.take(24)
    private val store=KeyStore.getInstance("AndroidKeyStore").apply {load(null)}
    private fun read(name:String):JSONObject {
        val f=File(root,name)
        val limit=if(name=="node-context.json")98304 else 32768
        if(root.canonicalFile!=root.absoluteFile || f.canonicalFile!=f.absoluteFile || !f.isFile || f.length()>limit)throw IdentityLocked()
        return try {JSONObject(f.readText())} catch(_:Exception){throw IdentityLocked()}
    }
    private fun write(name:String,data:JSONObject) {
        if(root.canonicalFile!=root.absoluteFile)throw IdentityLocked()
        for(suffix in listOf("",".new",".bak")) {
            val f=File(root,name+suffix)
            if(java.nio.file.Files.isSymbolicLink(f.toPath()))throw IdentityLocked()
        }
        val atomic=AtomicFile(File(root,name));val stream=atomic.startWrite()
        try {stream.write(data.toString().toByteArray());stream.fd.sync();atomic.finishWrite(stream)}
        catch(e:Exception){atomic.failWrite(stream);throw IdentityLocked()}
    }
    private fun metadata():JSONObject {
        val m=read("application.json")
        if(m.keys().asSequence().toSet()!=setOf("format","app_id","key_version") || m.get("format")!=1 || m.get("key_version")!=1)throw IdentityLocked()
        try {if(UUID.fromString(m.getString("app_id")).toString()!=m.getString("app_id"))throw IdentityLocked()}
        catch(_:Exception){throw IdentityLocked()}
        return m
    }
    private fun key():SecretKey=try {store.getKey(alias,null) as? SecretKey ?: throw IdentityLocked()}catch(_:Exception){throw IdentityLocked()}
    private fun encrypt(id:String,purpose:String,plain:String):JSONObject {
        val c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,key());c.updateAAD("asc-native:1:$id:$purpose".toByteArray())
        return JSONObject().put("format",1).put("iv",Base64.encodeToString(c.iv,Base64.NO_WRAP))
            .put("ciphertext",Base64.encodeToString(c.doFinal(plain.toByteArray()),Base64.NO_WRAP))
    }
    private fun decrypt(id:String,purpose:String,encrypted:JSONObject):String = try {
        if(encrypted.keys().asSequence().toSet()!=setOf("format","iv","ciphertext") || encrypted.get("format")!=1)throw IdentityLocked()
        val iv=Base64.decode(encrypted.getString("iv"),Base64.NO_WRAP);if(iv.size!=12)throw IdentityLocked()
        val c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,key(),GCMParameterSpec(128,iv))
        c.updateAAD("asc-native:1:$id:$purpose".toByteArray());String(c.doFinal(Base64.decode(encrypted.getString("ciphertext"),Base64.NO_WRAP)))
    } catch(_:Exception){throw IdentityLocked()}
    @Synchronized fun requireIdentity():String {
        val id=metadata().getString("app_id")
        if(decrypt(id,"canary",read("canary.json"))!="application:$id")throw IdentityLocked()
        return id
    }
    @Synchronized fun provision():JSONObject {
        if(root.exists())return JSONObject().put("app_id",requireIdentity()).put("state","READY")
        if(store.containsAlias(alias))throw IdentityLocked()
        if(!root.mkdir())throw IdentityLocked()
        val generator=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore")
        generator.init(KeyGenParameterSpec.Builder(alias,KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
            .setKeySize(256).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setRandomizedEncryptionRequired(true).build())
        generator.generateKey()
        val id=UUID.randomUUID().toString()
        write("application.json",JSONObject().put("format",1).put("app_id",id).put("key_version",1))
        write("canary.json",encrypt(id,"canary","application:$id"))
        return JSONObject().put("app_id",requireIdentity()).put("state","READY")
    }
    fun state():JSONObject = try {
        if(!root.exists())JSONObject().put("state",if(store.containsAlias(alias))"IDENTITY_LOCKED" else "NOT_PROVISIONED")
        else JSONObject().put("state","READY").put("app_id",requireIdentity()).put("key_version",1).put("key_exportable",key().encoded!=null)
    } catch(_:Exception){JSONObject().put("state","IDENTITY_LOCKED")}
    @Synchronized fun saveDraft(id:String,endpoint:String,pin:String,cluster:String,name:String,code:String):JSONObject {
        RequestPolicy.validate(1,id,"quick_join",endpoint,pin,cluster,name,code,true)
        val app=requireIdentity()
        val draft=JSONObject().put("request_id",id).put("controller",endpoint).put("pin",pin).put("cluster_id",cluster)
            .put("name",name).put("code",code).put("state","DRAFT_NOT_SENT")
        if(File(root,"join-draft.json").exists()) {
            val old=JSONObject(decrypt(app,"join-draft",read("join-draft.json")))
            if(old.toString()!=draft.toString())throw IllegalArgumentException("draft_conflict")
        } else write("join-draft.json",encrypt(app,"join-draft",draft.toString()))
        return draftSummary()
    }
    fun draftSummary():JSONObject {
        val app=requireIdentity()
        if(!File(root,"join-draft.json").exists())return JSONObject().put("state","NO_DRAFT").put("network_enrolled",false)
        val draft=JSONObject(decrypt(app,"join-draft",read("join-draft.json")))
        if(draft.keys().asSequence().toSet()!=setOf("request_id","controller","pin","cluster_id","name","code","state") || draft.getString("state")!="DRAFT_NOT_SENT")throw IdentityLocked()
        RequestPolicy.validate(1,draft.getString("request_id"),"quick_join",draft.getString("controller"),draft.getString("pin"),draft.getString("cluster_id"),draft.getString("name"),draft.getString("code"),true)
        draft.remove("code");return draft.put("network_enrolled",false).put("native_enrollment_supported",false)
    }

    // Trusted in-process provider ONLY, never exposed as a generic Binder
    // read/write operation. One fixed authenticated record, independent of the
    // unsent form. The witness detects record deletion; partial writes are held.
    internal fun loadNodeContext():String? = synchronized(ApplicationVault::class.java) {
        val app=requireIdentity()
        val record=File(root,"node-context.json");val witness=File(root,"node-context-required.json")
        if(!record.exists() && !witness.exists())return@synchronized null
        val binding=read("node-context-required.json")
        if(binding.keys().asSequence().toSet()!=setOf("format","app_id") ||
            binding.get("format")!=1 || binding.getString("app_id")!=app)throw IdentityLocked()
        decrypt(app,"node-context",read("node-context.json"))
    }
    internal fun compareNodeContext(expected:String?,replacement:String) = synchronized(ApplicationVault::class.java) {
        val app=requireIdentity()
        if(replacement.toByteArray().size>65536 || loadNodeContext()!=expected)throw IdentityLocked()
        val value=try {JSONObject(replacement)} catch(_:Exception){throw IdentityLocked()}
        if(value.get("format")!=1 || value.getString("app_id")!=app)throw IdentityLocked()
        if(expected==null)write("node-context-required.json",JSONObject().put("format",1).put("app_id",app))
        write("node-context.json",encrypt(app,"node-context",replacement))
        if(loadNodeContext()!=replacement)throw IdentityLocked()
    }
}
