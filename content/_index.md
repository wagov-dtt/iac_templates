---
title: Home
---

# Overview

Initial goal is reducing cost/effort to run a security focused [Internal Developer Platform](https://internaldeveloperplatform.org) with a small team.

## Opinionated Rancher platforms

Below guides are to setup [Certified Kubernetes](https://www.cncf.io/training/certification/software-conformance/) on public cloud environments with:

- [Karpenter](https://karpenter.sh) to prefer spot nodes and revert to ondemand if they aren’t available
- [Longhorn ready nodes and NVMe disks](https://longhorn.io/docs/latest/references/settings/#create-default-disk-on-labeled-nodes)  with [best-effort data locality](https://longhorn.io/docs/latest/high-availability/data-locality/#data-locality-settings)
- [Traefik](https://doc.traefik.io/traefik/) and [LetsEncrypt](https://letsencrypt.org/getting-started/) with an [cert-manager (ACME)](https://cert-manager.io/docs/configuration/acme/#configuration)
- [Rancher](https://ranchermanager.docs.rancher.com/getting-started/overview) and [Fleet](https://fleet.rancher.io) for multi cluster admin, gitops and access mgmt.

## Install Guides

- Azure with [AKS Automatic](docs/kubernetes/azure-aks)
- TODO: AWS with [karpenter/eksctl](https://karpenter.sh/v1.0/getting-started/getting-started-with-karpenter/)
- TODO: GKE with [Autopilot](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview)
- TODO: OCI with [OKE](https://www.oracle.com/cloud/cloud-native/kubernetes-engine/features/)

## References
- [CNCF Landscape](https://landscape.cncf.io)
- [Internal Developer Platform](https://internaldeveloperplatform.org)
- [CISA Secure By Design Principles](https://www.cisa.gov/resources-tools/resources/secure-by-design)
- [DoD Platform One](https://p1.dso.mil)
