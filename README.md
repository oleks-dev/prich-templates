# prich Templates Repository  

[![Used by prich](https://img.shields.io/badge/used%20by-prich-blue?logo=github)](https://github.com/oleks-dev/prich)

This repository contains reusable templates for the [**prich** CLI tool](https://github.com/oleks-dev/prich), designed for easy sharing and installation.

---

See [Prich Templates List](https://github.com/oleks-dev/prich-templates/blob/main/templates/index.md)

## List Available Templates

To list available remote templates from this repository, run:
```commandline
prich templates-repo
```

## Installing a Template

Use `template_id` from the list above and install it with the `-r` or `--remote` flag:
```commandline
prich install <template_id> -r
```
This will download the corresponding archive from the remote templates repo and extract it locally. 

## Contributing
Want to share your own template?
Feel free to open a pull request or suggest a new template idea!
