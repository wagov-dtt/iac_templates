#!/usr/bin/env python3
"""
This script installs K3s and Rancher on a system (tested on Debian 12), configuring necessary parameters and dependencies.
"""

import os
import sys
from pathlib import Path
from subprocess import run, call

def increase_limits():
    """
    Increase system limits for inotify instances, watches, and memory mappings.
    Writes new limits to a sysctl configuration file and applies the changes.
    """
    sysctl_params = """
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches = 524288
vm.max_map_count = 262144
"""
    Path("/etc/sysctl.d/99-k3s-densepod.conf").write_text(sysctl_params.strip())
    call(["sysctl", "--system"])

def main(rancher_fqdn, password):
    """
    Main function to install and configure K3s and Rancher. Based on https://ranchermanager.docs.rancher.com/getting-started/quick-start-guides/deploy-rancher-manager/helm-cli 

    Args:
        rancher_fqdn (str): Fully Qualified Domain Name for Rancher
        password (str): Bootstrap password for Rancher

    This function performs the following steps:
    1. Increases system limits
    2. Installs K3s
    3. Sets up Helm
    4. Installs cert-manager
    5. Installs Rancher
    """
    if rancher_fqdn == "sslip.io":
        rancher_fqdn = run("dig @ns.sslip.io txt ip.sslip.io +short -4", shell=True, text=True, capture_output=True).stdout.replace('"', "").strip() + ".sslip.io"
    increase_limits()
    call('curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=v1.28 INSTALL_K3S_EXEC="--kubelet-arg=max-pods=900" sh -', shell=True)
    os.environ["KUBECONFIG"] = "/etc/rancher/k3s/k3s.yaml"
    call("curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash", shell=True)
    call(["helm", "repo", "add", "jetstack", "https://charts.jetstack.io", "--force-update"])
    call(["helm", "install", "cert-manager", "jetstack/cert-manager", "--namespace", "cert-manager", "--create-namespace", "--set", "crds.enabled=true"])
    call(["sleep", "30"])
    call(["helm", "repo", "add", "rancher-stable", "https://releases.rancher.com/server-charts/stable"])
    call(["helm", "install", "rancher", "rancher-stable/rancher", "--namespace", "cattle-system", "--create-namespace",
         "--set", f"hostname={rancher_fqdn}", "--set", f"bootstrapPassword={password}", "--set", "ingress.tls.source=letsEncrypt",
         "--set", f"letsEncrypt.email=admin@{rancher_fqdn}", "--set", "letsEncrypt.ingress.class=traefik"])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: sudo python3 script.py <rancher_fqdn> <password>")
    main(sys.argv[1], sys.argv[2])