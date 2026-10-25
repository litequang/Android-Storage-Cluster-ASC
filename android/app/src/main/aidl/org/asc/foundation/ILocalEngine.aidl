package org.asc.foundation;
// No paths, PID, shell, arbitrary Intent/Bundle or credentials returned to clients.
interface ILocalEngine {
    String approvePrivateProbe(int version, String requestId, long quotaBytes, long reserveBytes) = 0;
    String request(int version, String requestId, String operation,
        String controller, String pin, String clusterId, String name,
        String code, boolean trustConfirmed) = 1;
}
