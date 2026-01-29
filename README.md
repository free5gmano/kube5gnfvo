# Kube5GNfvo

## Table of Contents

- [Kube5GNfvo](#Kube5GNfvo)
- [Quick Start](#quick-start)
  - [Deployment with Chocolee Deploy Scripts](#deployment-with-chocolee-deploy-scripts)
    - [Script Overview](#script-overview)
    - [Prerequisites](#prerequisites)
    - [Quick Start](#quick-start-1)
    - [Cleanup](#cleanup)

## Quick Start

### Deployment with Chocolee Deploy Scripts

We provide deployment scripts in the `chocolee_deploy/scripts/` directory:

#### Script Overview

- **0-cleanup-kubernetes.sh** - Completely removes Kubernetes and all components
- **1-setup-environment-v3.sh** - Sets up Kubernetes environment with all required components
- **2-deploy-kube5gnfvo.sh** - Deploys MySQL database and prepares the application

#### Prerequisites
- Ubuntu 20.04 or later
- At least 4 CPU cores and 8GB RAM
- 50GB free disk space
- Internet connection for downloading packages

#### Quick Start

1. **Setup Kubernetes Environment** (First time only)
```shell
sudo bash chocolee_deploy/scripts/1-setup-environment-v3.sh
```

You can specify a different Kubernetes version:
```shell
sudo bash chocolee_deploy/scripts/1-setup-environment-v3.sh --k8s-version 1.32
```

2. **Deploy MySQL and Prepare Application**
```shell
bash chocolee_deploy/scripts/2-deploy-kube5gnfvo.sh
```

3. **Start the Application**
```shell
python3 manage.py migrate
python3 manage.py runserver 0.0.0.0:8000
```

#### Cleanup
To completely remove Kubernetes and all components:
```shell
sudo bash chocolee_deploy/scripts/0-cleanup-kubernetes.sh
```
