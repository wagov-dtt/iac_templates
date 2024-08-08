#!/usr/bin/env bash

set -euo pipefail

usage() {
    echo "Usage: $0 <rancher_fqdn>"
    exit 1
}

increase_limits() {
    local sysctl_params=(
        "fs.inotify.max_user_instances=524288"
        "fs.inotify.max_user_watches=524288"
        "fs.file-max=2097152"
    )

    local limits_params=(
        "* soft nofile 1048576"
        "* hard nofile 1048576"
        "root soft nofile 1048576"
        "root hard nofile 1048576"
    )

    printf '%s\n' "${sysctl_params[@]}" | sudo tee -a /etc/sysctl.conf > /dev/null
    sudo sysctl -p

    ulimit -n 1048576

    printf '%s\n' "${limits_params[@]}" | sudo tee -a /etc/security/limits.conf > /dev/null

    sudo sysctl --system
}

install_k3s() {
    curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=v1.28 INSTALL_K3S_EXEC="--kubelet-arg=max-pods=10000" sh -
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
}

install_helm() {
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
}

install_cert_manager() {
    helm repo add jetstack https://charts.jetstack.io --force-update
    helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set crds.enabled=true
    sleep 30
}

install_rancher() {
    local rancher_fqdn=$1
    local bootstrap_password=$2

    helm repo add rancher-stable https://releases.rancher.com/server-charts/stable
    helm install rancher rancher-stable/rancher \
        --namespace cattle-system \
        --create-namespace \
        --set hostname="$rancher_fqdn" \
        --set bootstrapPassword="$bootstrap_password" \
        --set ingress.tls.source=letsEncrypt \
        --set letsEncrypt.email="admin@$rancher_fqdn" \
        --set letsEncrypt.ingress.class=traefik
    sleep 30
}

main() {
    [[ $# -eq 0 ]] && usage

    local rancher_fqdn=$1
    local bootstrap_password
    bootstrap_password=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 16 | head -n 1)

    increase_limits
    install_k3s
    install_helm
    install_cert_manager
    install_rancher "$rancher_fqdn" "$bootstrap_password"

    echo "Rancher installed at: https://$rancher_fqdn/dashboard/?setup=$bootstrap_password"
}

main "$@"