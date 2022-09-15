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

        retries = urllib3.util.Retry(total=15, backoff_factor=0.1)
        http = urllib3.PoolManager(retries=retries)
        def fetch_files(root_cid, output_dir, sub_dir):
            subdir_str = str(sub_dir)
            if subdir_str == '.':
                subdir_str = ''

            url = f"https://dweb.link/api/v0/ls?arg={root_cid}/{subdir_str}"
            response = http.request('GET', url)
            contents = json.loads(response.data.decode('utf-8'))
            for objects in contents['Objects']:
                for link in objects['Links']:
                  object_type = link['Type']
                  if object_type == 2:
                      file_name = link['Name']
                      file_path = sub_dir / file_name
                      url = f"https://{root_cid}.ipfs.w3s.link/{file_path}"
                      response = http.request('GET', url)
                      with open(output_dir / sub_dir / file_name, 'wb') as fp:
                          fp.write(response.data)
                  elif object_type == 1:
                      nested_dir = sub_dir / link['Name']
                      (output_dir / nested_dir).mkdir()
                      fetch_files(root_cid, output_dir, nested_dir)

        fetch_files(cid, web3_data_dir, PurePosixPath(''))
    except Exception as err:
        shutil.rmtree(web3_data_dir)
        raise err

    return web3_data_dir
