# Local Engine Bridge API v1

Status:4.1b.1 implements provisioning/private IPC/status/Quick Join; lifecycle still
operation_not_supported until4.1b.2. Qualification: PHASE4-1-PROGRESS.
Linux synthetic same-UID native client only, not a browser HTTP API or APK bridge.
No cross-UID Termux access is claimed. No second Catalog/Storage/enrollment engine.

## Process and authorization

Operator explicitly provisions a NEW private control root outside existing state,
volumes and source, bound to one already initialized marked Demo state and one
application UUID. It contains independent local-app authorization and bounded retry
journal; node/cluster identity remains in existing state. Provisioning never init/
adopts an engine. Missing/incompatible/recovery state refuses before operations.

Server owns one filesystem Unix stream socket inside0700 operator-owned directory,
socket0600; Linux SO_PEERCRED must match current owning UID, plus distinct random
application bearer and explicit scopes read/join/lifecycle. Credential is returned
ONLY by explicit operator provisioning, retained privately0600/native secure storage,
never a browser value/log/URL/argv/environment. Same UID is not sufficient by itself.
Default scope read. Other apps/UIDs, TCP/CORS/HTTP/WebSocket clients have no route.
Future APK cannot read Termux control directory just because it is on the phone.

At most8 handlers, one newline JSON frame<=8192bytes, fixed deadlines, no duplicate
JSON keys/nonfinite/type aliases/unknown fields. Reply is bounded and sanitized.
No caller-selected path/PID/shell/env/source/runtime mode. Existing source verified
on installed-prefix use; device/M51/unknown and existing engine locks remain.

## Envelope

Exactly `{api_version:1,request_id:UUID,app_id:UUID,authorization:secret,
operation:string,params:object}`. Authorization is LOCAL APP only, never node/admin.
Response `{api_version:1,request_id,ok,result|error,replayed}`; fixed error labels,
no arbitrary exceptions/input echoed. Response success is not storage/write proof.

| operation | scope | params / semantics |
|---|---|---|
| status | read | empty; fresh runtime lock observations, identity presence/IDs, controller confirmation, approved volume metrics; null/UNKNOWN stays unknown |
| quick_join | join | controller HTTPS private origin, full pin, cluster_id, name; optional code and replace_code boolean; uses existing Quick Join subprocess/secret stdin |
| node_start | lifecycle | empty; initialized Demo node ONLY, existing storage configuration and guards; start only fixed owned child; no Controller/Core/Raft start |
| node_stop | lifecycle | empty; stop only this bridge's own child handle; never guessed PID or external foreground |

Quick Join code is a one-use enrollment grant, not local-app authorization. It
travels only authenticated UDS then private stdin to existing worker. Pending
operation/token persists in existing engine format. After interruption retry SAME
request ID and same intent; explicit replacement code uses NEW bridge request ID
but existing engine enrollment operation with replace_code=true. No auto-repair,
identity regeneration, volume init or storage/domain approval. Registered node
remains pending explicit owner storage/domain approval; observations may be UNKNOWN.

## Retry / lifecycle contract

Read retries sample fresh state, not cached authority. Mutating requests persist
private FULL journal RECEIVED before dispatch, DONE with sanitized historical result
after completion.<=256 permanent request records; exhausted journal refuses rather
than evicting retry identity. Same ID/different app/public binding or supplied code hash conflicts. A retry may
omit the original code: existing pending context/receipt is reused; if the first
worker never saved context, join_code_required asks for the original code. Same receipt
is historical and tagged replayed, not current process/write authority. Interrupted
join repeats existing engine operation; a saved identity is not silently replaced.
No raw code/bearer/token is stored in bridge receipt; Core pending remains sensitive.

Controlled lifecycle is optional Linux implementation, not Android acceptance.
Bridge retains only actual Popen handles. Linux parent-death signal set in a fixed
child launcher (no threaded preexec hook); parent identity checked before exec.
Bridge exit/crash terminates its own node; core locks/journals retain state.
Failure to support this fence refuses start. Stop/timeout never kills a foreign
PID. Node process alive !=writable, fsync success, Controller reachability or replica
protection. External foreground remains independently owned and cannot be stopped.
No background auto-start/update/Termux:Boot/system service is installed.

## Native boundary and rollback

Future Android UI calls a signature-authorized native bound service, not UDS in a
foreign UID. Binder caller UID/signature+user consent maps to these scopes; native
engine owns keys/state and mediates fixed operations. Until implemented/tested,
Termux->APK and cross-UID access are BLOCKED. See ANDROID-APP-CONTRACT and threat
model. Bridge/controller owner browser session/node bearer are separate actors.
Stop bridge+node and make NEW verified backups before compatible code rollback;
retain control journal/auth separately, never restore old DB over new bytes.

## Implemented source entry points (4.1b.1)

`python -B -m asc.bridge.cli --control <NEW-private-control> provision --state
<already-initialized-Demo-root> --allow-join` creates local-app authorization only.
`--allow-lifecycle` reserves a scope; lifecycle is still unsupported in b.1.
Run with the same private HOME/device environment, then `... --control <control>
run`. Native Python client: `asc.bridge.service.call(control,'status')` or
`call(control,'quick_join',params,request_id)`. Standalone CLI quick-join requires
public controller/pin/cluster-id/name/request-id flags and hidden code input;
`--resume` omits code for same binding/ID, `--new-code` needs a NEW request ID.
No plaintext secret argument/environment or browser endpoint exists.

Control format1 bridge.json binds installation UUID AND original state directory
device/inode, app ID/hash/scopes and optional installed prefix. client.json holds
only private local-app authorization, never a node token. requests.sqlite3 schema1
stores request ID/app/public intent hash/code hash/RECEIVED or DONE/sanitized result.
No raw code/app/node/admin credential in the journal. Engine pending file still
contains private enrollment material under existing unchanged format.<=256 records.
Reads are fresh, mutation receipt replay is tagged historical_receipt=true.

b.1 graceful exit removes only its own exact socket inode; a foreign or stale
socket is refused/preserved. Crash socket recovery and owned Node lifecycle are
next b.2 gates, not claimed here. Root replacement/recovery/missing state/M51/
unknown/malformed/foreign socket/app scope/secret response boundaries tested.
Local status reads existing manifest/approved adapter and actual free space,
never constructs a second Engine or probes writable/fsync. Those values remain
null; ONLINE controller is pinned-info reachability only, writer_authority=false.
