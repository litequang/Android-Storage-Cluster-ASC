"""Owner-pinned network source; frozen metadata is never storage authority."""
from contextlib import contextmanager
import time
from .format import fail
from ..catalog.transport import source_stream
from ..storage.client import StorageClient


class PinnedSource:
    def __init__(self, owner): self.owner=owner

    def capture(self):
        view=self.owner.request('POST','external/capture',{})['capture']
        # Full manifest validation will bind checkpoint/document on engine capture.
        return view

    def streams(self,file,manifest):
        plan=self.owner.request('POST','external/read',{'cluster_id':manifest['cluster_id'],
            'epoch':manifest['epoch'],'file':file})
        for candidate in plan['candidates']:
            yield lambda c=candidate:self._stream(c,file)

    @staticmethod
    @contextmanager
    def _stream(candidate,file):
        client=StorageClient(candidate['origin'],candidate['pin'],candidate['grant'],candidate['volume_id'],
                             timeout=candidate['timeout'])
        with source_stream(client,candidate['local_file_id'],file['size'],file['sha256'],
                           candidate['rate'],time.time()+candidate['timeout']) as stream:
            yield stream

    def revalidate(self,manifest):
        result=self.owner.request('POST','external/check',{'cluster_id':manifest['cluster_id'],
            'epoch':manifest['epoch'],'source_index':manifest['source_index']})
        if result.get('current_authority') is not True:fail('external_authority_unconfirmed',503)
