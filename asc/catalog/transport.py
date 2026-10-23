"""Bounded relay IO shared by jobs and owner download fallback."""
from contextlib import contextmanager
import hashlib
import time
from ..client import ClientError
from ..storage.client import StorageClient
from ..storage.volumes import CHUNK
from .common import CatalogError


class RelayReader:
    def __init__(self,stream,size,sha256,rate,deadline,purpose='transfer'):
        self.purpose=purpose
        self.stream,self.size,self.sha,self.rate,self.deadline=stream,size,sha256,rate,deadline
        self.count,self.digest,self.started=0,hashlib.sha256(),time.monotonic()

    def read(self,size):
        if time.time()>=self.deadline:
            raise CatalogError('job_timeout',408)
        chunk=self.stream.read1(min(size,CHUNK,self.size-self.count))
        if not chunk and self.count<self.size:
            raise CatalogError('source_interrupted',503)
        if time.time()>=self.deadline:raise CatalogError('job_timeout',408)
        self.count+=len(chunk);self.digest.update(chunk)
        delay=self.count/self.rate-(time.monotonic()-self.started)
        if delay>0:time.sleep(min(delay,CHUNK/self.rate))
        return chunk

    def finish(self):
        if self.count!=self.size or self.digest.hexdigest()!=self.sha:
            raise CatalogError('source_checksum_mismatch',422)


@contextmanager
def source_stream(client,file_id,size,sha256,rate,deadline,purpose='transfer'):
    # Reuse Phase 1.2A's pin-before-headers connection and fixed framing.
    conn=client._connection('GET','files/'+file_id+'/content')
    try:
        response=conn.getresponse()
        if response.status!=200:
            client._reply(response)
            raise CatalogError('source_unavailable',503)
        if response.getheader('Content-Length')!=str(size) or response.getheader('X-ASC-SHA256')!=sha256:
            raise CatalogError('source_metadata_mismatch',409)
        reader=RelayReader(response,size,sha256,rate,deadline,purpose)
        yield reader
        reader.finish()
    finally:
        conn.close()
