# ASC Phase4 internal candidate — 2026-10-27

NOT a production release or physical-phone acceptance. Native APK versionCode4,
org.asc.foundation, min26/target35; Native Node TLS requires30+, API30 and retained API35 x86_64
runtime tested. ARM64 packaged, not runtime tested. Full4.2 remains NOT ACCEPTED
until remaining platform and owner device gates are closed.

Artifacts are stored as immutable files on feature/phase4-2-android-native because
GitHub Release upload returned401. No token/proxy/CA change or private signer upload.

- android-artifacts/asc-native-node-0.4.0-internal-debug.apk
- candidates/asc-demo-alpha-0.4.3-native-node-internal-source.tar.gz
- Each has an adjacent .sha256; use sha256sum -c on the downloaded file.

APK SHA256:7c4ba6496e89ac673026345f7abf1ea1bc4424f5ff93747630dbd072cbdc91e8.
Public signing certificate SHA256:bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30.
Controller source archive SHA256:9dbd9007058a6a43f075c1924f4014faa7060ef6667e014bbc28a91be070ad59.
Source version0.4.3-dev/releaseIDe69ebeae3e5ab9a5372465caa8ed5e1882f352fd5f355157299091361f4c6706;
byte-equal actual Native Catalog E2E Controller package, not a new stable Demo release.
Old published archives/Foundation APK remain unchanged.

Read ANDROID-NATIVE-PILOT.md and ANDROID-NATIVE-OPERATIONS.md before owner tests.
APK is a Storage Node, not Controller. Keep Termux state separate; no migration.
Owner verifies Controller HTTPS/pin/Cluster, issues one-use code, approves storage
and truthful physical domain. Use another unused port if Termux already uses9443.
Termux+APK on the same phone are ONE domain. Browser File Manager requires the
verified public Dashboard CA and separate Demo owner login; Core observer read-only.
No native file picker/multiuser accounts/automatic hotspot/Cloudflare access.

Exact direct retained Native3->4 upgrade PASS; Foundation2->4 NOT TESTED. Keep keys,
IDs/data on upgrade, no uninstall/clear/-d. Rollback uses a compatible future-version
fix, never stale database restore. Private debug signer must remain in owner custody.

383Python0skip/64fault banners, Go11/vet/modules/builds, actual Android26+foreign1
are recorded in qualification/phase4-2j3-final.json. Runtime code unchanged since
that gate; only artifact/ignore/document publication metadata changes here. API30 fresh enrollment and subsequent retained full flow after SDK network correction
are qualified separately in phase4-api30-node.json; API35 cold is still BLOCKED. Phones/real LAN/
ChromeAndroid/OEM/Doze/two physical domains and writableDR remain unqualified.
