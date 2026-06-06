[![Pylint](https://github.com/drsjb80/PRSST/actions/workflows/pylint.yml/badge.svg)](https://github.com/drsjb80/PRSST/actions/workflows/pylint.yml)
[![Pytest](https://github.com/drsjb80/PRSST/actions/workflows/pytest.yml/badge.svg)](https://github.com/drsjb80/PRSST/actions/workflows/pytest.yml)

# PRSST
A simple Python RSS/Atom ticker, similar to JRSST.

## Installation

You'll need Python 3.10+ with tkinter: https://stackoverflow.com/a/25905642

Install dependencies:

    python3 -m pip install -r requirements.txt

## Running

Start the ticker:

    python3 prsst/main.py

### Command-line Arguments

- `-f`, `--feed` : Specify one or more RSS/Atom feed URLs directly
- `-y`, `--yaml` : Specify one or more YAML configuration file(s)

If no arguments are provided, PRSST looks for `~/.prsst.yml`.

### Configuration

You can configure PRSST via a YAML file (`~/.prsst.yml` or specified via `-y` flag).

**Configuration options:**

- `feeds` (list): RSS/Atom feed URLs to display
- `delay` (int): Milliseconds between ticker updates (default: 10)
- `reload` (int): Seconds between feed refreshes (default: 120)
- `growright` (bool): Grow window to the right when new items arrive (default: false)
- `font-family` (string): Font name (e.g., "Helvetica")
- `font-size` (int): Font size in points
- `font-weight` (string): Font weight ("normal" or "bold")
- `font-slant` (string): Font slant ("roman" or "italic")

**Example YAML:**

```yaml
feeds:
  - https://us-cert.cisa.gov/ncas/all.xml
  - https://krebsonsecurity.com/feed/
delay: 10
reload: 120
growright: false
font-family: Helvetica
font-size: 14
font-weight: normal
font-slant: roman
```

You can also change the font via the Settings menu while the ticker is running.

## Troubleshooting

### Linux: "BadLength" X11 Error

If you get this error on Linux:

```
X Error of failed request:  BadLength (poly request too large or internal Xlib length error)
```

This is typically caused by emoji fonts. Remove the problematic font:

```bash
sudo apt remove fonts-noto-color-emoji
```
