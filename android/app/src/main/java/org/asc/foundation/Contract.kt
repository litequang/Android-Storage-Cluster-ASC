package org.asc.foundation

/** Application IPC, never a node/cluster identity or writer capability. */
object Contract {
    const val VERSION = 1
    const val FOUNDATION = "FOUNDATION"
    const val UNKNOWN = "UNKNOWN"
    fun version(value: Int) { require(value == VERSION) { "unsupported_version" } }
    fun measured(value: Long?): String = value?.toString() ?: UNKNOWN
}
