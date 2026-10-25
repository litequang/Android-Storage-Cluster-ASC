# ASC Demo Alpha 0.4.0 — DEMO.4 acceptance

Status: **NOT YET QUALIFIED**. DEMO.4a/4b targeted gates pass; DEMO.4c fresh full
qualification and public artifact verification remain pending. Linux synthetic only;
Android/real-phone browser CA import/SD/Doze/power-cut/production NOT TESTED.

Branch feature/android-demo-alpha, Core base acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c.
Start 2d19eb06cee1b6bede0fbafac9d4704704c039a9; Core untouched.

| Checkpoint / gate | Actual evidence |
|---|---|
| DEMO.4a backend | 5db17aef375b5ebfd03ce680a3b0a52c3a993f99, pushed/remote verified; 35 targeted PASS, 136.486s |
| DEMO.4b frontend | 8e4661bbccc9c6b11e451e414907d190a55a799c, pushed/remote verified; 21 targeted PASS, 105.743s incl real Chromium |
| Exact published 0.3.0 -> 0.4.0 -> old0.3 code/new state | PASS, 1 test14.810s; final combined22 targeted PASS0skip119.508s |
| Fresh full Python 230 cases | PENDING |
| Fresh Go/vet/modules/builds | PENDING |
| Final public package / install / SHA / secret audit | PENDING |
| Android runtime / PC and Android manual trust UX | NOT TESTED; owner pilot only |

Backend reuses the sole Demo Controller/Catalog and unchanged pinned transfer
client. Separate explicit IP-SAN trusted HTTPS, one-use owner code and RAM sessions,
Secure/HttpOnly/SameSite cookie, CSRF/Host/Origin/rate/body/worker/transfer limits.
Browser never receives Core admin/node token or private key. Node approval/domain
changes remain CLI. Dynamic content text-only, no external assets or offline write.
Unknown measurements remain UNKNOWN, protection requires two available verified
independent physical domains. No delete/GC/reduction/Raft/failover/public Internet.

Actual Chromium uses an isolated synthetic NSS HOME, public CA import only and
normal certificate verification; a separate untrusted profile fails TLS. UI upload,
physical bodies/two domains, browser saved-download SHA after real first node stop,
unsafe new upload refusal, literal HTML filename/XSS denial, 390px mobile viewport,
network disconnect UNKNOWN/actions disabled, reconnect and logout all pass.
No fake API success, skipped browser gate or TLS/certificate-error bypass.

Exact published0.3 fixture SHA remains
3bf81c5d94891fa064e2f05f99d60d620b4c5db71c87bb2ee6c89ac72b9a445a.
Old installed launcher creates/populates original cluster, stages/activates0.4;
new trusted Dashboard reads old bytes, new code writes another file, NEW complete
backup then code-only rollback runs exact old code over actual new state. IDs/keys/
certs/pins/Cluster ID/schema/old+new bytes preserved; optional Dashboard CA keys are
preserved and backed up. Base state formats unchanged; no DB restore/migration.

Owner usage/CA trust/update/rollback: DEMO-QUICKSTART.md sections 5a/6/6a.
Android checklist stays blank in DEMO-ANDROID-PILOT.md. Historical0.3 evidence remains
in DEMO-TRACK-ACCEPTANCE.md, never reused as current0.4 full regression evidence.
