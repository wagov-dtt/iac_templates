# Opinionated EKS setup (Cilium, Longhorn, local NVMe)

To get maximum price/performance ration, the below establishes an EKS cluster using spot instances (some can be reserved for stability), and Cilium networking.

## Setup script

The [`aws_k8s_quickstart.py`](aws_k8s_quickstart.py) script sets up a reasonably sized cluster for testing - approx 96GB ram and 1.5TB raw disk, 512GB replicated 3 ways.

```bash
# Run in AWS Cloud Shell (takes approx 15 mins)
curl -sL https://github.com/wagov-dtt/iac_templates/raw/main/aws_k8s_quickstart.py | python - <clustername>
```

## Configure options

There are some defaults that can be overridden with env vars (e.g. just run `export AWS_INSTANCE_TYPE=m6a.xlarge` before running the script above):

```yaml
  region: {env('AWS_REGION', 'ap-southeast-2')}
  instanceType: {env('AWS_INSTANCE_TYPE' ,'i4i.xlarge')}
  volumeSize: {env('AWS_VOLUME_SIZE', 64)}
```

## TODO: Longhorn with local ephemeral volumes

`apt install linux-modules-extra-aws` is needed for nvme-tcp module on each node (todo add to alpine daemonset)

Needs some work to figure out how to format and mount ephemeral volumes as part of the launch template so longhorn can manage them easily.