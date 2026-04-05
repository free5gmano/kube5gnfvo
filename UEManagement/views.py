from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from GnbManagement.models import UeInstance
from UEManagement.serializers import UeInstanceSerializer, UeInstanceCreateSerializer
from utils.process_ue.ue_deployer import UeDeployer


@api_view(["GET", "POST"])
def ue_instances_list(request):
    if request.method == "GET":
        instances = UeInstance.objects.all().order_by("-createdAt")
        serializer = UeInstanceSerializer(instances, many=True)
        return Response(serializer.data)

    serializer = UeInstanceCreateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            deployer = UeDeployer(
                ue_name=serializer.validated_data["ueInstanceName"],
                namespace=serializer.validated_data.get("namespace", "default"),
                yaml_content=serializer.validated_data["yamlContent"],
                node_name=serializer.validated_data.get("nodeName") or None,
                gnb_service_name=serializer.validated_data.get("gnbServiceName") or None,
            )
            ue_instance = deployer.deploy()
            if serializer.validated_data.get("ueInstanceDescription"):
                ue_instance.ueInstanceDescription = serializer.validated_data["ueInstanceDescription"]
            if serializer.validated_data.get("gnbServiceName"):
                ue_instance.gnbServiceName = serializer.validated_data["gnbServiceName"]
            ue_instance.save()
            return Response(UeInstanceSerializer(ue_instance).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "DELETE"])
def ue_instance_detail(request, ue_id):
    try:
        ue_instance = UeInstance.objects.get(id=ue_id)
    except UeInstance.DoesNotExist:
        return Response({"error": "UE instance not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(UeInstanceSerializer(ue_instance).data)

    try:
        deployer = UeDeployer(
            ue_name=ue_instance.ueInstanceName,
            namespace=ue_instance.namespace,
            yaml_content=ue_instance.yamlContent,
            gnb_service_name=ue_instance.gnbServiceName,
        )
        deployer.undeploy()
        ue_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
