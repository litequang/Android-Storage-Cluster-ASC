'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const model = { mode: null, readOnly: true, csrf: null, connected: false, state: null, max: null, uploading: false, activeTicket: null, polling: false, pending: null };
  const pairing = { generation: 0, ticket: null, timer: null, creating: false, polling: false };
  const messages = {
    pairing_limit: 'Đã đạt giới hạn mã đang theo dõi (8/phiên, 32/Controller). Đợi hoặc kiểm tra các mã đã tạo.',
    pairing_not_found: 'Không còn bằng chứng theo dõi trong phiên này. Không suy ra mã đã bị thu hồi.',
    unsupported_runtime: 'Quick Join chỉ hỗ trợ Demo single-writer đã xác minh.',
    read_only_mode: 'Chế độ Core chỉ quan sát; thao tác thay đổi bị từ chối phía server.',
    login_rejected: 'Mã không hợp lệ, đã dùng hoặc đã hết hạn. Lấy mã mới từ Controller.',
    login_required: 'Phiên đã hết hạn. Đăng nhập lại bằng mã một lần.',
    insufficient_capacity: 'Không đủ dung lượng hoặc chưa có hai điện thoại độc lập đủ điều kiện. Chưa xác nhận upload.',
    insufficient_spool_space: 'Controller chưa đủ chỗ tạm để xử lý file. Giữ file gốc và thử lại sau.',
    upload_too_large: 'File vượt giới hạn của Dashboard. Hãy dùng CLI cho file lớn hơn.',
    browser_download_too_large: 'File vượt giới hạn tải bằng Dashboard. Hãy dùng CLI.',
    checksum_mismatch: 'SHA-256 không khớp. Chưa xác nhận file; giữ file gốc để kiểm tra.',
    file_exists: 'Tên và phiên bản này đã tồn tại. Chọn tên mới; Dashboard không ghi đè file.',
    idempotency_conflict: 'Lần thử lại không khớp nội dung ban đầu. Không tạo upload mới cho cùng tên.',
    transfer_busy: 'Đang có một tác vụ truyền file. Đợi tác vụ đó xong rồi thử lại.',
    transfer_limit: 'Đã đạt giới hạn tác vụ đang chờ. Đợi hoặc đăng nhập lại để kiểm tra file.',
    transfer_not_found: 'Tác vụ đã hết hạn hoặc phiên đã đổi. Chọn lại cùng file để tiếp tục an toàn.',
    origin_rejected: 'Nguồn yêu cầu không hợp lệ. Mở đúng URL HTTPS của Dashboard.',
    csrf_required: 'Phiên chưa xác minh yêu cầu. Tải lại trang hoặc đăng nhập lại.',
    core_unavailable: 'Dịch vụ chưa sẵn sàng. Chưa xác nhận thao tác thành công; kiểm tra Controller và node.',
    replica_unavailable: 'Chưa có bản sao đọc được đã xác minh. Không xóa hoặc thay thế dữ liệu cũ.',
    not_found: 'Không tìm thấy mục đã yêu cầu.',
    upload_timeout: 'Upload quá thời gian. Giữ cùng file và thử lại; chưa xác nhận thành công.',
    upload_incomplete: 'Chưa nhận đủ file. Giữ cùng file để thử lại.',
    metadata_too_large: 'Yêu cầu vượt giới hạn cho phép.',
    bad_request: 'Yêu cầu không hợp lệ. Kiểm tra tên file hoặc tải lại trang.',
  };
  class APIError extends Error {
    constructor(code, status) { super(messages[code] || 'Yêu cầu chưa được xác nhận. Kiểm tra kết nối và thử lại.'); this.code = code; this.status = status; }
  }
  const node = (tag, className, text) => {
    const value = document.createElement(tag);
    if (className) value.className = className;
    if (text !== undefined) value.textContent = text;
    return value;
  };
  const button = (text, callback, cls = 'subtle') => {
    const value = node('button', 'button ' + cls, text);
    value.type = 'button'; value.addEventListener('click', callback); return value;
  };
  const amount = value => {
    if (value === null || value === undefined || !Number.isFinite(value)) return 'UNKNOWN';
    let n = value, index = 0; const units = ['B', 'KiB', 'MiB', 'GiB', 'TiB'];
    while (n >= 1024 && index < units.length - 1) { n /= 1024; index += 1; }
    return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(n) + ' ' + units[index];
  };
  const count = value => value === null || value === undefined ? 'UNKNOWN' : String(value);
  const date = value => value === null || value === undefined || !Number.isFinite(value) ? 'UNKNOWN' : new Date(value * 1000).toLocaleString('vi-VN');
  const short = value => value ? value.slice(0, 8) : 'UNKNOWN';
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  function notice(text) { $('notice').textContent = text; $('notice').hidden = !text; }
  function connection(ok) {
    model.connected = ok;
    if (!ok) clearPairing('Mất kết nối: mã đã ẩn, đăng ký và quyền lưu trữ UNKNOWN.');
    pairingButton();
    if (!ok && $('details').open) $('details').close();
    $('connection').textContent = model.readOnly ? (ok ? 'Gateway online' : 'Gateway UNKNOWN') : ok ? 'Controller online' : 'Controller UNKNOWN';
    $('connection').className = 'badge ' + (ok ? 'good' : 'unknown');
    $('upload-button').disabled = !ok || model.uploading;
    if (model.state) render(model.state);
  }
  function loginView(clear = true) {
    model.csrf = null; model.connected = false; model.state = null;
    clearPairing('Đăng nhập lại để tạo mã ghép. Mã cũ chưa dùng có thể vẫn còn hiệu lực.');
    $('application').hidden = true; $('login-panel').hidden = false; $('logout').hidden = true;
    $('summary').replaceChildren(); $('node-list').replaceChildren(); $('file-list').replaceChildren();
    if ($('details').open) $('details').close();
    if (clear) { $('file-input').value = ''; $('logical-path').value = ''; }
  }
  async function request(path, { method = 'GET', json, body, csrf = true, binary = false, timeout = 180000 } = {}) {
    const headers = {};
    if (csrf && model.csrf) headers['X-ASC-CSRF'] = model.csrf;
    if (json !== undefined) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(json); }
    if (body instanceof File) headers['Content-Type'] = 'application/octet-stream';
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(path, { method, headers, body, credentials: 'same-origin', cache: 'no-store', signal: controller.signal });
      if (!response.ok) {
        let code = 'core_unavailable';
        try { const value = await response.json(); if (typeof value.error === 'string') code = value.error; } catch (_) { /* fixed safe fallback */ }
        if (response.status === 401 && path !== '/api/login') { loginView(); $('login-error').textContent = messages.login_required; }
        if (response.status === 503) { connection(false); notice('Dịch vụ chưa sẵn sàng. Dữ liệu cũ chưa xác minh lại, không xác nhận ghi mới.'); }
        throw new APIError(code, response.status);
      }
      if (binary) return { buffer: await response.arrayBuffer(), sha: response.headers.get('X-ASC-SHA256') };
      return await response.json();
    } catch (error) {
      if (error instanceof APIError) throw error;
      connection(false); notice('Mất kết nối Controller. Dữ liệu dưới đây là bản xem cũ; trạng thái bảo vệ chưa xác minh lại.');
      throw new APIError('core_unavailable', 0);
    } finally { clearTimeout(timer); }
  }
  function pairingButton() {
    $('pair-create').disabled = !model.csrf || !model.connected || model.readOnly || pairing.creating;
  }
  function clearPairing(message = 'Chưa tạo mã ghép.') {
    pairing.generation += 1;
    if (pairing.timer) clearInterval(pairing.timer);
    pairing.timer = null; pairing.ticket = null; pairing.creating = false; pairing.polling = false;
    for (const id of ['pair-code', 'pair-origin', 'pair-pin', 'pair-cluster', 'pair-expiry', 'pair-registration']) $(id).textContent = '';
    $('pair-details').hidden = true; $('pair-status').textContent = message; delete $('pair-status').dataset.state; pairingButton();
  }
  async function pollPairing(generation) {
    if (generation !== pairing.generation || !pairing.ticket || pairing.polling || !model.connected || !model.csrf) return;
    pairing.polling = true;
    try {
      const value = await request('/api/v1/quick-join/pairings/' + encodeURIComponent(pairing.ticket), { timeout: 10000 });
      if (generation !== pairing.generation || !model.csrf || !model.connected) return;
      const states = { waiting: 'Đang chờ node nhập mã.', expired: 'Mã đã hết hạn. Chưa xác nhận đăng ký.',
        registered: 'Node đã đăng ký. Kiểm tra riêng quyền lưu trữ bên dưới.',
        revoked: 'Node đã bị thu hồi quyền. Không xác nhận sẵn sàng lưu trữ.', unknown: 'Trạng thái đăng ký UNKNOWN. Chưa đủ bằng chứng.' };
      $('pair-status').textContent = states[value.state] || states.unknown;
      $('pair-status').dataset.state = value.state in states ? value.state : 'unknown';
      if (value.state !== 'waiting') $('pair-code').textContent = '';
      const approval = value.state === 'registered' ?
        value.storage_approved === true ? 'Đã có phê duyệt lưu trữ từ owner; miền lỗi: ' + (value.failure_domain || 'UNKNOWN') :
        value.storage_approved === false ? 'CHƯA phê duyệt lưu trữ / miền lỗi. Owner phải kiểm tra và approve bằng CLI.' : 'Quyền lưu trữ / miền lỗi UNKNOWN.' : 'Quyền lưu trữ chưa xác minh.';
      $('pair-registration').textContent = (value.node_id ? 'Node ID: ' + value.node_id + '. ' : '') + approval;
    } catch (error) {
      if (generation === pairing.generation) clearPairing(error.message);
    } finally { if (generation === pairing.generation) pairing.polling = false; }
  }
  async function createPairing() {
    if (!model.csrf || !model.connected || model.readOnly || pairing.creating) return;
    clearPairing('Đang yêu cầu mã từ Controller; chưa xác nhận tạo thành công.');
    const generation = pairing.generation;
    pairing.creating = true; pairingButton();
    try {
      const value = await request('/api/v1/quick-join/pairings', { method: 'POST', json: {}, timeout: 10000 });
      if (generation !== pairing.generation || !model.csrf || !model.connected) return;
      if (value.quick_join_version !== 1 || value.runtime !== 'single-writer-demo' || value.storage_auto_approval !== false) throw new APIError('unsupported_runtime', 403);
      pairing.ticket = value.pairing_id;
      $('pair-code').textContent = value.code;
      $('pair-origin').textContent = value.controller; $('pair-pin').textContent = value.pin;
      $('pair-cluster').textContent = value.cluster_id; $('pair-expiry').textContent = date(value.expires_at);
      $('pair-details').hidden = false;
      $('pair-status').textContent = 'Đã tạo mã một lần, tối đa 10 phút. Chưa có node đăng ký.';
      $('pair-status').dataset.state = 'waiting';
      await pollPairing(generation);
      if (generation === pairing.generation) pairing.timer = setInterval(() => { void pollPairing(generation); }, 2000);
    } catch (error) {
      if (generation === pairing.generation) clearPairing(error.message);
    } finally { if (generation === pairing.generation) { pairing.creating = false; pairingButton(); } }
  }
  function applyMode(value) {
    if (!['single-writer-demo', 'core-quorum', 'recovery-read-only'].includes(value.mode) || value.read_only !== (value.mode !== 'single-writer-demo')) throw new APIError('unsupported_runtime', 503);
    model.mode = value.mode; model.readOnly = value.read_only;
    $('runtime-label').textContent = model.readOnly ? 'Core · Quan sát chỉ đọc' : 'Demo Alpha · LAN riêng';
    $('login-method').textContent = model.readOnly ?
      'Dùng mã một lần được operator chủ gateway tạo qua serve --issue-login-code. Xác minh CA/URL trước khi nhập; mã hiệu lực 5 phút.' :
      'Dùng mã một lần từ ascdemo dashboard-code trên Controller. Mỗi mã có hiệu lực 5 phút.';
    $('upload-panel').hidden = model.readOnly;
    document.querySelector('[data-tab="quick-join"]').hidden = model.readOnly;
    $('core-observation').hidden = !model.readOnly;
    $('refresh').textContent = model.readOnly ? 'Đọc trạng thái' : 'Cập nhật kiểm tra';
    pairingButton();
  }
  function renderCore(state) {
    const r = state.runtime;
    $('connection').textContent = model.connected ? r.state : 'Gateway UNKNOWN';
    $('connection').className = 'badge ' + (model.connected && r.state === 'ONLINE' ? 'good' : r.state === 'UNKNOWN' ? 'unknown' : 'warn');
    $('core-status').textContent = r.state + ' · Quorum read: ' + (r.quorum_available === null ? 'UNKNOWN' : r.quorum_available ? 'Đã xác minh barrier tại thời điểm đọc' : 'UNAVAILABLE') +
      ' · Leader đã xác minh: ' + (r.leader_confirmed ? r.leader_id : 'UNKNOWN') + ' · Checkpoint: ' + count(r.checkpoint?.index) + ' · Chỉ đọc, không writer authority';
    $('controller-list').replaceChildren(...(r.controllers || []).map(item => {
      const card = node('article', 'node-card'); card.dataset.controllerId = item.node_id;
      card.append(node('strong', '', item.node_id), node('p', '', 'Controller: ' + item.state),
        node('p', '', 'Voter process: ' + item.voter_process), node('p', '', 'Role hint: ' + (item.role || 'UNKNOWN')),
        node('p', '', 'Leader proof: ' + (item.leader_confirmed ? 'Barrier + term/binding' : 'Chưa xác minh'))); return card;
    }));
    $('core-jobs').replaceChildren(...(state.jobs || []).map(j => node('li', '', j.kind + ' · ' + j.state + ' · ' + short(j.job_id))));
    if (!state.jobs?.length) $('core-jobs').append(node('li', '', r.strong_read_confirmed ? 'Không có job trong quan sát hiện tại.' : 'Jobs UNKNOWN hoặc metadata cũ.'));
    const backup = state.backup, rows = [];
    for (const s of backup.snapshots || []) rows.push(node('li', '', 'Snapshot ' + short(s.snapshot_id) + ': ' + s.state + ' (lịch sử) · xác minh ' + date(s.verified_at)));
    rows.push(node('li', '', 'External backup: ' + backup.external.state + ' · ' + date(backup.external.verified_at)));
    rows.push(node('li', '', 'Recovery: ' + backup.recovery.state + ' · writer authority: false'));
    $('core-backups').replaceChildren(...rows);
  }
  function activate() {
    $('application').hidden = false; $('login-panel').hidden = true; $('logout').hidden = false;
    $('upload-limit').textContent = 'Tối đa ' + amount(model.max) + ' mỗi file trong Dashboard. Chỉ dùng file thử nghiệm bỏ được.';
    $('login-code').value = ''; $('login-error').textContent = '';
  }
  function badge(file) {
    const known = model.connected;
    if (model.readOnly) return node('span', 'badge ' + (!known || file.protected === null ? 'unknown' : file.protected ? 'good' : 'warn'),
      !known || file.protected === null ? 'UNKNOWN · cần xác minh' : file.protected ? 'Đạt policy ' + file.desired_replicas + ' miền lỗi' : 'Chưa đạt policy ' + file.desired_replicas + ' miền lỗi');
    return node('span', 'badge ' + (!known || file.protection === 'unknown' ? 'unknown' : file.protected ? 'good' : 'warn'),
      !known ? 'UNKNOWN · dữ liệu cũ' : file.protected ? 'Đủ hai bản sao' : file.protection === 'unknown' ? 'UNKNOWN · cần xác minh' : 'Chưa đủ hai bản sao');
  }
  function stat(title, value, detail) {
    const card = node('div', 'summary-card'); card.append(node('small', '', title), node('strong', '', value), node('span', '', detail)); return card;
  }
  function detail(label, text) {
    const row = node('div', 'detail-row'); row.append(node('span', '', label), node('strong', '', text)); return row;
  }
  function showDetails(title, values) {
    $('details-title').textContent = title; $('details-body').replaceChildren(...values);
    if (!$('details').open) $('details').showModal();
  }
  function nodeDetails(item) {
    const rows = [detail('Node ID', item.node_id), detail('Phê duyệt', item.storage_approved ? 'Đã duyệt lưu trữ' : 'Chưa duyệt lưu trữ / cần duyệt lại bằng CLI'),
      detail('Miền lỗi do owner xác nhận', item.failure_domain || 'UNKNOWN'), detail('Heartbeat cuối (giờ Controller)', date(item.last_seen)),
      detail('Replica được ghi nhận', count(item.recorded_replicas))];
    for (const volume of item.volumes) {
      const card = node('div', 'replica-card');
      card.append(node('strong', '', volume.kind === 'internal' ? 'Bộ nhớ trong' : volume.kind === 'termux_sd' ? 'microSD (Termux)' : 'Loại bộ nhớ UNKNOWN'),
        node('p', '', 'Volume: ' + volume.volume_id), node('p', '', 'Trạng thái: ' + (model.connected ? volume.state : 'UNKNOWN · dữ liệu cũ')),
        node('p', '', 'Quota: ' + amount(volume.quota) + ' · Đã dùng: ' + amount(volume.used_bytes)),
        node('p', '', 'Free đo được: ' + amount(volume.free_bytes) + ' · Khả dụng: ' + amount(volume.available_bytes)),
        node('p', 'muted', 'Số đo: ' + date(volume.checked_at)));
      rows.push(card);
    }
    if (!item.volumes.length) rows.push(node('p', 'muted', 'Chưa có volume được phê duyệt và đo đạc.'));
    showDetails(item.name, rows);
  }
  async function replicas(fileId) {
    try {
      const file = await request('/api/files/' + encodeURIComponent(fileId));
      const rows = [badge(file), detail('SHA-256', file.sha256), detail('Bản sao / khả dụng', count(file.verified_replicas) + ' / ' + count(file.available_replicas))];
      for (const replica of file.replicas) {
        const card = node('div', 'replica-card'); card.dataset.replicaNode = replica.node_id;
        card.append(node('strong', '', replica.node_name || 'Thiết bị UNKNOWN'), node('p', '', 'Node: ' + replica.node_id),
          node('p', '', 'Volume: ' + replica.volume_id), node('p', '', 'Bằng chứng: ' + replica.state),
          node('p', '', 'Khả dụng: ' + (!model.connected || replica.available === null ? 'UNKNOWN' : replica.available ? 'Có' : 'Chưa xác minh là đọc được')),
          node('p', 'muted', 'Kiểm tra SHA gần nhất: ' + date(replica.verified_at)));
        rows.push(card);
      }
      rows.push(node('p', 'muted', 'Hai volume hoặc hai Node ID trên cùng một điện thoại không được tính là hai miền lỗi độc lập.'));
      showDetails(file.logical_path, rows);
    } catch (error) { notice(error.message); }
  }
  async function sha256(buffer) {
    const hash = await crypto.subtle.digest('SHA-256', buffer);
    return Array.from(new Uint8Array(hash), x => x.toString(16).padStart(2, '0')).join('');
  }
  async function download(file) {
    $('download-status').className = '';
    $('download-status').textContent = 'Đang tải bản sao và đối chiếu SHA-256…';
    try {
      if (!model.connected) throw new APIError('core_unavailable', 0);
      const result = await request('/api/files/' + encodeURIComponent(file.file_id) + '/content', { binary: true });
      if (result.buffer.byteLength !== file.size || result.sha !== file.sha256 || await sha256(result.buffer) !== file.sha256) throw new APIError('checksum_mismatch', 422);
      const url = URL.createObjectURL(new Blob([result.buffer], { type: 'application/octet-stream' }));
      const link = node('a'); link.href = url;
      link.download = (file.logical_path.split('/').pop() || 'ASC-' + file.file_id).replace(/[<>:"\\|?*\u0000-\u001f]/g, '_');
      document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 60000);
      $('download-status').className = 'success'; $('download-status').textContent = 'SHA-256 khớp. Trình duyệt đang lưu bản tải mới; bạn quyết định nơi lưu.';
    } catch (error) { $('download-status').className = 'error'; $('download-status').textContent = error.message; }
  }
  function render(state) {
    model.state = state;
    $('cluster-name').textContent = state.cluster.name;
    $('snapshot-time').textContent = (model.readOnly ? (state.runtime.strong_read_confirmed ? 'Quan sát qua barrier: ' : 'Metadata cũ / chưa xác minh quorum: ') : model.connected ? 'Cập nhật: ' : 'Bản xem cũ: ') + date(state.as_of);
    if (model.readOnly) { renderCore(state); if (!state.runtime.strong_read_confirmed && $('details').open) $('details').close(); }
    const c = state.counts, capacity = state.capacity;
    $('summary').replaceChildren(
      stat('Điện thoại đã ghép', count(c.paired_nodes), 'Không tính identity Controller riêng'),
      stat('Online / offline / chưa rõ', model.connected ? count(c.online) + ' / ' + count(c.offline) + ' / ' + count(c.unknown) : 'UNKNOWN', 'Theo heartbeat và nguồn quan sát'),
      stat('File trong cụm', count(c.files), 'Các phiên bản bất biến'),
      stat(model.readOnly ? 'File đạt replica policy' : 'File đủ hai bản sao', model.connected ? count(c.protected_files) : 'UNKNOWN', model.connected ? count(c.unprotected_files) + ' file cần kiểm tra' : 'Chưa xác minh kết nối'),
      stat('Quota được duyệt', amount(capacity.approved_quota_bytes), 'Không phải tổng dung lượng hãng công bố'),
      stat('Đã sử dụng', amount(capacity.used_bytes), 'Số đo từ volume đã duyệt'),
      stat('Khả dụng theo quota / reserve', model.connected ? amount(capacity.available_bytes) : 'UNKNOWN', 'UNKNOWN nếu volume dùng chung chưa xác minh'),
      stat('Controller', model.readOnly ? state.runtime.state : model.connected ? 'Online' : 'UNKNOWN', model.readOnly ? 'Quan sát read-only, không cấp quyền ghi' : 'Một writer cố định, không tự failover'));
    const warnings = [];
    if (!model.connected) warnings.push('Không liên lạc được Controller: không xác nhận ghi hoặc trạng thái bảo vệ mới.');
    if (c.offline) warnings.push(c.offline + ' node offline theo heartbeat. Giữ nguyên dữ liệu và identity.');
    if (state.nodes.some(n => n.probe_error)) warnings.push('Có volume/node chưa phản hồi phép kiểm tra lưu trữ.');
    if (c.unprotected_files) warnings.push(c.unprotected_files + ' file chưa xác nhận đủ hai bản sao khả dụng.');
    if (capacity.available_bytes === null) warnings.push('Dung lượng khả dụng UNKNOWN; không suy diễn là 0 hoặc đủ chỗ để upload.');
    if (model.readOnly && !state.runtime.strong_read_confirmed) warnings.push('Quorum chưa xác minh: availability/protection UNKNOWN; dữ liệu có thể cũ.');
    if (!warnings.length) warnings.push('Chưa ghi nhận cảnh báo tại thời điểm quan sát; đây không phải cam kết bảo vệ dữ liệu production.');
    $('warnings').replaceChildren(...warnings.map(x => node('li', '', x)));
    $('node-list').replaceChildren(...state.nodes.map(item => {
      const card = node('article', 'node-card'); card.dataset.nodeId = item.node_id;
      const title = node('div', 'card-heading'); title.append(node('h2', '', item.name),
        node('span', 'badge ' + (!model.connected || item.online === 'unknown' ? 'unknown' : item.online === 'online' ? 'good' : 'warn'),
          !model.connected ? 'UNKNOWN' : item.online));
      card.append(title, node('code', '', short(item.node_id)),
        node('p', 'node-facts', (item.storage_approved ? 'Đã duyệt lưu trữ' : 'Chưa duyệt lưu trữ') + ' · ' + item.volumes.length + ' volume · ' + item.recorded_replicas + ' replica ghi nhận'),
        node('p', 'muted', 'Heartbeat: ' + date(item.last_seen)), button('Xem chi tiết', () => nodeDetails(item)));
      return card;
    }));
    if (!state.nodes.length) $('node-list').append(node('p', 'muted', 'Chưa có Storage Node được ghép. Ghép và phê duyệt bằng CLI trước.'));
    $('file-count').textContent = count(c.files) + ' file';
    $('file-list').replaceChildren(...state.files.map(file => {
      const row = node('article', 'file-row'); row.dataset.fileId = file.file_id;
      const info = node('div', 'file-info'); info.append(node('div', 'file-name', file.logical_path), badge(file),
        node('p', 'file-meta', amount(file.size) + ' · v' + file.version + ' · verified ' + file.verified_replicas + ' · available ' + (model.connected ? count(file.available_replicas) : 'UNKNOWN')));
      const actions = node('div', 'file-actions');
      const view = button('Bản sao & SHA', () => replicas(file.file_id)); view.dataset.action = 'replicas';
      const get = button('Tải xuống', () => download(file)); get.dataset.action = 'download'; get.disabled = !model.connected || file.size > model.max;
      actions.append(view); if (!model.readOnly) actions.append(get); row.append(info, actions); return row;
    }));
    if (!state.files.length) $('file-list').append(node('p', 'muted', model.readOnly ? 'Chưa có file trong metadata quan sát.' : 'Chưa có file. Upload một file nhỏ để thử hai bản sao.'));
    if (state.files_truncated) $('file-list').append(node('p', 'error', 'Danh sách bị giới hạn; không coi đây là toàn bộ Catalog.'));
    $('upload-button').disabled = !model.connected || model.uploading;
  }
  async function reload(probe = false) {
    if (!model.csrf || model.polling) return;
    model.polling = true; $('refresh').disabled = true;
    try {
      probe = probe && !model.readOnly;
      const state = await request(probe ? '/api/refresh' : '/api/state', probe ? { method: 'POST', json: {} } : {});
      model.state = state; connection(true); notice(''); render(state);
    } catch (error) { if (model.csrf) notice(error.message); }
    finally { model.polling = false; $('refresh').disabled = false; }
  }
  function pending(meta) {
    try {
      const old = model.pending || JSON.parse(sessionStorage.getItem('asc-demo-pending-upload') || 'null');
      if (old && old.path === meta.path && old.size === meta.size && old.sha === meta.sha && typeof old.key === 'string') return old.key;
    } catch (_) { /* storage may be unavailable; in-memory retry still uses same request key */ }
    const key = crypto.randomUUID();
    model.pending = { ...meta, key };
    try { sessionStorage.setItem('asc-demo-pending-upload', JSON.stringify({ ...meta, key })); } catch (_) { /* no auth credential is stored here */ }
    return key;
  }
  async function upload(event) {
    event.preventDefault(); if (model.readOnly || model.uploading || !model.connected) return;
    const file = $('file-input').files[0], path = $('logical-path').value.trim();
    if (!file || !path) return;
    $('upload-status').className = ''; $('upload-status').textContent = 'Đang tính SHA-256 trước khi gửi…';
    $('upload-bytes').textContent = ''; $('upload-progress').hidden = true;
    let timer = null, monitorBusy = false;
    model.uploading = true; $('upload-button').disabled = true;
    try {
      if (file.size > model.max) throw new APIError('upload_too_large', 413);
      const sha = await sha256(await file.arrayBuffer());
      const key = pending({ path, size: file.size, sha });
      const plan = await request('/api/uploads', { method: 'POST', json: { logical_path: path, size: file.size, sha256: sha, idempotency_key: key } });
      let result = plan.file;
      if (!plan.completed) {
        model.activeTicket = plan.transfer_id;
        $('upload-status').textContent = 'Đang gửi file tới Controller. Chưa xác nhận hai bản sao.';
        const progress = async () => {
          if (monitorBusy || model.activeTicket !== plan.transfer_id) return;
          monitorBusy = true;
          try {
            const p = await request('/api/uploads/' + plan.transfer_id, { timeout: 10000 });
            if (model.activeTicket !== plan.transfer_id) return;
            $('upload-progress').hidden = false; $('upload-progress').max = p.size || 1; $('upload-progress').value = p.received_bytes;
            $('upload-bytes').textContent = 'Controller đã nhận ' + amount(p.received_bytes) + ' / ' + amount(p.size) +
              (p.checksum_verified_bytes === null ? ' · Chưa xác minh SHA toàn file' : ' · SHA đã khớp, tiếp tục kiểm tra replica');
          } catch (_) { /* main operation handles definitive result; never fabricate progress */ }
          finally { monitorBusy = false; }
        };
        void progress(); timer = setInterval(progress, 700);
        const reply = await request('/api/uploads/' + plan.transfer_id, { method: 'PUT', body: file });
        result = reply.file;
        model.activeTicket = null; clearInterval(timer); timer = null;
        $('upload-progress').hidden = false; $('upload-progress').max = file.size || 1; $('upload-progress').value = file.size;
        $('upload-bytes').textContent = 'Controller đã nhận đủ ' + amount(file.size) + ' và SHA-256 khớp. Tiến độ byte không phải bằng chứng hai bản sao.';
      }
      const deadline = Date.now() + 120000;
      while (!result.protected && Date.now() < deadline && model.csrf) {
        $('upload-status').textContent = 'Đã tiếp nhận file; đang chờ xác minh đủ hai bản sao. Giữ cùng file/key nếu cần thử lại.';
        await sleep(900); result = await request('/api/files/' + result.file_id);
      }
      $('upload-status').className = result.protected ? 'success' : '';
      $('upload-status').textContent = result.protected ? 'Đã xác nhận đủ hai bản sao trên hai miền lỗi độc lập.' : 'File chưa đủ hai bản sao. Công việc được giữ lại; kiểm tra Bản sao & SHA.';
      if (result.protected) { model.pending = null; try { sessionStorage.removeItem('asc-demo-pending-upload'); } catch (_) { /* optional metadata storage */ } }
      await reload();
    } catch (error) { $('upload-status').className = 'error'; $('upload-status').textContent = error.message; }
    finally { model.activeTicket = null; if (timer) clearInterval(timer); model.uploading = false; $('upload-button').disabled = !model.connected; }
  }
  $('login-form').addEventListener('submit', async event => {
    event.preventDefault(); $('login-button').disabled = true; $('login-error').textContent = '';
    try {
      const reply = await request('/api/login', { method: 'POST', json: { code: $('login-code').value.trim() }, csrf: false });
      model.csrf = reply.csrf;
      const session = await request('/api/session', { csrf: false }); applyMode(session); model.max = session.max_upload_bytes;
      activate(); await reload();
    } catch (error) { $('login-error').textContent = error.message; }
    finally { $('login-button').disabled = false; }
  });
  $('logout').addEventListener('click', async () => {
    clearPairing('Mã đã ẩn; đăng xuất không tự thu hồi mã node chưa dùng.');
    try { await request('/api/logout', { method: 'POST', json: {} });
      model.pending = null;
      try { sessionStorage.removeItem('asc-demo-pending-upload'); } catch (_) { /* no auth storage */ }
      loginView(); notice('');
    } catch (error) { notice(error.message); }
  });
  window.addEventListener('pagehide', () => { clearPairing('Trang đã đóng: theo dõi đã bỏ, không tự thu hồi mã.'); });
  $('pair-create').addEventListener('click', () => { void createPairing(); });
  $('refresh').addEventListener('click', () => { void reload(true); });
  $('upload-form').addEventListener('submit', upload);
  $('file-input').addEventListener('change', () => { const file = $('file-input').files[0]; if (file) $('logical-path').value = file.name; });
  $('details-close').addEventListener('click', () => $('details').close());
  for (const tab of document.querySelectorAll('[data-tab]')) tab.addEventListener('click', () => {
    for (const other of document.querySelectorAll('[data-tab]')) { const selected = other === tab; other.classList.toggle('selected', selected); other.setAttribute('aria-selected', String(selected)); $(other.dataset.tab).hidden = !selected; }
  });
  async function boot() {
    if (location.protocol !== 'https:' || !window.isSecureContext || !crypto.subtle) {
      $('login-error').textContent = 'Cần HTTPS được trình duyệt tin cậy. Xác minh CA/IP, không bỏ qua lỗi certificate.'; $('login-button').disabled = true; return;
    }
    try { applyMode(await request('/api/mode', { csrf: false })); const session = await request('/api/session', { csrf: false }); applyMode(session); model.csrf = session.csrf; model.max = session.max_upload_bytes; activate(); await reload(); }
    catch (_) { $('login-error').textContent = ''; /* normal first visit requires login */ }
    setInterval(() => { if (model.csrf && !model.uploading) void reload(); }, 10000);
  }
  void boot();
})();
