import os
import tempfile
import yaml
from pathlib import Path
from subprocess import run

cluster_name = os.environ.get("CLUSTER_NAME", "eks01")
region = os.environ.get("AWS_REGION", "ap-southeast-2")
tags = os.environ.get("TAGS", "environment=dev,project=demo")
node_groups = os.environ.get("NODE_GROUPS", "base:2,scale-spot:1")
instance_type = os.environ.get("INSTANCE_TYPE", "i4i.2xlarge")

def install_tools():
    run("""
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"; chmod +x kubectl
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    curl -LO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz"; tar -xzf eksctl_*.tar.gz
    """, shell=True)

def parse_node_groups(node_groups_str):
    node_groups = []
    for group in node_groups_str.split(','):
        name, size = group.split(':')
        ng = {
            "name": name,
            "instanceType": instance_type,
            "desiredCapacity": int(size),
            "disableIMDSv1": True,
            "amiFamily": "Ubuntu2204",
            "maxPodsPerNode": 600,
            "preBootstrapCommands": ["setup-local-disks raid0", "apt-get -y update && apt-get -y install open-iscsi"]
        }
        if name.endswith('-spot'):
            ng["spot"] = True
        node_groups.append(ng)
    return node_groups

def generate_config(temp_dir):
    config = {
        "apiVersion": "eksctl.io/v1alpha5",
        "kind": "ClusterConfig",
        "metadata": {
            "name": cluster_name,
            "region": region,
            "tags": {tag.split('=')[0]: tag.split('=')[1] for tag in tags.split(',')}
        },
        "addons": [{"name": "vpc-cni"}, {"name": "coredns"}, {"name": "kube-proxy"}],
        "managedNodeGroups": parse_node_groups(node_groups),
        "kubernetesNetworkConfig": {"ipFamily": "IPv6"},
        "iam": {"withOIDC": True}
    }

    config_path = Path(temp_dir) / "cluster-config.yaml"
    yaml.dump(config)
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path

def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        install_tools()
        run(f"PATH={temp_dir}:$PATH eksctl create cluster -f {generate_config(temp_dir)}", shell=True)

if __name__ == "__main__":
    main()