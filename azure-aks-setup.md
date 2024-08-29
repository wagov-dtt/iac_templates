# Opinionated AKS setup (Cilium, Longhorn, local NVMe)

To get maximum price/performance ration, the below establishes an AKS cluster using spot instances (some can be reserved for stability), and Cilium networking.

## Setup using AKS Automatic

Create a cluster using [AKS Automatic](https://learn.microsoft.com/en-us/azure/aks/intro-aks-automatic). Connect to the cluster using cloud shell, and run the below bootstrap to configure kubernetes (see [`nodes.yaml`](bootstrap_k8s/config/nodes.yaml) for instance/headroom defaults):

```bash
# Setup nodes and install rancher
RANCHER_HOSTNAME=rancher01.cool.domain python bootstrap_k8s.pyz
kubectl get services # this will show the IP that dns for your domain needs to be pointed at
```

## Backup to azure blob storage acct

## Add more clusters

```bash
# Setup nodes and register with existing rancher
```
