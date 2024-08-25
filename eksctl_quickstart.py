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
rancher_fqdn = os.environ.get("RANCHER_FQDN", False)


def install_tools():
    run(
        """
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"; chmod +x kubectl
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    curl -LO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz"; tar -xzf eksctl_*.tar.gz
    """,
        shell=True,
    )


def parse_node_groups(node_groups_str):
    node_groups = []
    for group in node_groups_str.split(","):
        name, size = group.split(":")
        ng = {
            "name": name,
            "instanceType": instance_type,
            "desiredCapacity": int(size),
            "disableIMDSv1": True,
            "amiFamily": "Ubuntu2204",
            "maxPodsPerNode": 600,
            "volumeSize": 300,
            "preBootstrapCommands": [
                "apt-get -y update && apt-get -y install open-iscsi",
                """cat << 'EOF' > /etc/systemd/system/mount-nvme.service
[Unit]
Description=Format and mount NVMe
DefaultDependencies=no
Before=local-fs.target
[Service]
Type=oneshot
ExecStart=/bin/bash -c 'mkfs.ext4 -F /dev/nvme1n1; mkdir -p /var/lib/longhorn; mount /dev/nvme1n1 /var/lib/longhorn'
RemainAfterExit=yes
[Install]
WantedBy=sysinit.target
EOF""",
                "systemctl enable mount-nvme.service",
                "systemctl start mount-nvme.service",
            ],
        }
        if name.endswith("-spot"):
            ng["spot"] = True
        node_groups.append(ng)
    return node_groups


def generate_config(temp_dir):
    config = {
        "apiVersion": "eksctl.io/v1alpha5",
        "kind": "ClusterConfig",
        "metadata": {"name": cluster_name, "region": region, "tags": {tag.split("=")[0]: tag.split("=")[1] for tag in tags.split(",")}},
        "addonsConfig": {"autoApplyPodIdentityAssociations": True},
        "addons": [
            {"name": "vpc-cni", "version": "latest"},
            {"name": "coredns", "version": "latest"},
            {"name": "kube-proxy", "version": "latest"},
            {"name": "eks-pod-identity-agent", "version": "latest"},
        ],
        "managedNodeGroups": parse_node_groups(node_groups),
        "iam": {"withOIDC": True},
    }

    config_path = Path(temp_dir) / "cluster-config.yaml"
    yaml.dump(config)
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path

traefik_config = """service:
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: external
    service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
  spec:
    externalTrafficPolicy: Local

providers:
  kubernetesCRD:
    enabled: true
  kubernetesIngress:
    enabled: true
    publishedService:
      enabled: true

ingressClass:
  enabled: true
  isDefaultClass: true

additionalArguments:
  - "--providers.kubernetesingress.ingressclass=traefik"
  - "--providers.kubernetesingress.allowexternalnameservices=true"
"""

rancher_cmds = [
    f"eksctl utils write-kubeconfig --cluster={cluster_name} --region={region}",
    "curl -o iam-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.8.2/docs/install/iam_policy.json",
    "aws iam create-policy --policy-name AWSLoadBalancerControllerIAMPolicy --policy-document file://iam-policy.json",
    (f"eksctl create iamserviceaccount --cluster={cluster_name} --region={region} --namespace=kube-system --name=aws-load-balancer-controller"
     " --attach-policy-arn=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy"
     " --override-existing-serviceaccounts --approve"),
    "helm repo add eks https://aws.github.io/eks-charts",
    "helm repo add traefik https://traefik.github.io/charts",
    "helm repo add jetstack https://charts.jetstack.io",
    "helm repo add rancher-latest https://releases.rancher.com/server-charts/latest",
    "helm repo update",
    f"helm install --atomic aws-load-balancer-controller eks/aws-load-balancer-controller -n kube-system --set clusterName={cluster_name} --set serviceAccount.create=false --set serviceAccount.name=aws-load-balancer-controller",
    "helm install --atomic traefik traefik/traefik -n kube-system -f traefik-values.yaml",
    "helm install --atomic cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set crds.enabled=true",
    ("helm install --atomic rancher rancher-latest/rancher --create-namespace --namespace cattle-system --set ingress.tls.source=letsEncrypt"
     f" --set letsEncrypt.ingress.class=traefik --set hostname={rancher_fqdn} --set letsEncrypt.email={rancher_fqdn}@maildrop.cc")
]


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        install_tools()
        cmds = [f"eksctl create cluster -f {generate_config(temp_dir)}"]
        if rancher_fqdn:
            cmds += rancher_cmds
            Path("traefik-values.yaml").write_text(traefik_config)
        script = "\n".join(cmds)
        run(f"export PATH={temp_dir}:$PATH\n{script}", shell=True)


if __name__ == "__main__":
    main()
