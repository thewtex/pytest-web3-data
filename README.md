# Pytest Web3 Data

[![PyPI - Version](https://img.shields.io/pypi/v/pytest-web3-data.svg)](https://pypi.org/project/pytest-web3-data)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-web3-data.svg)](https://pypi.org/project/pytest-web3-data)

-----

A pytest plugin to fetch test data from IPFS HTTP gateways during pytest execution.

**Table of Contents**

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

```console
pip install pytest-web3-data
```

## Usage

Let's say we want to store our testing data at `test/data/*`.

Optionally, first add `test/data/` to `.gitignore`.

Create example test data:

```console
mkdir -p test/data/staging/
echo 'hello world!' > ./test/data/staging/hello.txt
```

Upload the data to the [InterPlanetary File System (IPFS)](https://en.wikipedia.org/wiki/InterPlanetary_File_System).

One option is to use [web3.storage](https://web3.storage). Install [Node/NPM](https://nodejs.org/en/download/), and install the [w3 CLI](https://www.npmjs.com/package/@web3-storage/w3):


```console
npm install --location=global @web3-storage/w3
```

The set your upload token from [https://web3.storage](https://web3.storage):

```console
w3 token
# Paste in token from the web UI
```

Upload the testing data to IPFS:

```console
w3 put ./test/data/staging --name pytest-web3-data-example --hidden --no-wrap
```

This outputs a reference to the [Content Identifier (CID)](https://proto.school/anatomy-of-a-cid/01), e.g.:

```
# Packed 1 file (0.0MB)
# bafybeigvfmtttajzj5no3jt2xavkdncxy3xapw3rndvoxmao72vhwy4osu
⁂ Stored 1 file
⁂ https://w3s.link/ipfs/bafybeigvfmtttajzj5no3jt2xavkdncxy3xapw3rndvoxmao72vhwy4osu
```

When we create a test, e.g.:

```python
# content of test_usage.py
def test_usage(web3_data):
    assert web3_data.exists()
    assert (web3_data / 'hello.txt').read_text() == "hello world!\n"
```

We can reference our CID either with a flag:

```console
pytest --web3-data-dir=test/data/bafybeigvfmtttajzj5no3jt2xavkdncxy3xapw3rndvoxmao72vhwy4osu
```

or in the `pytest.ini` file:

```
# content of pytest.ini
[pytest]
web3_data_dir = test/data/bafybeigvfmtttajzj5no3jt2xavkdncxy3xapw3rndvoxmao72vhwy4osu
```

Enjoy! 😊

## License

`pytest-web3-data` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
