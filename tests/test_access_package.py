"""Real immutable bundle extraction/venvs/dependencies. No phone or cloud setup."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from asc.demo import package as demo_package
from tools import package_access as package

PIP=Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python')
WHEELS=Path('/workspace/asc-access-dev/wheels')


class AccessPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.asc-distribution-test-',dir=Path.home());self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.repo=Path(__file__).resolve().parents[1]
        self.archive=self.base/'bundle.tar.gz';self.report=package.build(self.repo,self.archive)
    def install(self,label='code',version=None):
        archive=self.archive;sha=self.report['sha256']
        if version:
            archive=self.base/(label+'.tar.gz');sha=package.build(self.repo,archive,version)['sha256']
        root=self.base/label;package.unpack(archive,root,sha);return root
    def cli(self,code,python,*args):
        return subprocess.run([str(python),'-I','-B',str(code/'access.py'),*map(str,args)],
            capture_output=True,text=True,timeout=45,cwd=self.base)

    def test_deterministic_complete_archive_and_canonical_runtime_unchanged(self):
        other=self.base/'second.tar.gz';package.build(self.repo,other)
        self.assertEqual(self.archive.read_bytes(),other.read_bytes())
        code=self.install();release=package.verify(code)
        for name in ('README.md','requirements-cloudflare.txt',*('docs/'+n for n in package.DOCS)):
            self.assertTrue((code/name).is_file(),name)
        for original in (self.repo/'asc').rglob('*.py'):
            relative=original.relative_to(self.repo);self.assertEqual((code/relative).read_bytes(),original.read_bytes(),str(relative))
        self.assertEqual(release['kind'],'asc-linux-access')
        with self.assertRaises((ValueError,FileNotFoundError)):demo_package.verify(code)
        self.assertFalse((code/'release.json').exists())
        for path in code.rglob('*'):
            if path.is_file():self.assertEqual(path.stat().st_mode&0o777,0o600)
        before=self.archive.read_bytes()
        with self.assertRaises(ValueError):package.build(self.repo,self.archive)
        self.assertEqual(self.archive.read_bytes(),before)

    def test_actual_private_venv_no_global_packages_and_release_binding(self):
        code=self.install();env=self.base/'env';package.prepare_env(code,env)
        result=self.cli(code,env/'bin/python','verify');self.assertEqual(result.returncode,0,result.stderr)
        profile=self.base/'approved-profile.json';profile.write_text(json.dumps(dict(format=1,mode='private-gateway',
            frontend_origin='https://127.0.0.1:8445',upstream_origin='https://127.0.0.1:8444',
            upstream_pin='a'*64,upstream_mode='single-writer-demo',max_body_bytes=1024**2)));profile.chmod(0o600)
        state=self.base/'new-gateway-only'
        initialized=self.cli(code,env/'bin/python','gateway','--root',state,'init','--profile',profile)
        self.assertEqual(initialized.returncode,0,initialized.stderr);before=(state/'dashboard/server.crt').read_bytes()
        repeated=self.cli(code,env/'bin/python','gateway','--root',state,'init','--profile',profile)
        self.assertEqual(repeated.returncode,0,repeated.stderr);self.assertEqual((state/'dashboard/server.crt').read_bytes(),before)
        self.assertFalse((state/'controller.json').exists());self.assertFalse((state/'node.json').exists())
        no_jwt=subprocess.run([str(env/'bin/python'),'-I','-B','-c','import importlib.util;assert importlib.util.find_spec("jwt") is None'],capture_output=True)
        self.assertEqual(no_jwt.returncode,0)
        result=self.cli(code,env/'bin/python','edge','--root',self.base/'no-state','info')
        self.assertEqual(json.loads(result.stdout)['error'],'access_bundle_refused');self.assertFalse((self.base/'no-state').exists())
        newer=self.install('newer','0.1.1-internal')
        result=self.cli(newer,env/'bin/python','gateway','--root',self.base/'no-state','info')
        self.assertEqual(json.loads(result.stdout)['error'],'access_bundle_refused')
        with self.assertRaises(ValueError):package.prepare_env(code,env)
        receipt=json.loads((env/'access-env.json').read_text());receipt['python']=[0,0,0]
        (env/'access-env.json').write_text(json.dumps(receipt))
        result=self.cli(code,env/'bin/python','gateway','--root',self.base/'no-state','info')
        self.assertEqual(json.loads(result.stdout)['error'],'access_bundle_refused')

    def test_real_offline_hash_locked_edge_dependencies(self):
        self.assertTrue(PIP.is_file());self.assertTrue(WHEELS.is_dir())
        code=self.install();env=self.base/'edge-env';package.prepare_env(code,env,True,PIP,WHEELS)
        check=subprocess.run([str(env/'bin/python'),'-I','-B','-c',
            'import jwt,cryptography,cffi,pycparser;assert jwt.__version__=="2.15.1";assert cryptography.__version__=="50.0.2"'],capture_output=True)
        self.assertEqual(check.returncode,0,check.stderr)
        # No team keys fetched by info. This enters the existing CLI, which safely
        # refuses a missing root rather than a missing environment/dependency.
        result=self.cli(code,env/'bin/python','edge','--root',self.base/'absent','info')
        self.assertEqual(json.loads(result.stdout)['error'],'edge_origin_refused')

    def test_corrupt_wheel_cannot_create_complete_environment(self):
        code=self.install();wheels=self.base/'bad-wheels';shutil.copytree(WHEELS,wheels)
        wheel=next(wheels.glob('pyjwt-*.whl'));wheel.write_bytes(wheel.read_bytes()+b'test-owned hash corruption')
        env=self.base/'incomplete-env'
        with self.assertRaises(subprocess.CalledProcessError):package.prepare_env(code,env,True,PIP,wheels)
        self.assertTrue(env.is_dir());self.assertFalse((env/'access-env.json').exists())
        result=self.cli(code,env/'bin/python','gateway','--root',self.base/'absent','info')
        self.assertEqual(json.loads(result.stdout)['error'],'access_bundle_refused');self.assertFalse((self.base/'absent').exists())

    def test_checksum_existing_state_recovery_volume_and_link_refusals(self):
        with self.assertRaises(ValueError):package.unpack(self.archive,self.base/'bad-sha','0'*64)
        self.assertFalse((self.base/'bad-sha').exists())
        for index,marker in enumerate(('demo.json','RECOVERY_READ_ONLY.json','.asc-volume.json','gateway.json','backup-complete.json','install.json')):
            parent=self.base/('protected'+str(index));parent.mkdir(mode=0o700);(parent/marker).write_bytes(b'preserve')
            with self.assertRaises(ValueError):package.unpack(self.archive,parent/'forbidden',self.report['sha256'])
            self.assertEqual({p.name for p in parent.iterdir()},{marker})
            self.assertEqual((parent/marker).read_bytes(),b'preserve')
        link=self.base/'link';link.symlink_to(self.base,target_is_directory=True)
        with self.assertRaises(ValueError):package.unpack(self.archive,link/'forbidden',self.report['sha256'])
        existing=self.base/'existing';existing.mkdir(mode=0o700);sentinel=existing/'keep';sentinel.write_bytes(b'keep')
        with self.assertRaises(ValueError):package.unpack(self.archive,existing,self.report['sha256'])
        self.assertEqual(sentinel.read_bytes(),b'keep')
        with self.assertRaises(ValueError):package.build(self.repo,self.base/'protected0'/'not-code.tar.gz')
        self.assertEqual({p.name for p in (self.base/'protected0').iterdir()},{'demo.json'})

    def test_archive_paths_links_duplicates_missing_and_corrupt_bytes_never_extract(self):
        with tarfile.open(self.archive) as archive:
            original=[(entry,archive.extractfile(entry).read()) for entry in archive.getmembers()]
        for kind in ('traversal','symlink','duplicate','missing','corrupt','expanded'):
            bad=self.base/(kind+'.tar.gz')
            if kind=='expanded':bad.write_bytes(gzip.compress(b'\0'*(package.MAX_BYTES+1)))
            else:
                with tarfile.open(bad,'w:gz') as archive:
                    for entry,data in original:
                        if kind=='missing' and entry.name.endswith('/requirements-cloudflare.txt'):continue
                        if kind=='corrupt' and entry.name.endswith('/asc/access/gateway.py'):data+=b'corrupt';entry=tarfile.TarInfo(entry.name);entry.size=len(data);entry.mode=0o600
                        archive.addfile(entry,io.BytesIO(data))
                    if kind in ('traversal','symlink'):
                        extra=tarfile.TarInfo(package.PREFIX+('../escape.py' if kind=='traversal' else 'asc/alias.py'))
                        extra.mode=0o600
                        if kind=='symlink':extra.type=tarfile.SYMTYPE;extra.linkname='/tmp/never-followed'
                        archive.addfile(extra)
                    if kind=='duplicate':archive.addfile(original[0][0],io.BytesIO(original[0][1]))
            target=self.base/(kind+'-target')
            with self.subTest(kind=kind),self.assertRaises((ValueError,tarfile.TarError)):package.unpack(bad,target,hashlib.sha256(bad.read_bytes()).hexdigest())
            self.assertFalse(target.exists());self.assertFalse((self.base/'escape.py').exists())

    def test_installed_source_tamper_refused_before_profile_access(self):
        code=self.install();env=self.base/'env';package.prepare_env(code,env)
        source=code/'asc/access/gateway.py';source.write_bytes(source.read_bytes()+b'\n# untrusted modification\n')
        with self.assertRaises(ValueError):package.verify(code)
        result=self.cli(code,env/'bin/python','gateway','--root',self.base/'absent','init','--profile',self.base/'absent-profile')
        self.assertEqual(json.loads(result.stdout)['error'],'access_bundle_refused');self.assertFalse((self.base/'absent').exists())

    def test_operator_cli_unpack_prepare_verify_and_no_overwrite(self):
        code=self.base/'operator-code';tool=self.repo/'tools/package_access.py'
        command=[sys.executable,'-I','-B',str(tool),'unpack','--archive',str(self.archive),
            '--sha256',self.report['sha256'],'--destination',str(code)]
        first=subprocess.run(command,cwd=self.base,capture_output=True,text=True,timeout=15)
        self.assertEqual(first.returncode,0,first.stderr);self.assertFalse(json.loads(first.stdout)['identity_created'])
        before=(code/package.MANIFEST).read_bytes()
        again=subprocess.run(command,cwd=self.base,capture_output=True,text=True,timeout=15)
        self.assertNotEqual(again.returncode,0);self.assertEqual((code/package.MANIFEST).read_bytes(),before)
        env=self.base/'operator-env'
        result=self.cli(code,sys.executable,'prepare-env','--destination',env)
        self.assertEqual(result.returncode,0,result.stderr);self.assertFalse(json.loads(result.stdout)['runtime_started'])
        result=self.cli(code,env/'bin/python','verify');self.assertEqual(result.returncode,0,result.stderr)
