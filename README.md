# prich Templates Repository  

This repository contains reusable templates for the [**prich** CLI tool](https://github.com/oleks-dev/prich), designed for easy sharing and installation.

---

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
