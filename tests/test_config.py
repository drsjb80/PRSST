import tempfile
from pathlib import Path

import pytest
import yaml


# Minimal config validation function for testing
def validate_test_config(config):
    if 'feeds' not in config or not config['feeds']:
        return False
    if not isinstance(config['feeds'], list):
        return False
    if 'delay' in config and (not isinstance(config['delay'], int) or config['delay'] <= 0):
        return False
    if 'reload' in config and (not isinstance(config['reload'], int) or config['reload'] <= 0):
        return False
    if 'growright' in config and not isinstance(config['growright'], bool):
        return False
    return True


def test_validate_config_valid():
    config = {
        'feeds': ['https://example.com/feed.xml'],
        'delay': 10,
        'reload': 120,
        'growright': False,
    }
    assert validate_test_config(config) is True


def test_validate_config_missing_feeds():
    config = {}
    assert validate_test_config(config) is False


def test_validate_config_empty_feeds_list():
    config = {'feeds': []}
    assert validate_test_config(config) is False


def test_validate_config_feeds_not_list():
    config = {'feeds': 'not a list'}
    assert validate_test_config(config) is False


def test_validate_config_negative_delay():
    config = {
        'feeds': ['https://example.com/feed.xml'],
        'delay': -5,
    }
    assert validate_test_config(config) is False


def test_validate_config_zero_delay():
    config = {
        'feeds': ['https://example.com/feed.xml'],
        'delay': 0,
    }
    assert validate_test_config(config) is False


def test_validate_config_invalid_growright_type():
    config = {
        'feeds': ['https://example.com/feed.xml'],
        'growright': 'yes',
    }
    assert validate_test_config(config) is False


def test_load_yaml_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml_content = {
            'feeds': [
                'https://example.com/feed1.xml',
                'https://example.com/feed2.xml',
            ],
            'delay': 20,
            'reload': 180,
        }
        yaml.dump(yaml_content, f)
        temp_path = f.name

    try:
        with open(temp_path) as f:
            loaded = yaml.safe_load(f)
        assert loaded['feeds'] == yaml_content['feeds']
        assert loaded['delay'] == 20
        assert loaded['reload'] == 180
    finally:
        Path(temp_path).unlink()


def test_yaml_invalid_format():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write('feeds: [invalid yaml: [')
        temp_path = f.name

    try:
        with pytest.raises(yaml.YAMLError):
            with open(temp_path) as f:
                yaml.safe_load(f)
    finally:
        Path(temp_path).unlink()
