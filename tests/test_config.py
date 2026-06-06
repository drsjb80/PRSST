"""Tests for configuration validation and loading."""
import tempfile
from pathlib import Path

import pytest
import yaml


def validate_test_config(config):
    """Validate configuration dictionary."""
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
    """Test that valid configuration passes validation."""
    config = {
        'feeds': ['https://example.com/feed.xml'],
        'delay': 10,
        'reload': 120,
        'growright': False,
    }
    assert validate_test_config(config) is True


def test_validate_config_missing_feeds():
    """Test that configuration without feeds fails validation."""
    config = {}
    assert validate_test_config(config) is False


def test_validate_config_empty_feeds_list():
    """Test that configuration with empty feeds list fails validation."""
    config = {'feeds': []}
    assert validate_test_config(config) is False


def test_validate_config_feeds_not_list():
    """Test that configuration with non-list feeds fails validation."""
    config = {'feeds': 'not a list'}
    assert validate_test_config(config) is False


def test_validate_config_negative_delay():
    """Test that configuration with negative delay fails validation."""
    config = {
        'feeds': ['https://example.com/feed.xml'],
        'delay': -5,
    }
    assert validate_test_config(config) is False


def test_validate_config_zero_delay():
    """Test that configuration with zero delay fails validation."""
    config = {
        'feeds': ['https://example.com/feed.xml'],
        'delay': 0,
    }
    assert validate_test_config(config) is False


def test_validate_config_invalid_growright_type():
    """Test that configuration with non-boolean growright fails validation."""
    config = {
        'feeds': ['https://example.com/feed.xml'],
        'growright': 'yes',
    }
    assert validate_test_config(config) is False


def test_load_yaml_file():
    """Test loading configuration from a YAML file."""
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
        with open(temp_path, encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        assert loaded['feeds'] == yaml_content['feeds']
        assert loaded['delay'] == 20
        assert loaded['reload'] == 180
    finally:
        Path(temp_path).unlink()


def test_yaml_invalid_format():
    """Test that invalid YAML raises an error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write('feeds: [invalid yaml: [')
        temp_path = f.name

    try:
        with pytest.raises(yaml.YAMLError):
            with open(temp_path, encoding='utf-8') as f:
                yaml.safe_load(f)
    finally:
        Path(temp_path).unlink()
