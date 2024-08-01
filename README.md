# Infrastructure as Code templates

Some convenient quick starts for use in cloud shells

[![Open Azure Cloud Shell](https://aka.ms/deploytoazurebutton)](https://shell.azure.com/bash)

Below will setup a resource group `$NAME` and a rancher vm `$NAME-rancher` accessible from the internet. See the [`rancher_k3s.sh`](rancher_k3s.sh) for the script which should run on any linux server that supports [k3s](https://docs.k3s.io/installation/requirements#operating-systems).

```bash
curl -sL https://raw.githubusercontent.com/adonm/iac_templates/main/azure_rancher_k3s.py | python3 - $NAME
```