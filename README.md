[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=drsjb80_PRSST&metric=alert_status)](https://sonarcloud.io/dashboard?id=drsjb80_PRSST)

# PRSST
A simple Python RSS/Atom ticker, similar to JRSST.

### Arguments
- --feed or -f : specify one or more feed(s) directly
- --yaml or -y : specify one or more yaml file(s); these can contain font etc. information in addition to feeds.
If neither are found, PRSST looks for a .prsst.yml file in your home directory.

### YAML file format
```
feeds:
    - https://us-cert.cisa.gov/ncas/all.xml
font: Helvetica 14 normal roman
```
