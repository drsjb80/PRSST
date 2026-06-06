"""Tests for entry text extraction and formatting."""
# pylint: disable=duplicate-code
import re
import html


def extract_entry_text(entry):
    """Extract displayable text from an RSS/Atom entry.

    Returns text from title, or description if no title, or a placeholder.
    Strips HTML tags and unescapes HTML entities.
    """
    text = None
    if 'title' in entry and entry['title']:
        text = re.sub(r'<[^<>]+?>', r'', entry['title'])
    elif 'description' in entry and entry['description']:
        text = entry['description']
        if len(text) > 60:
            text = text[:60] + '...'
    else:
        text = "(No title or description)"

    return html.unescape(text)


def test_extract_title():
    """Test extracting title from entry."""
    entry = {'title': 'Test Article'}
    assert extract_entry_text(entry) == 'Test Article'


def test_extract_title_with_html():
    """Test extracting title with HTML tags."""
    entry = {'title': 'Test <b>Article</b> Title'}
    assert extract_entry_text(entry) == 'Test Article Title'


def test_extract_title_with_entities():
    """Test extracting title with HTML entities."""
    entry = {'title': 'Test &amp; Article'}
    assert extract_entry_text(entry) == 'Test & Article'


def test_extract_description_fallback():
    """Test using description when title is missing."""
    entry = {'description': 'This is a longer description text'}
    assert extract_entry_text(entry) == 'This is a longer description text'


def test_truncate_long_description():
    """Test truncating long descriptions."""
    long_text = 'A' * 70
    entry = {'description': long_text}
    result = extract_entry_text(entry)
    assert result == 'A' * 60 + '...'
    assert len(result) == 63


def test_missing_both_title_and_description():
    """Test placeholder when both title and description are missing."""
    entry = {}
    assert extract_entry_text(entry) == "(No title or description)"


def test_empty_title_uses_description():
    """Test using description when title is empty."""
    entry = {'title': '', 'description': 'Fallback text'}
    assert extract_entry_text(entry) == 'Fallback text'


def test_none_values_handled():
    """Test handling None values in title."""
    entry = {'title': None, 'description': 'Description text'}
    assert extract_entry_text(entry) == 'Description text'


def test_complex_html_stripping():
    """Test stripping complex HTML tags from text."""
    entry = {'title': '<a href="url">Link <b>text</b></a>'}
    assert extract_entry_text(entry) == 'Link text'
