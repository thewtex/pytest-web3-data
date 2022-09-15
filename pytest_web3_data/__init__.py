# SPDX-FileCopyrightText: 2022-present NumFOCUS <info@numfocus.org>
#
# SPDX-License-Identifier: MIT

from pathlib import PurePosixPath, Path
import json
import shutil

import pytest
from cid import make_cid
import urllib3

def pytest_addoption(parser):
    group = parser.getgroup('web3-data')
    group.addoption(
      '--web3-data-dir',
      action='store',
      dest='web3_data_dir',
      help='Set the path to the IPFS test data directory with the format f"path/to/{cid}"',
    )

    parser.addini('web3_data_dir', 'default value for --web3-data-dir', 'string')


@pytest.fixture
def web3_data(request):
    web3_data_dir = request.config.getoption("web3_data_dir")
    if not web3_data_dir:
        web3_data_dir = request.config.getini("web3_data_dir")
    if not web3_data_dir:
        raise RuntimeError("web3_data_dir not set. Use --web3-data-dir or the web3_data_dir pytest.ini entry")

    web3_data_dir = Path(web3_data_dir).resolve()

    if not web3_data_dir.parent.exists():
        web3_data_dir.parent.mkdir(parents=True)

    if web3_data_dir.exists():
        return web3_data_dir

    cid = web3_data_dir.stem   
    try:
        make_cid(cid)
    except ValueError:
        raise ValueError('The last directory in the web3_data_dir should be a valid CID')

    try:
        web3_data_dir.mkdir(exist_ok=True)

        http = urllib3.PoolManager()
        have_local_ipfs_daemon = False
        try:
            response = http.request('GET', 'http://localhost:8080/ipfs/QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG/readme')
            if response.status == 200:
                have_local_ipfs_daemon = True
        except urllib3.exceptions.MaxRetryError:
            pass

        retries = urllib3.util.Retry(total=15, backoff_factor=0.1)
        http = urllib3.PoolManager(retries=retries)

        def ls_ipfs_dir_local(root_cid, subdir_str):
            url = f"http://localhost:8080/api/v0/ls?arg={root_cid}/{subdir_str}"
            response = http.request('GET', url)
            return json.loads(response.data.decode('utf-8'))
        def ls_ipfs_dir_remote(root_cid, subdir_str):
            url = f"https://dweb.link/api/v0/ls?arg={root_cid}/{subdir_str}"
            response = http.request('GET', url)
            return json.loads(response.data.decode('utf-8'))

        def dl_ipfs_file_local(file_name, sub_dir, root_cid, output_dir):
            file_path = sub_dir / file_name
            url = f"http://localhost:8080/ipfs/{root_cid}/{file_path}"
            response = http.request('GET', url, preload_content=False)
            with open(output_dir / sub_dir / file_name, 'wb') as fp:
                for chunk in response.stream():
                    fp.write(chunk)
            response.release_conn()
        def dl_ipfs_file_remote(file_name, sub_dir, root_cid, output_dir):
            file_path = sub_dir / file_name
            url = f"https://{root_cid}.ipfs.w3s.link/{file_path}"
            response = http.request('GET', url, preload_content=False)
            with open(output_dir / sub_dir / file_name, 'wb') as fp:
                for chunk in response.stream():
                    fp.write(chunk)
            response.release_conn()

        if have_local_ipfs_daemon:
            ls_ipfs_dir = ls_ipfs_dir_local
            dl_ipfs_file = dl_ipfs_file_local
        else:
            ls_ipfs_dir = ls_ipfs_dir_remote
            dl_ipfs_file = dl_ipfs_file_remote
        
        def fetch_files(root_cid, output_dir, sub_dir):
            subdir_str = str(sub_dir)
            if subdir_str == '.':
                subdir_str = ''

            contents = ls_ipfs_dir(root_cid, subdir_str)
            for objects in contents['Objects']:
                for link in objects['Links']:
                  object_type = link['Type']
                  if object_type == 2:
                      file_name = link['Name']
                      dl_ipfs_file(file_name, sub_dir, root_cid, output_dir)
                  elif object_type == 1:
                      nested_dir = sub_dir / link['Name']
                      (output_dir / nested_dir).mkdir()
                      fetch_files(root_cid, output_dir, nested_dir)

        fetch_files(cid, web3_data_dir, PurePosixPath(''))
    except Exception as err:
        shutil.rmtree(web3_data_dir)
        raise err

    return web3_data_dir
