  #!/bin/bash
  # Only arg should be FQDN for rancher
  curl -sfL https://get.k3s.io | sh -
  kubectl create namespace cattle-system
  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
  helm repo add rancher-stable https://releases.rancher.com/server-charts/stable
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=120s
  helm install rancher rancher-stable/rancher --namespace cattle-system --set hostname=$1