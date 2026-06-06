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
    entry = {'title': 'Test Article'}
    assert extract_entry_text(entry) == 'Test Article'


def test_extract_title_with_html():
    entry = {'title': 'Test <b>Article</b> Title'}
    assert extract_entry_text(entry) == 'Test Article Title'


def test_extract_title_with_entities():
    entry = {'title': 'Test &amp; Article'}
    assert extract_entry_text(entry) == 'Test & Article'


def test_extract_description_fallback():
    entry = {'description': 'This is a longer description text'}
    assert extract_entry_text(entry) == 'This is a longer description text'


def test_truncate_long_description():
    long_text = 'A' * 70
    entry = {'description': long_text}
    result = extract_entry_text(entry)
    assert result == 'A' * 60 + '...'
    assert len(result) == 63


def test_missing_both_title_and_description():
    entry = {}
    assert extract_entry_text(entry) == "(No title or description)"


def test_empty_title_uses_description():
    entry = {'title': '', 'description': 'Fallback text'}
    assert extract_entry_text(entry) == 'Fallback text'


def test_none_values_handled():
    entry = {'title': None, 'description': 'Description text'}
    assert extract_entry_text(entry) == 'Description text'


def test_complex_html_stripping():
    entry = {'title': '<a href="url">Link <b>text</b></a>'}
    assert extract_entry_text(entry) == 'Link text'
