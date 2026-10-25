package org.asc.foundation
import android.content.Context
import org.json.JSONObject

/** Capability probe seam, NOT object storage, Catalog, SAF->POSIX mapping or Node approval. */
interface StorageFoundation {
    fun status():JSONObject
    fun approve(quota:Long,reserve:Long):JSONObject
    fun probe():JSONObject
}
class PrivateProbeStorage(context:Context,private val vault:ApplicationVault):StorageFoundation {
    private val engine=EmbeddedEngine(context)
    override fun status()=engine.volumeStatus(vault.requireIdentity())
    override fun approve(quota:Long,reserve:Long)=engine.approveProbe(vault.requireIdentity(),quota,reserve)
    override fun probe()=engine.probe(vault.requireIdentity())
}
class UnqualifiedSafStorage:StorageFoundation {
    override fun status()=JSONObject().put("state","NOT SUPPORTED").put("provider","SAF_UNQUALIFIED")
        .put("writable",JSONObject.NULL).put("fsync_tested",JSONObject.NULL).put("identity",JSONObject.NULL)
    override fun approve(quota:Long,reserve:Long):JSONObject {throw UnsupportedOperationException("saf_provider_unqualified")}
    override fun probe()=status()
}
