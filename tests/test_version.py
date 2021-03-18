from crystal import __version__
import os
import re


def test_version_is_expected_value():
    assert __version__ == '1.1.0b'


def test_version_in_pyproject_toml_is_consistent_with_package_version():
    pyproject_toml_filepath = os.path.join(
        os.path.dirname(__file__), '..', 'pyproject.toml')
    with open(pyproject_toml_filepath, 'r') as f:
        pyproject_toml = f.read()
    m = re.search(r'\nversion *= *"([^"]+)"\n', pyproject_toml)
    assert m is not None, 'Unable to find version in pyproject.toml'
    pyproject_toml_version = m.group(1)
    assert __version__ == pyproject_toml_version
