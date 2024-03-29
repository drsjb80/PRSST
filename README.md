[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=drsjb80_PRSST&metric=alert_status)](https://sonarcloud.io/dashboard?id=drsjb80_PRSST)

# PRSST
A simple Python RSS/Atom ticker, similar to JRSST.

## Installation
You'll need Python3 tkinter: https://stackoverflow.com/a/25905642

You'll also need to install three Python3 packages via:

    python3 -m pip install -r requirements.txt

### Arguments
- --feed or -f : specify one or more feed(s) directly
- --yaml or -y : specify one or more yaml file(s); these can contain font etc. information in addition to feeds.
If neither are found, PRSST looks for a .prsst.yml file in your home directory.

### YAML file format
```
feeds:
    - https://us-cert.cisa.gov/ncas/all.xml
font: Helvetica 14 normal roman
growright: False
delay: 10
```

If you get the following error on a Linux system:

    X Error of failed request:  BadLength (poly request too large or internal Xlib length error)

it is easiest, though a bit draconian, to remove a color emoji font:

    sudo apt remove fonts-noto-color-emoji
