---
title: Azure AKS Automatic
---

# Opinionated AKS setup (Cilium, Longhorn, local NVMe)

To get maximum price/performance ration, the below establishes an AKS cluster using spot instances (some can be reserved for stability), and Cilium networking.

## Setup using AKS Automatic

Create a cluster using [AKS Automatic](https://learn.microsoft.com/en-us/azure/aks/intro-aks-automatic). 

```bash
# Create an AKS Automatic cluster from azure cloud shell
export RG=rancher01 NAME=rancher01
az extension add --name aks-preview
az group create --name $RG --location australiaeast
az aks create --resource-group $RG --name $NAME --sku automatic
az aks get-credentials --resource-group $RG --name $NAME --overwrite-existing
```

The above steps can also be done in the [Azure portal](https://learn.microsoft.com/en-us/azure/aks/learn/quick-kubernetes-automatic-deploy?pivots=azure-portal) if preferred.

Connect to the cluster using cloud shell, and run the [bootstrap](https://github.com/wagov-dtt/site-reliability-engineering/blob/main/static/bootstrap_k8s/__main__.py) to configure kubernetes. If `RANCHER_FQDN` env var is configured the bootstrap will also install Rancher.

```bash
# Setup nodes
kubectl get nodes
curl -LO https://sre.radk8s.net/bootstrap_k8s.pyz
python bootstrap_k8s.pyz
# Can also setup DNS explicitly instead of using sslip.io, just point it to the same ingress IP
export RANCHER_FQDN=$(kubectl get services -n kube-system traefik -o jsonpath='{.status.loadBalancer.ingress[0].ip}').sslip.io
python bootstrap_k8s.pyz
# Grab url for initial rancher login/setup
echo https://$RANCHER_FQDN/dashboard/?setup=$(kubectl get secret --namespace cattle-system bootstrap-secret -o go-template='{{.data.bootstrapPassword|base64decode}}')
```

## Backup to azure blob storage acct

## Add more clusters

In rancher, under Cluster Management click Import Existing and copy the `kubectl apply -f ...yaml` command. Then use azure cli to provision another cluster and register it with the kubectl command like below.

```bash
unset RANCHER_FQDN
export RG=rancher01 NAME=rancher02
az aks create --resource-group $RG --name $NAME --sku automatic
```

The above steps can also be done in the [Azure portal](https://learn.microsoft.com/en-us/azure/aks/learn/quick-kubernetes-automatic-deploy?pivots=azure-portal) if preferred.

```bash
# Setup nodes and register with existing rancher
az aks get-credentials --resource-group $RG --name $NAME --overwrite-existing
curl -LO https://sre.radk8s.net/bootstrap_k8s.pyz
python bootstrap_k8s.pyz
kubectl apply -f ...yaml
```
