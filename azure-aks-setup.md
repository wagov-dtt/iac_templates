# Opinionated AKS setup (Cilium, Longhorn, local NVMe)

To get maximum price/performance ration, the below establishes an AKS cluster using spot instances (some can be reserved for stability), and Cilium networking.

## Setup using AKS Automatic

Create a cluster using [AKS Automatic](https://learn.microsoft.com/en-us/azure/aks/intro-aks-automatic) to get all the good defaults, then switch it to a standard sku (`Switch to Standard Cluster` in portal) and create a nodepool of local instances storage vms to enable longhorn spdk well.

## Longhorn focused node pool

Add node pool as follows:

- 3 nodes
- kubernetes.azure.com/os-sku:Ubuntu
- node.kubernetes.io/instance-type:Standard_L8as_v3
- kubernetes.azure.com/ebpf-dataplane:cilium

