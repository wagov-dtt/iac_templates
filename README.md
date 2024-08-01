# Infrastructure as Code templates

Some convenient quick starts for use in cloud shells

[![Open Azure Cloud Shell](https://aka.ms/deploytoazurebutton)](https://shell.azure.com/bash)

Below will setup a resource group `$NAME` and a rancher vm `$NAME-rancher` accessible from the internet.

```bash
curl -sL https://raw.githubusercontent.com/adonm/iac_templates/main/azure_rancher_k3s.py | python3 - $NAME
```
