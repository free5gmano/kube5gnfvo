# Kube5GNfvo

## Table of Contents

- [Kube5GNfvo](#Kube5GNfvo)
- [Prerequisites](#prerequisites)
  - [Kubernetes](#Kubernetes)
  - [Multus](#Multus)
  - [OpenvSwitch](#OpenvSwitch)
  - [OVS-CNI](#OVS-CNI)
- [Quick Start](#quick-start)
  - [Deploy kube5gnfvo](#Database migrate)
  - [Example deployments](#example-deployments)
    - [Testing kube5gnfvo](#Testing-kube5gnfvo)

### Kubernetes
Please refer to [Bootstrapping clusters with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/) to install Kubernetes.
>Using Kubernetes version: v1.15.3

>Support Kubernetes version: v1.15 to v1.18

##### on ubuntu
```shell=
apt-get install -y kubelet=1.15.3-00 kubeadm=1.15.3-00 kubectl=1.15.3-00 --allow-downgrades
```

### Multus
>Please refer to [Multus Quickstart Installation Guide](https://github.com/intel/multus-cni#quickstart-installation-guide) to install Multus.
##### Or follow the instructions
```shell=
cd kube5gnfvo/example/
kubectl apply -f multus-daemonset-pre-1.16.yml
```
If using v1.16 or higher
```shell=
cd kube5gnfvo/example/
kubectl apply -f multus-daemonset.yml
```
### OpenvSwitch
>Please refer to [Open vSwitch Installation Guide](http://docs.openvswitch.org/en/latest/intro/install/#) to install OpenvSwitch.
##### Or follow the instructions
```shell=
apt install openvswitch-switch -y
ovs-vsctl add-br br1
```
### OVS-CNI
>Please refer to [Kubevirt OVS CNI](https://github.com/kubevirt/ovs-cni) to install ovs-cni.
##### Or follow the instructions
```shell=
cd kube5gnfvo/example/
kubectl apply -f ovs-cni-pre-1.16.yaml
```
>If using v1.16 or higher
```shell=
cd kube5gnfvo/example/
kubectl apply -f ovs-cni.yaml
```
##### Create a NetworkAttachmentDefinition
```shell=
cat <<EOF >./ovs-net-crd.yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: ovs-net
  annotations:
    k8s.v1.cni.cncf.io/resourceName: ovs-cni.network.kubevirt.io/br1
spec:
  config: '{
      "cniVersion": "0.3.1",
      "type": "ovs",
      "bridge": "br1"
    }'
EOF
kubectl apply -f ovs-net-crd.yaml
```




### ISTIO
>If you wish to learn more details, please refer to the follow the [ISTIO official website](https://github.com/istio/istio) or you can follow the steps below to perform a simple test and installation.

>In order to utilize Istio's features, you must have a multi-cluster environment with at least two Kubernetes clusters. Here is a simple example below to illustrate how to configure a multi-cluster environment.

#### first. rename the cluster into two different names.
##### Modify the areas marked in red on the image below
```
kubectl edit configmaps kubeadm-config -n kube-system
```
![圖片](https://github.com/free5gmano/kube5gnfvo/assets/36353259/d092129b-f4d4-4c01-a4c0-565e1d6f83dc)

##### Modify the corresponding areas on the image to reflect the renamed cluster names.
```
vim ~/.kube/config
```
![圖片](https://github.com/free5gmano/kube5gnfvo/assets/36353259/38ed8e7a-7665-4a4e-8585-450d8529444e)

##### check the results.
```
kubectl config view
```
![圖片](https://github.com/free5gmano/kube5gnfvo/assets/36353259/79589676-5bdd-40bb-9681-18be230f9be6)

#### In the primary cluster, add configuration information for the subordinate cluster
##### In the subordinate cluster
```
vim ~/.kube/config
```
>Copy the information for 'cluster,' 'contexts,' and 'users' below, as you will need to paste it into the configuration of the primary cluster later.
##### cluster
![圖片](https://github.com/free5gmano/kube5gnfvo/assets/36353259/29c4691a-db8c-40b6-ae44-cba5084c7eec)

##### contexts
![圖片](https://github.com/free5gmano/kube5gnfvo/assets/36353259/fed4f1d1-a924-489d-a567-cf65c82de81a)

#####  users
![圖片](https://github.com/free5gmano/kube5gnfvo/assets/36353259/65a6c3df-0cfc-4efc-adff-250ad875e1b4)

##### Go to the primary cluster
```
vim ~/.kube/config
```
>Paste the copied configuration into the corresponding location below the red line
![圖片](https://github.com/free5gmano/kube5gnfvo/assets/36353259/aac7bd17-79ca-4e71-8554-a5f0d75203a7)

#### install MetalLB
```
kubectl edit configmap -n kube-system kube-proxy
```
##### Modify the configuration below
```
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: "ipvs"
ipvs:
  strictARP: true
```
##### Install
```
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.12.1/manifests/namespace.yaml
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.12.1/manifests/metallb.yaml
```
##### Setting up an EXTERNAL-IP in Kubernetes using MetalLB.
>addresses: You can modify it according to the IP address you want to configure
```
cat << EOF > MetalLB_config.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     namespace: metallb-system
     name: config
   data:
     config: |
       address-pools:
       - name: default
         protocol: layer2
         auto-assign: true
         addresses:
         - 192.168.1.241-192.168.1.241 
   EOF
kubectl apply -f MetalLB_config.yaml
```
#### Establishing Istio Cross-Cluster Connectivity
##### Download Istio
>Follow the steps [here](https://istio.io/latest/docs/setup/getting-started/#download) to complete the download.
##### Set Environment Variables(Navigate to the Istio folder)
```
export CTX_CLUSTER1=$(kubectl config view -o jsonpath='{.contexts[0].name}')
export CTX_CLUSTER2=$(kubectl config view -o jsonpath='{.contexts[1].name}')
export PATH=$PWD/bin:$PATH
```
##### Create a key(Both cluster 1 and 2 need to be created)
```
kubectl create --context=$CTX_CLUSTER1 ns istio-system

# in Istio folder
kubectl create secret generic cacerts -n istio-system --from-file=samples/certs/ca-cert.pem --from-file=samples/certs/ca-key.pem --from-file=samples/certs/root-cert.pem --from-file=samples/certs/cert-chain.pem
```
#### Configure the primary cluster
##### Configure the primary remote settings
```
cat <<EOF > cluster1.yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  values:
    global:
      meshID: mesh1
      multiCluster:
        clusterName: cluster-primary
      network: network1
EOF
istioctl install --context="${CTX_CLUSTER1}" -f cluster1.yaml
```
##### Install the primary remote east-west gateway
```
samples/multicluster/gen-eastwest-gateway.sh \
    --mesh mesh1 --cluster cluster-primary --network network1 | \
    istioctl --context="${CTX_CLUSTER1}" install -y -f -
```
##### Expose the control plane
```
kubectl apply --context="${CTX_CLUSTER1}" -n istio-system -f \
    samples/multicluster/expose-istiod.yaml
```
##### Expose the API server for Cluster 1
```
kubectl --context="${CTX_CLUSTER1}" apply -n istio-system -f \
    samples/multicluster/expose-services.yaml
```
#### Configure the remote cluster
##### Set up networking for Cluster 2
```
kubectl --context="${CTX_CLUSTER2}" get namespace istio-system && \
  kubectl --context="${CTX_CLUSTER2}" label namespace istio-system topology.istio.io/network=network2
```
##### Authorize access to the Cluster 1 API server for Cluster 2
```
istioctl x create-remote-secret \
    --context="${CTX_CLUSTER2}" \
    --name=cluster-remote | \
    kubectl apply -f - --context="${CTX_CLUSTER1}"
```
##### Set the environment variable for the Cluster East-West Gateway IP
```
export DISCOVERY_ADDRESS=$(kubectl \
    --context="${CTX_CLUSTER1}" \
    -n istio-system get svc istio-eastwestgateway \
    -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
```
##### Configure the Cluster 2 YAML descriptor file
```
cat <<EOF > cluster2.yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  values:
    global:
      meshID: mesh1
      multiCluster:
        clusterName: cluster2
      network: network2
      remotePilotAddress: ${DISCOVERY_ADDRESS}
EOF
```
##### Install Istio on Cluster 2
```
istioctl install --context="${CTX_CLUSTER2}" -f cluster2.yaml
```

##### Install the East-West Gateway on Cluster 2
```
samples/multicluster/gen-eastwest-gateway.sh \
    --mesh mesh1 --cluster cluster-remote --network network2 | \
    istioctl --context="${CTX_CLUSTER2}" install -y -f -
```

##### Expose the API server for Cluster 2
```
kubectl --context="${CTX_CLUSTER2}" apply -n istio-system -f \
    samples/multicluster/expose-services.yaml
```
#### Istio automatic sidecar injection configuration
##### Configure automatic sidecar injection for the namespace
```
kubectl label namespace ${namespace} istio-injection=enabled
```
#### Istio cross-cluster feature testing
>If you use the following command to test, you should see that the service switches between clusters. When a service in one cluster goes idle, the service in the other cluster activates. If this happens, it indicates that Istio configuration is complete
```
for i in $(seq 10); do kubectl --context=$CTX_CLUSTER1 -n sample exec "$(kubectl get pod --context="${CTX_CLUSTER1}" -n sample -l app=sleep -o jsonpath='{.items[0].metadata.name}')" -c sleep -- curl -s helloworld:5000/hello; done
```

## Quick Start
### Database migrate
```
cd kube5gnfvo
python3 manage.py makemigrations
python3 manage.py migrate
```
### Deploy kube5gnfvo
```
python3 manage.py runserver 0.0.0.0:30888
```

### Example deployments
#### Testing kube5gnfvo
##### POSTMAN
We use POSTMAN to send request to API server. You can download at [here](https://www.postman.com/downloads/).
##### Create NS instance
>Compress files
````
Under kube5gnfvo/example/free5gcv1
````
You will see two directories, ns and Vnfpackage.
Zip ns directory into ns.zip. In  kube5gnfvo/example/free5gcv1/Vnfpackage, you will see seven directories, zip each of them into .zip file directly.
Now the file structure shown as below:
````
kube5gnfvo/example/free5gcv1
|--ns
|--ns.zip
|--vnfpackage
   |--amf
   |--hss
   |--mongodb
   |--pcrf
   |--smf
   |--upf
   |--webui
   |--amf.zip
   |--hss.zip
   |--mongodb.zip
   |--pcrf.zip
   |--smf.zip
   |--upf.zip
   |--webui.zip
````

>Create and upload VNF packages
````
Under kube5gnfvo/example/free5gcv1
````
* Create VNF packages
We send request to API server in "POST" method.
1. You can modify following URL, replace <your server IP> as your IP address, and fill it in the request URL column.
````
http://<your server IP>:30888/vnfpkgm/v1/vnf_packages/
````
![](https://i.imgur.com/qiqi1cS.png)

Send request to server, you will receive server response "201 Created".

* Upload VNF packages
On the previous step, server will respone an id number(see the figure shown below, the red box)
![](https://i.imgur.com/ziatPPT.png)

2. Create a new request in "PUT" method. 
Modify following URL, replace <your server IP> as your IP address; <id> as we got in last figure.
````
http://<your server IP>:30888/vnfpkgm/v1/vnf_packages/<id>/package_content/
````
![](https://i.imgur.com/HxQUc2o.png)

3. Modify the headers of the request. Add two key-value, "Accept-application/zip" and "Accept-application/json" as following figure shown.
![](https://i.imgur.com/jNxaDYw.png)

4. Modify the body of the request. 
In "form-data" format, we add one key-value: "file" is our key and seven .zip files we compressed under /vnfpackages directory is our "value".
Remenber to select value type as "file" then you can choose .zip file as your value. To select value type you can find the menu as shown in figure(red box).
In each request we will upload only "one" file.

![](https://i.imgur.com/vceOJpu.png)

5. Send the request to server, you will get response "202 Accepted".

6. Repeat step 1 to step 4, each time replace one .zip file under /vnfpackages directory. Not until upload seven .zip file will you go to next step (step 7).

>Create ns descriptor

7. Create a new request in "POST" method.
Modify following URL, replace <your server IP> as your IP address.
````
http://<your server IP>:30888/nsd/v1/ns_descriptors/
````
Send request to server. You will receive server response "201 Created", and an id number as shown in following figure (red box).
![](https://i.imgur.com/YJXk7WE.png)

>Create and upload ns descriptor

8. Create a new request in "PUT" method.
Modify following URL, replace <your server IP> as your IP address; <id> as we got in last figure.
````
http://<your server IP>:30888/nsd/v1/ns_descriptors/<id>/nsd_content/
````

9. Modify the headers of the request. Add two key-value, "Accept-application/zip" and "Accept-application/json" as following figure shown.
![](https://i.imgur.com/YUDWd6B.png)

10. Modify the body of the request. In "form-data" format, we add one key-value: "file" is our key and "value" is our ns.zip file we comressed before. Also remenber to select type of value as "file"(shown in following figure, red box).
![](https://i.imgur.com/afmys1R.png)
Send the request to server, you will receive server response "202 Accepted".

> Create and instantiate ns instance

11. Create a new request in "POST" method.
Modify following URL, replace <your server IP> as your IP address.
````
http://<your server IP>:30888/nslcm/v1/ns_instances/
````

12. Modify the body of the request. In "raw, JSON" format, type in following JSON file.
````
{
    "nsdId": "2116fd24-83f2-416b-bf3c-ca1964793acb",
    "nsName": "String",
    "nsDescription": "String"
}
````
![](https://i.imgur.com/49GufwZ.png)
Send the request to server, you will receive server response "201 Created", and body of response in JSON format. Retain the response, we will use them in next step.

13. Create a new request in "POST" method.
Modify following URL, replace <your server IP> as your IP address; <id in red box> as we got in last response(as following figure shown, in red box).
````
http://<your server IP>:30888/nslcm/v1/ns_instances/<id in red box>/instantiate/
````
![](https://i.imgur.com/Q58u21n.png)

14. In request body, we used "raw, JSON" format.You can fill in the body as following.
````
{
    "vnfInstanceData":[
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        }
    ]
}
````
For "vnfInstanceId" fields, you can get them in previous response. The response in JSON format, we used ID in second layer as vnfInstanceId. The following is the JSON structure of response to show how we use in vnfInstanceId. You can also see the blue box in previous figure as example.
````
{
    "id": "ce76d430-f8d8-4598-9229-cdae44ab9f32",
    "vnffgInfo": [],
    "vnfInstance": [
        {
            "id": "<vnfInstanceId we look for>",
            "vnfInstanceName": "2116fd24-83f2-416b-bf3c-ca1964793smf-iqfuvhakgw",
            ......
        },
        {
            "id": "<vnfInstanceId we look for>",
            "vnfInstanceName": "2116fd24-83f2-416b-bf3c-ca19647webui-augxvnqoyw",
            ......
        },
        ......
}
````
Send the request to server, you will receive server response "202 Accepted".
