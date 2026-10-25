# Phase4.0 acceptance

**NOT ACCEPTED — final fresh full Python/fault regression pending.**
Branch feature/phase4-core-demo-integration from Core3D ca2504f; Demo reference
c9c2660, selective reviewed port only. No whole branch merge or state adoption.
Architecture/compatibility matrix and future app plan: PHASE4-PLAN. Checkpoint
receipts/test details and candidate SHA: PHASE4-PROGRESS. Operator: PHASE4-QUICK-JOIN.

Actual targeted:4a16PASS; b.1 95PASS; backend31PASS; UI17PASS; c.1 installer/upgrade/
browser13PASS plus persisted exact-candidate upgrade1PASS. All0skip0fail. Historical
full results are NOT reused for integration acceptance. Fresh Go11/vet/modules/
Linux build/Windows+Android cross-build PASS. Candidate0.4.2-dev has unchanged
formats, exact04.1 old-launcher upgrade/new-state code-only rollback and pending
resume in both directions; no old database restore. Candidate SHA
b7904a82c55e41866b374ecb42b873a6796a4f8e5e53a213f648e026467a64a3.
Source-only106files,196386bytes; NOT a GitHub Release or public Android release.

Final gate: frozen source/tests/packaged guides +287 unique full Python cases,
original Core physical/network/replay/recovery faults intact, exact candidate
hash/source, tracked/index/unpacked security audit, remote source/branch checks.
No completion claim before actual PASS. Source freeze receipt follows c.1 push.

Intended qualified scope: Linux synthetic Demo single-writer owner Quick Join
Dashboard/local guided enrollment reusing existing Core; preserve Core3A–3D.
Android/Windows runtime, real media/power interruption/CA user experience NOT TESTED.
Core quorum UI/APK/Keystore/SAF/Termux migration and single-writer-to-Raft deferred.
Writable DR remains NOT ACCEPTED/BLOCKED: no new authority/quorum/fencing/epoch,
no Demo runtime on passive recovery staging. No phones/M51/production access,
physical GC/failover/Raft unlock or automatic storage/domain approval.
