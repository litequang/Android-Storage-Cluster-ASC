'use strict';
(() => {
  const $ = id => document.getElementById(id);
  let installation = null;
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault(); installation = event; $('install-app').hidden = false;
  });
  $('install-app').addEventListener('click', async () => {
    const request = installation; installation = null; $('install-app').hidden = true;
    if (!request) return;
    try {
      await request.prompt();
      const choice = await request.userChoice;
      $('install-status').textContent = choice.outcome === 'accepted'
        ? 'Trình duyệt đã chấp nhận yêu cầu cài Web App; Node/Termux vẫn chạy riêng.'
        : 'Chưa cài Web App. Bạn vẫn dùng được Dashboard trong trình duyệt.';
    } catch (_) { $('install-status').textContent = 'Chưa xác nhận cài Web App. Tiếp tục dùng trình duyệt.'; }
  });
  window.addEventListener('appinstalled', () => {
    installation = null; $('install-app').hidden = true;
    $('install-status').textContent = 'Đã cài Web App trong trình duyệt này. Vẫn cần Controller online; không có offline-write.';
  });
  if (window.isSecureContext && 'serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js', { scope: '/', updateViaCache: 'none' })
      .catch(() => { $('install-status').textContent = 'Web App chưa sẵn sàng; Dashboard vẫn dùng qua trình duyệt HTTPS.'; });
  }
  const model = { mode: null, readOnly: true, csrf: null, connected: false, state: null, max: null, uploading: false, activeTicket: null, polling: false, pending: null, features: null, role: null, username: null, passwordEnabled: false };
  const pairing = { generation: 0, ticket: null, timer: null, creating: false, polling: false };
  const management = { generation: 0, revision: 0, node: null, preview: null, busy: false };
  const accountUI = { generation: 0, editing: null, busy: false };
  const fileUI = { generation: 0, offset: 0, next: null, folder: '', recursive: true, page: null };
  const jobUI = { generation: 0, offset: 0, next: null };
  let detailGeneration = 0;
  const messages = {
    pairing_limit: 'Đã đạt giới hạn mã đang theo dõi (8/phiên, 32/Controller). Đợi hoặc kiểm tra các mã đã tạo.',
    pairing_not_found: 'Không còn bằng chứng theo dõi trong phiên này. Không suy ra mã đã bị thu hồi.',
    unsupported_runtime: 'Quick Join chỉ hỗ trợ Demo single-writer đã xác minh.',
    read_only_mode: 'Chế độ Core chỉ quan sát; thao tác thay đổi bị từ chối phía server.',
    login_rejected: 'Mã không hợp lệ, đã dùng hoặc đã hết hạn. Lấy mã mới từ Controller.',
    login_required: 'Phiên đã hết hạn. Đăng nhập lại để tiếp tục.',
    rate_limited: 'Đã thử quá nhiều lần. Đợi giới hạn đăng nhập mở lại rồi thử tiếp.',
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
    node_state_changed: 'Node hoặc phê duyệt đã thay đổi. Đọc lại trạng thái, xem trước và xác nhận lại.',
    node_not_manageable: 'Node không tồn tại, bị bảo vệ hoặc không thể quản lý trong chế độ này.',
    management_limit: 'Đã đạt giới hạn bản xem trước. Đợi bản cũ hết hạn rồi thử lại.',
    management_preview_expired: 'Bản xem trước hết hạn hoặc không thuộc phiên này. Xem trước lại.',
    management_confirmation_required: 'Cần đúng Node ID và xác nhận endpoint/PIN/volume/miền lỗi trước khi áp dụng.',
    role_denied: 'Tài khoản Viewer chỉ được đọc và tải file; thao tác này cần Owner.',
    account_exists: 'Tên đăng nhập đã tồn tại. Đọc lại danh sách trước khi thử tiếp.',
    account_limit: 'Đã đạt giới hạn tài khoản hoặc số lần thay đổi được hỗ trợ.',
    account_state_changed: 'Tài khoản đã thay đổi. Đọc lại trước khi xác nhận thao tác mới.',
    last_owner_required: 'Phải giữ ít nhất một Owner. Tài khoản đầu tiên phải là Owner.',
    account_state_unavailable: 'State tài khoản không đọc/xác minh được. Giữ nguyên file để owner kiểm tra, không tự tạo lại.',
    job_state_changed: 'Tác vụ không còn ở trạng thái được thử lại. Đọc trạng thái mới; chưa suy ra sao chép thành công.',
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
    if (!ok) { clearManagement(); closeAccountEditor(); $('account-new-password').value = ''; }
    if (!ok) clearPairing('Mất kết nối: mã đã ẩn, đăng ký và quyền lưu trữ UNKNOWN.');
    pairingButton();
    if (!ok && $('details').open) $('details').close();
    $('connection').textContent = model.readOnly ? (ok ? 'Gateway online' : 'Gateway UNKNOWN') : ok ? 'Controller online' : 'Controller UNKNOWN';
    $('connection').className = 'badge ' + (ok ? 'good' : 'unknown');
    $('upload-button').disabled = !ok || model.uploading || !canUpload();
    if (model.state) render(model.state);
  }
  function loginView(clear = true) {
    model.csrf = null; model.connected = false; model.state = null;
    model.features = null; clearManagement();
    fileUI.generation++; fileUI.page = null; fileUI.offset = 0; fileUI.folder = ''; fileUI.recursive = true;
    jobUI.generation++; jobUI.offset = 0; $('job-list').replaceChildren(); detailGeneration++;
    $('file-search').value = ''; $('upload-version').value = '1';
    closeAccountEditor(); $('account-list').replaceChildren(); $('account-new-password').value = ''; $('login-password').value = '';
    $('account-new-username').value = ''; $('account-result').textContent = '';
    $('actor-label').hidden = true; $('actor-label').textContent = '';
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
      const value = await response.json();
      if (path === '/api/capabilities' && response.headers.get('X-ASC-Access-Mode') === 'file-access-only') {
        value.node_management = false; value.account_management = false; value.job_retry = false;
      }
      return value;
    } catch (error) {
      if (error instanceof APIError) throw error;
      connection(false); notice('Mất kết nối Controller. Dữ liệu dưới đây là bản xem cũ; trạng thái bảo vệ chưa xác minh lại.');
      throw new APIError('core_unavailable', 0);
    } finally { clearTimeout(timer); }
  }
  function pairingButton() {
    $('pair-create').disabled = !model.csrf || !model.connected || model.readOnly || !model.features?.node_management || pairing.creating;
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
        value.storage_approved === false ? 'CHƯA phê duyệt lưu trữ / miền lỗi. Owner kiểm tra tại Điện thoại → Quản lý hoặc CLI.' : 'Quyền lưu trữ / miền lỗi UNKNOWN.' : 'Quyền lưu trữ chưa xác minh.';
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
    if (value.authenticated === true) {
      if (value.role !== undefined && !['owner','viewer'].includes(value.role)) throw new APIError('unsupported_runtime',503);
      model.role = value.role || 'owner'; model.username = value.username || null;
    }
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
  async function loadFeatures() {
    try {
      const value = await request('/api/capabilities');
      if (value.dashboard_api_version !== 1 || value.mode !== model.mode) throw new APIError('unsupported_runtime', 503);
      model.features = value; $('capability-note').hidden = true;
    } catch (error) {
      // Published older file gateways do not forward this new metadata route.
      // Keep ONLY original file functions in the already verified mode/session;
      // never enable management or switch Core/recovery into Demo.
      if (!(error instanceof APIError) || ![403,404].includes(error.status)) throw error;
      model.features = { node_management:false, account_management:false, owner_password:false,
        file_upload:!model.readOnly && model.role === 'owner', file_download:!model.readOnly,
        refresh_probe:!model.readOnly && model.role === 'owner' };
      $('capability-note').textContent = 'Kết nối chỉ hỗ trợ File Manager cũ. Quản trị mới cần Dashboard LAN trực tiếp hoặc gateway tương thích.';
      $('capability-note').hidden = false;
    }
    $('upload-panel').hidden = model.readOnly || !model.features.file_upload;
    $('accounts-tab').hidden = !model.features.account_management;
    $('file-tools').hidden = !model.features.file_browse;
    $('file-pagination').hidden = !model.features.file_browse;
    $('version-upload-fields').hidden = !model.features.version_upload;
    $('jobs-tab').hidden = !model.features.job_read;
    document.querySelector('[data-tab="quick-join"]').hidden = !model.features.node_management;
    $('refresh').textContent = model.features.refresh_probe ? 'Cập nhật kiểm tra' : 'Đọc trạng thái';
    $('actor-label').textContent = (model.role === 'viewer' ? 'Viewer' : 'Owner') + (model.username ? ' · '+model.username : ' · mã cục bộ');
    $('actor-label').hidden = false;
  }
  function canUpload() { return !model.readOnly && model.features?.file_upload === true; }
  function loginKind() {
    const password = $('login-kind').value === 'password' && model.passwordEnabled && !model.readOnly;
    if (!password) $('login-kind').value = 'code';
    $('login-code-fields').hidden = password; $('login-code').disabled = password; $('login-code').required = !password;
    $('login-password-fields').hidden = !password;
    for (const id of ['login-username','login-password']) { $(id).disabled = !password; $(id).required = password; }
    if (password) $('login-method').textContent = 'Dùng tài khoản do Owner tạo. Mật khẩu chỉ gửi qua HTTPS, phiên đăng nhập không lưu vào browser storage.';
  }
  async function loadAuthMethods() {
    model.passwordEnabled = false;
    try {
      const value = await request('/api/auth/methods', { csrf:false });
      if (value.auth_api_version === 1 && value.password === true && !model.readOnly) model.passwordEnabled = true;
    } catch (_) { /* Legacy file ingress remains one-time code only; no downgrade of TLS or runtime. */ }
    $('login-kind').querySelector('[value="password"]').disabled = !model.passwordEnabled;
    if (model.passwordEnabled) $('login-kind').value = 'password';
    loginKind();
  }
  function closeAccountEditor() {
    accountUI.generation += 1; accountUI.editing = null; accountUI.busy = false;
    $('account-password').value = ''; $('account-confirm-name').value = ''; $('account-delete').checked = false;
    $('account-target').textContent = '';
    $('account-password').disabled = false; $('account-save').disabled = false; $('account-change-result').textContent = '';
    if ($('account-dialog').open) $('account-dialog').close();
  }
  function editAccount(item) {
    if (!model.features?.account_management || !model.connected) return;
    closeAccountEditor(); accountUI.editing = item;
    $('account-target').textContent = item.username + ' · generation '+item.generation;
    $('account-role').value = item.role; $('account-dialog').showModal();
  }
  async function loadAccounts() {
    if (!model.features?.account_management || !model.csrf) return;
    const generation = accountUI.generation;
    try {
      const value = await request('/api/accounts');
      if (generation !== accountUI.generation || !model.csrf) return;
      if (value.account_api_version !== 1) throw new APIError('unsupported_runtime',503);
      $('account-list').replaceChildren(...value.accounts.map(item => {
        const card = node('article','node-card'); card.dataset.accountId = item.account_id;
        card.append(node('h3','',item.username),node('p','',item.role === 'owner' ? 'Owner — quản trị toàn cụm' : 'Viewer — đọc toàn bộ file'),
          node('p','muted','Cập nhật: '+date(item.updated_at)),button('Sửa quyền / mật khẩu',()=>editAccount(item)));
        return card;
      }));
      if (!value.accounts.length) $('account-list').append(node('p','muted','Chưa có tài khoản. Tạo Owner đầu tiên bằng phiên mã cục bộ này.'));
    } catch (error) { if (generation === accountUI.generation) $('account-result').textContent = error.message; }
  }
  $('account-create-form').addEventListener('submit',async event => {
    event.preventDefault(); if (!model.features?.account_management || !model.connected || accountUI.busy) return;
    const generation = accountUI.generation;
    const body = { username:$('account-new-username').value.trim(), password:$('account-new-password').value, role:$('account-new-role').value };
    $('account-new-password').value = ''; accountUI.busy = true; $('account-create').disabled = true;
    $('account-result').textContent = 'Đang tạo tài khoản; chưa xác nhận thành công.';
    try {
      await request('/api/accounts',{method:'POST',json:body});
      if (generation !== accountUI.generation || !model.csrf) return;
      $('account-result').textContent = 'Controller đã xác nhận tạo tài khoản. Bạn có thể đăng xuất rồi dùng tài khoản/mật khẩu.';
      await loadAccounts();
    } catch (error) { if (generation === accountUI.generation) $('account-result').textContent = error.message; }
    finally { if (generation === accountUI.generation) accountUI.busy = false; $('account-create').disabled = false; }
  });
  $('account-change-form').addEventListener('submit',async event => {
    event.preventDefault(); const item = accountUI.editing;
    if (!item || accountUI.busy || !model.connected || !model.features?.account_management) return;
    if ($('account-confirm-name').value !== item.username) { $('account-change-result').textContent = 'Nhập đúng tên đăng nhập để xác nhận.'; return; }
    const generation = accountUI.generation;
    const body = { expected_generation:item.generation, role:$('account-role').value, password:$('account-password').value, delete:$('account-delete').checked };
    $('account-password').value = ''; accountUI.busy = true; $('account-save').disabled = true;
    $('account-change-result').textContent = 'Đang lưu; chờ Controller xác nhận.';
    try {
      const result = await request('/api/accounts/'+encodeURIComponent(item.username)+'/change',{method:'POST',json:body});
      if (generation !== accountUI.generation || !model.csrf) return;
      if (result.current_session_revoked) { loginView(); notice('Đã cập nhật tài khoản và thu hồi phiên cũ. Đăng nhập lại.'); await loadAuthMethods(); }
      else { closeAccountEditor(); $('account-result').textContent = 'Controller đã xác nhận thay đổi và thu hồi các phiên của tài khoản đó.'; await loadAccounts(); }
    } catch (error) { if (generation === accountUI.generation) $('account-change-result').textContent = error.message; }
    finally { if (generation === accountUI.generation) { accountUI.busy = false; $('account-save').disabled = false; } }
  });
  $('account-delete').addEventListener('change',()=>{ $('account-password').value = ''; $('account-password').disabled = $('account-delete').checked; });
  $('account-close').addEventListener('click',closeAccountEditor);
  $('account-dialog').addEventListener('cancel',closeAccountEditor);
  $('accounts-refresh').addEventListener('click',()=>{ void loadAccounts(); });
  $('login-kind').addEventListener('change',()=>{ $('login-password').value = ''; $('login-code').value = ''; loginKind(); });
  function clearManagement() {
    management.generation += 1; management.node = null; management.preview = null; management.busy = false;
    $('manage-apply').disabled = false; $('manage-preview').disabled = false;
    $('manage-confirm-panel').hidden = true; $('manage-confirm-node').value = ''; $('manage-domain-confirm').checked = false;
    $('manage-preview-body').textContent = ''; $('manage-result').textContent = '';
    $('manage-node').textContent = '';
    for (const id of ['manage-origin','manage-pin','manage-volumes','manage-domain','manage-name']) $(id).value = '';
    if ($('manage-dialog').open) $('manage-dialog').close();
  }
  function managementFields() {
    management.revision += 1;
    management.preview = null; $('manage-confirm-panel').hidden = true;
    $('manage-confirm-node').value = ''; $('manage-domain-confirm').checked = false;
    const action = $('manage-action').value;
    $('manage-approval-fields').hidden = action !== 'approve';
    $('manage-name-fields').hidden = action !== 'rename';
    $('manage-revoke-warning').hidden = action !== 'revoke';
  }
  async function manageNode(item) {
    if (!model.features?.node_management || model.readOnly || !model.connected) return;
    clearManagement(); const generation = management.generation;
    try {
      const value = await request('/api/manage/v1/nodes/' + encodeURIComponent(item.node_id));
      if (generation !== management.generation || !model.csrf) return;
      management.node = value;
      $('manage-node').textContent = value.name + ' · Node ID: ' + value.node_id + ' · Replica ghi nhận: ' + value.recorded_replicas;
      $('manage-name').value = value.name; $('manage-action').value = 'approve';
      $('manage-origin').value = value.approval?.origin || '';
      $('manage-pin').value = value.approval?.pin || '';
      $('manage-volumes').value = (value.approval?.volume_ids || value.reported_volume_ids || []).join('\n');
      $('manage-domain').value = value.approval?.device_id || '';
      managementFields(); $('manage-preview').disabled = value.state !== 'active';
      $('manage-dialog').showModal();
    } catch (error) { notice(error.message); }
  }
  $('manage-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (!management.node || management.busy || !model.connected || !model.csrf) return;
    const generation = management.generation, revision = management.revision, action = $('manage-action').value;
    const parameters = action === 'approve' ? {
      origin: $('manage-origin').value.trim(), pin: $('manage-pin').value.replace(/:/g, '').trim().toLowerCase(),
      volume_ids: $('manage-volumes').value.split(/[\s,]+/).filter(Boolean), failure_domain: $('manage-domain').value.trim()
    } : action === 'rename' ? { name: $('manage-name').value.trim() } : {};
    management.busy = true; $('manage-preview').disabled = true; $('manage-result').textContent = 'Đang lấy bản xem trước; chưa áp dụng thay đổi.';
    try {
      const value = await request('/api/manage/v1/nodes/' + encodeURIComponent(management.node.node_id) + '/preview',
        { method: 'POST', json: { management_version: 1, action, parameters } });
      if (generation !== management.generation || revision !== management.revision || !model.csrf) return;
      management.preview = value;
      $('manage-preview-body').textContent = value.action + '\n' + JSON.stringify(value.parameters, null, 2) + '\nReplica đang ghi nhận: ' + value.recorded_replicas + '\nBản xem trước hết hạn sau tối đa 120 giây. Chưa xác minh storage writable.';
      $('manage-confirm-panel').hidden = false; $('manage-result').textContent = 'Đối chiếu thông tin rồi xác nhận bằng đúng Node ID.';
    } catch (error) { if (generation === management.generation) $('manage-result').textContent = error.message; }
    finally { if (generation === management.generation) { management.busy = false; $('manage-preview').disabled = false; } }
  });
  $('manage-apply').addEventListener('click', async () => {
    if (!management.preview || management.busy || !model.connected || !model.csrf) return;
    const generation = management.generation, preview = management.preview;
    management.busy = true; $('manage-apply').disabled = true; $('manage-result').textContent = 'Đang áp dụng; chờ Controller xác nhận.';
    try {
      await request('/api/manage/v1/confirm/' + encodeURIComponent(preview.preview_id), { method: 'POST', json: {
        management_version: 1, intent_sha256: preview.intent_sha256, confirmation_node_id: $('manage-confirm-node').value.trim(),
        physical_domain_confirmed: $('manage-domain-confirm').checked
      } });
      if (generation !== management.generation || !model.csrf) return;
      management.preview = null; $('manage-confirm-panel').hidden = true;
      $('manage-result').textContent = 'Controller đã xác nhận thay đổi. Phê duyệt không phải bằng chứng đủ replica hoặc volume writable.';
      await reload(true);
    } catch (error) { if (generation === management.generation) $('manage-result').textContent = error.message; }
    finally { if (generation === management.generation) { management.busy = false; $('manage-apply').disabled = false; } }
  });
  $('manage-close').addEventListener('click', clearManagement);
  $('manage-dialog').addEventListener('cancel', clearManagement);
  $('manage-action').addEventListener('change', managementFields);
  for (const id of ['manage-origin','manage-pin','manage-volumes','manage-domain','manage-name']) $(id).addEventListener('input', managementFields);
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
    detailGeneration++;
    $('details-title').textContent = title; $('details-body').replaceChildren(...values);
    if (!$('details').open) $('details').showModal();
  }
  function nodeDetails(item) {
    const rows = [detail('Node ID', item.node_id), detail('Phê duyệt', item.storage_approved ? 'Đã duyệt lưu trữ' : 'Chưa duyệt lưu trữ / cần owner duyệt lại'),
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
      if (model.features?.node_management && !model.readOnly) {
        const manage = button('Quản lý', () => manageNode(item)); manage.dataset.action = 'manage'; manage.disabled = !model.connected;
        card.append(manage);
      }
      return card;
    }));
    if (!state.nodes.length) $('node-list').append(node('p', 'muted', 'Chưa có Storage Node được ghép. Mở Ghép điện thoại để tạo mã, rồi phê duyệt trong Quản lý.'));
    if (!model.features?.file_browse || !fileUI.page) {
      $('file-count').textContent = count(c.files) + ' file';
      renderFiles(state.files);
      if (state.files_truncated) $('file-list').append(node('p', 'error', 'Danh sách bị giới hạn; không coi đây là toàn bộ Catalog.'));
    } else renderBrowse(fileUI.page);
    $('upload-button').disabled = !model.connected || model.uploading || !canUpload();
  }
  function renderFiles(files) {
    $('file-list').replaceChildren(...files.map(file => {
      const row = node('article', 'file-row'); row.dataset.fileId = file.file_id;
      const info = node('div', 'file-info'); info.append(node('div', 'file-name', file.logical_path), badge(file),
        node('p', 'file-meta', amount(file.size) + ' · v' + file.version + ' · verified ' + file.verified_replicas + ' · available ' + (model.connected ? count(file.available_replicas) : 'UNKNOWN')));
      const actions = node('div', 'file-actions');
      const view = button('Bản sao & SHA', () => replicas(file.file_id)); view.dataset.action = 'replicas';
      const get = button('Tải xuống', () => download(file)); get.dataset.action = 'download'; get.disabled = !model.connected || file.size > model.max;
      actions.append(view); if (!model.readOnly) actions.append(get);
      if (model.features?.file_history) { const h = button('Lịch sử', () => history(file)); h.dataset.action = 'history'; actions.append(h); }
      if (model.features?.version_upload) { const v = button('Thêm phiên bản', () => newVersion(file)); v.dataset.action = 'new-version'; v.disabled = !model.connected; actions.append(v); }
      row.append(info, actions); return row;
    }));
    if (!files.length) $('file-list').append(node('p', 'muted', 'Không có file khớp bộ lọc tại thời điểm đọc.'));
  }
  function fileQuery(extra = {}) {
    return { browse_api_version:1, offset:fileUI.offset, search:$('file-search').value,
      folder:fileUI.folder, recursive:fileUI.recursive, sort:$('file-sort').value, versions:$('file-versions').value, ...extra };
  }
  function renderBrowse(page) {
    renderFiles(page.entries.filter(x => x.kind === 'file'));
    const folders = page.entries.filter(x => x.kind === 'folder').map(item => {
      const row = node('article', 'file-row'); row.dataset.folder = item.logical_path;
      row.append(node('strong', 'file-name', item.logical_path.split('/').pop()), button('Mở thư mục', () => navigateFolder(item.logical_path)));
      return row;
    });
    if (folders.length && !page.entries.some(x => x.kind === 'file')) $('file-list').replaceChildren();
    $('file-list').prepend(...folders);
    $('file-count').textContent = count(page.total) + ' mục khớp bộ lọc';
    $('browse-location').textContent = fileUI.recursive ? 'Tìm đệ quy: ' + (fileUI.folder || 'toàn cụm') : 'Thư mục logic: /' + fileUI.folder;
    $('browse-parent').hidden = !fileUI.folder;
    $('files-page').textContent = 'Mục ' + (page.total ? page.offset+1 : 0) + '–' + (page.offset+page.entries.length) + ' / ' + page.total;
    $('files-prev').disabled = !model.connected || fileUI.offset === 0;
    $('files-next').disabled = !model.connected || page.next_offset === null;
    $('browse-status').textContent = !model.connected ? 'Mất kết nối: danh sách cũ, trạng thái hiện tại UNKNOWN.' : page.query_limit_reached ? 'Đã đến giới hạn duyệt; thu hẹp thư mục hoặc từ khóa.' : '';
  }
  async function loadFiles() {
    if (!model.features?.file_browse || !model.csrf) return;
    const generation = ++fileUI.generation; $('browse-status').textContent = 'Đang đọc Catalog…';
    try {
      const page = await request('/api/files/query', { method:'POST', json:fileQuery() });
      if (generation !== fileUI.generation || !model.csrf) return;
      fileUI.page = page; fileUI.next = page.next_offset; renderBrowse(page);
    } catch (error) { if (generation === fileUI.generation && model.csrf) $('browse-status').textContent = error.message; }
  }
  function navigateFolder(folder) { fileUI.folder = folder; fileUI.recursive = false; fileUI.offset = 0; $('file-search').value = ''; void loadFiles(); }
  async function history(file) {
    showDetails('Lịch sử: ' + file.logical_path, [node('p', 'muted', 'Các phiên bản bất biến trong Catalog; không phải external backup.')]);
    const generation = detailGeneration;
    async function page(start) {
      try {
        const result = await request('/api/files/query', { method:'POST', json:fileQuery({ offset:start, folder:'', search:'', recursive:true, versions:'all', sort:'name', history_file_id:file.file_id }) });
        if (generation !== detailGeneration || !$('details').open || !model.csrf) return;
        const rows = result.entries.map(item => { const card = node('div', 'replica-card'); card.dataset.historyFileId = item.file_id;
          card.append(node('strong', '', 'Phiên bản ' + item.version), badge(item), detail('SHA-256', item.sha256), detail('Dung lượng', amount(item.size)), button('Tải phiên bản này', () => download(item))); return card; });
        $('details-body').replaceChildren(...rows);
        const nav = node('div', 'file-toolbar');
        if (start > 0) nav.append(button('Trang trước', () => page(Math.max(0, start-50))));
        if (result.next_offset !== null) nav.append(button('Trang sau', () => page(result.next_offset)));
        $('details-body').append(nav);
      } catch (error) { if (generation === detailGeneration && $('details').open) $('details-body').replaceChildren(node('p', 'error', error.message)); }
    }
    await page(0);
  }
  async function newVersion(file) {
    try {
      const result = await request('/api/files/query', { method:'POST', json:fileQuery({ offset:0, folder:'', search:'', recursive:true, versions:'all', sort:'name', history_file_id:file.file_id }) });
      if (!model.csrf || !canUpload()) return;
      const version = result.entries[0].version+1;
      if (version > 1000000) throw new APIError('bad_request', 400);
      $('logical-path').value = file.logical_path; $('upload-version').value = String(version); $('file-input').value = '';
      $('upload-status').textContent = 'Chọn nội dung cho phiên bản ' + version + '. File cũ giữ nguyên; chưa có dữ liệu mới được gửi.';
      $('upload-panel').scrollIntoView({ block:'start' }); $('file-input').focus();
    } catch (error) { notice(error.message); }
  }
  async function loadJobs() {
    if (!model.features?.job_read || !model.csrf) return;
    const generation = ++jobUI.generation; $('jobs-status').textContent = 'Đang đọc hàng đợi…';
    try {
      const page = await request('/api/jobs/query', { method:'POST', json:{offset:jobUI.offset} });
      if (generation !== jobUI.generation || !model.csrf) return;
      jobUI.next = page.next_offset;
      $('job-list').replaceChildren(...page.jobs.map(job => {
        const card = node('article', 'file-row'); card.dataset.jobId = job.job_id;
        const info = node('div', 'file-info'); info.append(node('strong', '', job.kind + ' · ' + job.state), detail('File / Node', short(job.file_id) + ' / ' + short(job.target_node_id)), detail('Lần thử / cập nhật', count(job.attempts) + ' / ' + date(job.updated_at)), detail('Lỗi', job.last_error || 'Chưa ghi nhận'));
        card.append(info, button('Chi tiết', async () => { try { const d = await request('/api/jobs/'+job.job_id); showDetails('Tác vụ ' + short(job.job_id), [detail('Trạng thái', d.job.state), ...d.history.map(h => detail(date(h.created_at), h.state + (h.error ? ' · '+h.error : '')))]); } catch(error) { notice(error.message); } }));
        if (job.retryable && model.features.job_retry) card.append(button('Yêu cầu thử lại', async () => {
          try { await request('/api/jobs/'+job.job_id+'/retry', {method:'POST', json:{}}); await loadJobs(); $('jobs-status').textContent = 'Controller đã nhận yêu cầu retry. Chờ kiểm chứng bytes/replica; chưa phải thành công.'; }
          catch(error) { await loadJobs(); $('jobs-status').textContent = error.message; }
        }));
        return card;
      }));
      if (!page.jobs.length) $('job-list').append(node('p', 'muted', 'Chưa có tác vụ trong trang này.'));
      $('jobs-page').textContent = 'Từ ' + jobUI.offset + ' · ' + page.jobs.length + ' tác vụ';
      $('jobs-prev').disabled = jobUI.offset === 0; $('jobs-next').disabled = page.next_offset === null;
      $('jobs-status').textContent = '';
    } catch(error) { if (generation === jobUI.generation && model.csrf) $('jobs-status').textContent = error.message; }
  }
  async function reload(probe = false) {
    if (!model.csrf || model.polling) return;
    model.polling = true; $('refresh').disabled = true;
    try {
      probe = probe && !model.readOnly && model.features?.refresh_probe === true;
      const state = await request(probe ? '/api/refresh' : '/api/state', probe ? { method: 'POST', json: {} } : {});
      model.state = state; connection(true); notice(''); render(state);
      await loadFiles();
      if (!$('jobs').hidden) await loadJobs();
    } catch (error) { if (model.csrf) notice(error.message); }
    finally { model.polling = false; $('refresh').disabled = false; }
  }
  function pending(meta) {
    try {
      const old = model.pending || JSON.parse(sessionStorage.getItem('asc-demo-pending-upload') || 'null');
      if (old && old.path === meta.path && old.size === meta.size && old.sha === meta.sha && (old.version || 1) === meta.version && typeof old.key === 'string') return old.key;
    } catch (_) { /* storage may be unavailable; in-memory retry still uses same request key */ }
    const key = crypto.randomUUID();
    model.pending = { ...meta, key };
    try { sessionStorage.setItem('asc-demo-pending-upload', JSON.stringify({ ...meta, key })); } catch (_) { /* no auth credential is stored here */ }
    return key;
  }
  async function upload(event) {
    event.preventDefault(); if (!canUpload() || model.uploading || !model.connected) return;
    const file = $('file-input').files[0], path = $('logical-path').value.trim();
    if (!file || !path) return;
    $('upload-status').className = ''; $('upload-status').textContent = 'Đang tính SHA-256 trước khi gửi…';
    $('upload-bytes').textContent = ''; $('upload-progress').hidden = true;
    let timer = null, monitorBusy = false;
    model.uploading = true; $('upload-button').disabled = true;
    try {
      if (file.size > model.max) throw new APIError('upload_too_large', 413);
      const sha = await sha256(await file.arrayBuffer());
      const version = model.features?.version_upload ? Number($('upload-version').value) : 1;
      if (!Number.isInteger(version) || version < 1 || version > 1000000) throw new APIError('bad_request', 400);
      const key = pending({ path, size: file.size, sha, version });
      const payload = { logical_path: path, size: file.size, sha256: sha, idempotency_key: key };
      if (model.features?.version_upload) payload.version = version;
      let plan;
      for (let attempt = 0; attempt < 5; attempt++) {
        try { plan = await request('/api/uploads', { method:'POST', json:payload }); break; }
        catch (error) {
          if (error.status !== 409 || error.code !== 'transfer_busy' || attempt === 4 || !model.csrf) throw error;
          $('upload-status').textContent = 'Worker đang xác minh lần gửi trước. Đợi lease kết thúc; giữ nguyên nội dung, phiên bản và key.';
          await sleep(900);
        }
      }
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
    finally { model.activeTicket = null; if (timer) clearInterval(timer); model.uploading = false; $('upload-button').disabled = !model.connected || !canUpload(); }
  }
  $('login-form').addEventListener('submit', async event => {
    event.preventDefault(); $('login-button').disabled = true; $('login-error').textContent = '';
    const passwordLogin = $('login-kind').value === 'password';
    try {
      const credentials = passwordLogin ? { username:$('login-username').value.trim(), password:$('login-password').value } : { code:$('login-code').value.trim() };
      $('login-password').value = ''; $('login-code').value = '';
      const reply = await request('/api/login', { method: 'POST', json: credentials, csrf: false });
      model.csrf = reply.csrf;
      const session = await request('/api/session', { csrf: false }); applyMode(session); model.max = session.max_upload_bytes; await loadFeatures();
      activate(); await reload();
    } catch (error) { $('login-error').textContent = passwordLogin && error.code === 'login_rejected' ? 'Tên đăng nhập hoặc mật khẩu không đúng.' : error.message; }
    finally { $('login-button').disabled = false; }
  });
  $('logout').addEventListener('click', async () => {
    clearPairing('Mã đã ẩn; đăng xuất không tự thu hồi mã node chưa dùng.');
    try { await request('/api/logout', { method: 'POST', json: {} });
      model.pending = null;
      try { sessionStorage.removeItem('asc-demo-pending-upload'); } catch (_) { /* no auth storage */ }
      loginView(); notice(''); await loadAuthMethods();
    } catch (error) { notice(error.message); }
  });
  window.addEventListener('pagehide', () => { clearPairing('Trang đã đóng: theo dõi đã bỏ, không tự thu hồi mã.'); clearManagement(); closeAccountEditor(); $('account-new-password').value = ''; $('login-password').value = ''; });
  $('pair-create').addEventListener('click', () => { void createPairing(); });
  $('refresh').addEventListener('click', () => { void reload(true); });
  $('upload-form').addEventListener('submit', upload);
  $('upload-new-file').addEventListener('click', () => { $('upload-version').value = '1'; $('logical-path').value = ''; $('file-input').value = ''; $('upload-status').textContent = 'Chọn tên và nội dung mới. Lần gửi dở trước vẫn giữ trong Controller, không tự xóa.'; });
  $('file-input').addEventListener('change', () => { const file = $('file-input').files[0]; if (file && Number($('upload-version').value) === 1) $('logical-path').value = file.name; });
  $('details-close').addEventListener('click', () => { detailGeneration++; $('details').close(); });
  $('details').addEventListener('close', () => { detailGeneration++; });
  $('file-search-form').addEventListener('submit', e => { e.preventDefault(); fileUI.offset = 0; void loadFiles(); });
  $('browse-all').addEventListener('click', () => { fileUI.folder = ''; fileUI.recursive = true; fileUI.offset = 0; void loadFiles(); });
  $('browse-root').addEventListener('click', () => navigateFolder(''));
  $('browse-parent').addEventListener('click', () => navigateFolder(fileUI.folder.split('/').slice(0,-1).join('/')));
  $('files-prev').addEventListener('click', () => { fileUI.offset = Math.max(0,fileUI.offset-50); void loadFiles(); });
  $('files-next').addEventListener('click', () => { if (fileUI.next !== null) { fileUI.offset = fileUI.next; void loadFiles(); } });
  $('jobs-refresh').addEventListener('click', () => { void loadJobs(); });
  $('jobs-prev').addEventListener('click', () => { jobUI.offset = Math.max(0,jobUI.offset-100); void loadJobs(); });
  $('jobs-next').addEventListener('click', () => { if (jobUI.next !== null) { jobUI.offset = jobUI.next; void loadJobs(); } });
  for (const tab of document.querySelectorAll('[data-tab]')) tab.addEventListener('click', () => {
    for (const other of document.querySelectorAll('[data-tab]')) { const selected = other === tab; other.classList.toggle('selected', selected); other.setAttribute('aria-selected', String(selected)); $(other.dataset.tab).hidden = !selected; }
    if (tab.dataset.tab === 'accounts') void loadAccounts();
    if (tab.dataset.tab === 'jobs') void loadJobs();
  });
  async function boot() {
    if (location.protocol !== 'https:' || !window.isSecureContext || !crypto.subtle) {
      $('login-error').textContent = 'Cần HTTPS được trình duyệt tin cậy. Xác minh CA/IP, không bỏ qua lỗi certificate.'; $('login-button').disabled = true; return;
    }
    try { applyMode(await request('/api/mode', { csrf: false })); await loadAuthMethods(); const session = await request('/api/session', { csrf: false }); applyMode(session); model.csrf = session.csrf; model.max = session.max_upload_bytes; await loadFeatures(); activate(); await reload(); }
    catch (_) { $('login-error').textContent = ''; /* normal first visit requires login */ }
    setInterval(() => { if (model.csrf && !model.uploading) void reload(); }, 10000);
  }
  void boot();
})();
