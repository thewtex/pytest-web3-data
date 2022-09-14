from pathlib import Path

def test_example(web3_data: Path):
    assert web3_data.exists()

    assert (web3_data / 'README.md').exists()
    assert (web3_data / 'README.md').read_text() == 'Test data for [pytest-web3-data](https://github.com/thewtex/pytest-web3-data).\n'

    assert (web3_data / 'numfocus' / 'NF10-2012-2022.svg').exists()
    assert (web3_data / 'web3-storage' / 'logo.svg').exists()
    assert (web3_data / 'web3-storage' / 'logo-dark.svg').exists()