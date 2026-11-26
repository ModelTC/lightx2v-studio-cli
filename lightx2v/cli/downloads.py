"""Authenticated origin requests and credential-free external media delivery."""
from __future__ import annotations
import hashlib
from urllib.parse import urljoin, urlsplit
import httpx


def stream_original(config, url, destination):
    origin=urlsplit(config.base_url)
    url=urljoin(config.base_url+'/',url)
    with httpx.Client(timeout=120,follow_redirects=False) as downloader:
        for _ in range(6):
            target=urlsplit(url)
            if target.scheme not in {'https','http'} or target.username or target.password:
                raise ValueError('Invalid download URL')
            same=(target.scheme,target.netloc)==(origin.scheme,origin.netloc)
            headers={'Authorization':'Bearer '+config.api_key} if same else {}
            with downloader.stream('GET',url,headers=headers) as response:
                if response.status_code in {301,302,303,307,308}:
                    following=urljoin(url,response.headers['location'])
                    if target.scheme=='https' and urlsplit(following).scheme!='https':
                        raise ValueError('Insecure download redirect')
                    url=following
                    continue
                response.raise_for_status()
                digest=hashlib.sha256();size=0
                for chunk in response.iter_bytes():
                    destination.write(chunk);digest.update(chunk);size+=len(chunk)
                return {'sha256':digest.hexdigest(),'size':size}
    raise ValueError('Too many download redirects')
