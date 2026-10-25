package org.asc.foundation
import java.net.URI
import java.util.UUID

object RequestPolicy {
    val operations = setOf("status", "volumes", "quick_join", "resume_join", "node_start", "stop_owned", "app_provision", "probe_private_volume", "save_join_draft", "draft_status")
    fun caller(uid: Int, ownUid: Int, signatureMatches: Boolean) {
        if (uid != ownUid || !signatureMatches) throw SecurityException("caller_denied")
    }
    fun validate(version: Int, id: String, op: String, endpoint: String, pin: String,
                 cluster: String, name: String, code: String, trusted: Boolean) {
        Contract.version(version)
        require(UUID.fromString(id).toString() == id) { "invalid_request_id" }
        require(op in operations) { "unsupported_operation" }
        require(listOf(id,op,endpoint,pin,cluster,name,code).sumOf { it.toByteArray().size } <= 8192) { "request_limit" }
        if (op !in setOf("quick_join","save_join_draft")) {
            require(listOf(endpoint,pin,cluster,name,code).all { it.isEmpty() } && !trusted) { "unexpected_fields" }
            return
        }
        val uri = URI(endpoint)
        require(uri.scheme == "https" && uri.rawUserInfo == null && uri.rawQuery == null && uri.rawFragment == null &&
            uri.rawPath.isNullOrEmpty() && uri.port in 1024..65535) { "invalid_endpoint" }
        val components = (uri.host ?: "").split('.')
        require(components.size == 4 && components.all { it.toIntOrNull() in 0..255 && (it == "0" || !it.startsWith('0')) }) { "private_ipv4_required" }
        val octets=components.map { it.toInt() }
        require(octets[0]==10 || octets[0]==127 || octets[0]==192 && octets[1]==168 || octets[0]==172 && octets[1] in 16..31) { "private_ipv4_required" }
        require(pin.matches(Regex("[a-f0-9]{64}"))) { "invalid_pin" }
        require(UUID.fromString(cluster).toString()==cluster) { "invalid_cluster" }
        require(name.length in 1..64 && name.trim()==name && name.none { Character.isISOControl(it) || Character.getType(it)==Character.FORMAT.toInt() }) { "invalid_name" }
        require(code.matches(Regex("[a-fA-F0-9]{12}")) && trusted) { "trust_or_code_required" }
    }
}
