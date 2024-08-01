#!/bin/bash

# Usage: ./rancher_k3s.sh <rancher_fqdn>

[ $# -eq 0 ] && { echo "Usage: $0 <rancher_fqdn>"; exit 1; }
RANCHER_FQDN=$1
BOOTSTRAP_PASSWORD=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 16 | head -n 1)

curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=v1.28 sh -
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

helm repo add jetstack https://charts.jetstack.io --force-update
helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set crds.enabled=true
sleep 10
helm repo add rancher-stable https://releases.rancher.com/server-charts/stable
helm install rancher rancher-stable/rancher --namespace cattle-system --create-namespace --set hostname=$RANCHER_FQDN --set bootstrapPassword=$BOOTSTRAP_PASSWORD --set ingress.tls.source=letsEncrypt --set letsEncrypt.email=admin@$RANCHER_FQDN --set letsEncrypt.ingress.class=traefik
sleep 10
echo "Rancher installed at: https://$RANCHER_FQDN/dashboard/?setup=$BOOTSTRAP_PASSWORD"