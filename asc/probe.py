"""Non-root, best-effort Android capability probe. Unknown remains unknown."""
import glob
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile

PRESETS = [
    (('sm-m515', 'galaxy m51', 'm51'), 'Samsung Galaxy M51', 6, 128, 'production-protected'),
    (('blade v40', 'zte v40'), 'ZTE Blade V40', 6, 128, 'controller-candidate'),
    (('a40', 'bphone a40'), 'Bphone A40', 4, 64, 'backup-and-voter-candidate'),
    (('h8416', 'xz3', 'h9436', 'h9493'), 'Sony Xperia XZ3', 4, 64, 'storage-and-voter-candidate'),
    (('vsmart live', 'live 1'), 'Vsmart Live', 4, 64, 'backup-node'),
    (('xa ultra', 'f321'), 'Sony XA Ultra', 3, 16, 'archive-only'),
    (('a11w', 'oppo a11w'), 'Oppo A11W', 1, 4, 'unsupported'),
]


def _cmd(*args):
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=3, check=False)
        return proc.stdout.strip() if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _memory_mb():
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemTotal:'):
                return round(int(line.split()[1]) / 1024)
    except (OSError, ValueError, IndexError):
        pass
    return None


def _volume(path):
    try:
        st = os.statvfs(path)
        return {'total_bytes': st.f_blocks * st.f_frsize,
                'free_bytes': st.f_bavail * st.f_frsize}
    except (OSError, ValueError, AttributeError):
        return None


def _detect_sd_locations():
    result = []
    seen = set()
    # Only app-specific paths are candidates for optional write test.
    for root in glob.glob('/storage/[A-Za-z0-9]*-*') + glob.glob(str(Path.home() / 'storage/external-*')):
        canonical = os.path.realpath(root)
        if not os.path.isdir(canonical):
            continue
        suffix = os.path.join('Android', 'data', 'com.termux', 'files')
        # Termux ~/storage/external-1 can already resolve to the app folder.
        app_dir = canonical if canonical.endswith(os.sep + suffix) else os.path.join(canonical, suffix)
        app_identity = os.path.realpath(app_dir)
        if app_identity in seen:
            continue
        seen.add(app_identity)
        result.append({'mount': canonical, 'app_dir': app_dir,
                       'app_dir_exists': os.path.isdir(app_dir), 'space': _volume(canonical)})
    return result


def probe_sd_write(sd):
    """Only temporary write under pre-existing Termux-owned app-specific SD folder."""
    target = sd['app_dir']
    if not os.path.isdir(target):
        return {'status': 'not_tested', 'reason': 'Termux app-specific directory not present; never create it blindly'}
    name = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.asc-probe-', dir=target, delete=False) as f:
            name = f.name
            f.write(b'asc-storage-probe-v1')
            f.flush()
            os.fsync(f.fileno())
        with open(name, 'rb') as f:
            ok = f.read() == b'asc-storage-probe-v1'
        os.unlink(name)
        name = None
        return {'status': 'pass' if ok else 'fail', 'reason': 'byte verification' if ok else 'readback mismatch'}
    except OSError as ex:
        return {'status': 'fail', 'reason': type(ex).__name__ + ': bounded probe failed'}
    finally:
        if name is not None:
            try:
                os.unlink(name)
            except OSError:
                pass  # Only the uniquely-created probe path is ever removed.


def inspect(sd_write=False):
    android_model = _cmd('getprop', 'ro.product.model')
    model = android_model or 'unknown'
    brand = _cmd('getprop', 'ro.product.manufacturer') or 'unknown'
    android = _cmd('getprop', 'ro.build.version.release') or 'unknown'
    sdk_text = _cmd('getprop', 'ro.build.version.sdk')
    sdk = int(sdk_text) if sdk_text and sdk_text.isdigit() else None
    device = _cmd('getprop', 'ro.product.device')
    product = _cmd('getprop', 'ro.product.name')
    known = lambda value: bool(value and value.lower() not in ('unknown', 'null'))
    identity_known = known(android_model) and known(brand) and sdk is not None
    candidates = ' '.join(x for x in (model, brand, device, product) if x).lower()
    preset = None
    for patterns, device, ram_gb, internal_gb, role in PRESETS:
        if any(pat in candidates for pat in patterns):
            preset = {'device': device, 'assumed_ram_gb': ram_gb,
                      'assumed_internal_gb': internal_gb, 'baseline_role': role}
            break
    protected = bool(preset and preset['baseline_role'] == 'production-protected')
    install_allowed = identity_known and not protected and sdk >= 24
    sd = _detect_sd_locations()
    for volume in sd:
        volume['write_probe'] = (probe_sd_write(volume) if sd_write and install_allowed else
                                 {'status': 'not_tested', 'reason': 'write probe not requested or device protected'})
        volume['status'] = 'writable-tested' if volume['write_probe']['status'] == 'pass' else 'detected'
    free = _volume(str(Path.home()))
    role = preset['baseline_role'] if preset else 'general-storage-candidate'
    if sdk is not None and sdk < 24 and not protected:
        role = 'unsupported'
    ram_actual = _memory_mb()
    ram_used_gb = (ram_actual / 1024) if ram_actual else (preset['assumed_ram_gb'] if preset else None)
    if role not in ('unsupported', 'production-protected') and ram_used_gb and ram_used_gb < 2:
        role = 'archive-only'
    # This score is ONLY a baseline role hint; never authorizes leader election.
    score = None
    if ram_used_gb is not None:
        score = min(90, round(35 + 5 * min(ram_used_gb, 8) +
                              (10 if free and free['free_bytes'] >= 8 * 1024**3 else 0)))
        if role == 'production-protected':
            score = min(score, 25)
        if role == 'unsupported':
            score = 0
    return {'profile_version': 1, 'model': model, 'manufacturer': brand, 'android': android, 'sdk': sdk,
            'machine': platform.machine(), 'memory_mb': ram_actual,
            'preset': preset, 'protected': protected,
            'device_identity_status': 'known' if identity_known else 'unknown',
            'installation_allowed': install_allowed,
            'score_basis': 'runtime-ram' if ram_actual is not None else ('manufacturer-baseline' if preset else 'unknown'),
            'sd_status': ('writable-tested' if any(v['status'] == 'writable-tested' for v in sd)
                          else 'detected' if sd else 'unknown'),
            'recommended_role': role, 'readiness_score': score,
            'internal_app_storage': free, 'sd_candidates': sd,
            'limitations': ['Score is theoretical, not a leader election vote',
                            'Android battery/background behavior requires observation',
                            'SD write access is never assumed without a write probe']}


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--sd-write', action='store_true')
    args = p.parse_args()
    print(json.dumps(inspect(args.sd_write), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
