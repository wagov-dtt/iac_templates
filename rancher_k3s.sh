#!/bin/bash

# Usage: ./rancher_k3s.sh <rancher_fqdn>

[ $# -eq 0 ] && { echo "Usage: $0 <rancher_fqdn>"; exit 1; }
RANCHER_FQDN=$1

curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=v1.28 sh -
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

kubectl create namespace cattle-system
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm repo add rancher-stable https://releases.rancher.com/server-charts/stable

kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=120s

helm install rancher rancher-stable/rancher --namespace cattle-system --set hostname=$RANCHER_FQDN

get_bootstrap_password() {
    kubectl get secret -n cattle-system bootstrap-secret -o go-template='{{.data.bootstrapPassword|base64decode}}'
}

for i in {1..5}; do
    BOOTSTRAP_PASSWORD=$(get_bootstrap_password)
    [ -n "$BOOTSTRAP_PASSWORD" ] && { echo "https://$RANCHER_FQDN/dashboard/?setup=$BOOTSTRAP_PASSWORD"; exit 0; }
    echo "Attempt $i: Waiting for bootstrap secret..."
    sleep 10
done

echo "Error: Bootstrap secret not found after 5 attempts."
exit 1