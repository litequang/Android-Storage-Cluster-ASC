"""Security boundary cases for the local IPC contract, no phone or server."""
import copy
import json
import unittest
from asc.bridge.contract import decode, request, Refused, MAX_FRAME


class BridgeContractTests(unittest.TestCase):
    def envelope(self):
        return dict(api_version=1,request_id='11111111-1111-4111-8111-111111111111',
                    app_id='22222222-2222-4222-8222-222222222222',authorization='a'*43,operation='status',params={})

    def test_duplicate_keys_invalid_encoding_nonfinite_and_frames_fail_closed(self):
        for raw in (b'{"x":1,"x":2}', b'{"n":NaN}', b'\xff', b'[]', b'{}'*MAX_FRAME, b''):
            with self.subTest(size=len(raw)), self.assertRaises(Refused):decode(raw)
        self.assertEqual(request(decode(json.dumps(self.envelope()).encode())),self.envelope())

    def test_version_aliases_and_unknown_fields_never_downgrade(self):
        for version in (True,1.0,0,2,'1'):
            value=self.envelope();value['api_version']=version
            with self.assertRaises(Refused):request(value)
        value=self.envelope();value['path']='/etc/passwd'
        with self.assertRaises(Refused):request(value)

    def test_shell_paths_pid_and_destructive_operations_are_not_capabilities(self):
        for op in ('exec','shell','init','gc','approve','promote','recover','controller_start'):
            value=self.envelope();value['operation']=op
            with self.assertRaises(Refused):request(value)
        for params in ({'pid':123},{'root':'/'},{'args':['sh']},{'command':'id'}):
            value=self.envelope();value['params']=params
            with self.assertRaises(Refused):request(value)

    def test_join_binding_and_explicit_replacement_have_strict_types(self):
        value=self.envelope();value.update(operation='quick_join',params=dict(controller='https://127.0.0.1:8443',
            pin='A'*64,cluster_id=value['app_id'],name='synthetic node',code='012345ABCDEF',replace_code=True))
        request(value)
        for field,invalid in (('controller','http://127.0.0.1:8443'),('controller','https://8.8.8.8:8443'),
                              ('pin','bad'),('cluster_id','other'),('name','a\n'),('replace_code',1),('code','not-a-code')):
            bad=copy.deepcopy(value);bad['params'][field]=invalid
            with self.assertRaises(Refused):request(bad)

    def test_errors_never_reflect_authorization_or_join_secret(self):
        value=self.envelope();value['operation']='secret arbitrary text'
        with self.assertRaises(Refused) as caught:request(value)
        self.assertEqual(str(caught.exception),'invalid_request')
        self.assertNotIn(value['authorization'],str(caught.exception))
