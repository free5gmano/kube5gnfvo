from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import GnbInstance, GnbTemplate
from .serializers import (
    GnbInstanceSerializer,
    GnbInstanceCreateSerializer,
    GnbTemplateSerializer,
    GnbTemplateCreateSerializer,
    GnbTemplateDeploySerializer,
)
from UEManagement.models import UeInstance
from UEManagement.serializers import UeInstanceSerializer
from utils.process_gnb.gnb_deployer import GnbDeployer


@api_view(["GET", "POST"])
def gnb_templates_list(request):
    if request.method == "GET":
        templates = GnbTemplate.objects.all().order_by("-createdAt")
        return Response(GnbTemplateSerializer(templates, many=True).data)

    serializer = GnbTemplateCreateSerializer(data=request.data)
    if serializer.is_valid():
        template = GnbTemplate.objects.create(
            templateName=serializer.validated_data["templateName"],
            templateDescription=serializer.validated_data.get("templateDescription", ""),
            namespace=serializer.validated_data.get("namespace", "default"),
            yamlContent=serializer.validated_data["yamlContent"],
        )
        return Response(GnbTemplateSerializer(template).data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "DELETE"])
def gnb_template_detail(request, template_id):
    try:
        gnb_template = GnbTemplate.objects.get(id=template_id)
    except GnbTemplate.DoesNotExist:
        return Response({"error": "gNB template not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(GnbTemplateSerializer(gnb_template).data)

    gnb_template.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def gnb_template_deploy(request, template_id):
    try:
        gnb_template = GnbTemplate.objects.get(id=template_id)
    except GnbTemplate.DoesNotExist:
        return Response({"error": "gNB template not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = GnbTemplateDeploySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    gnb_instance_name = serializer.validated_data.get("gnbInstanceName") or gnb_template.templateName
    gnb_instance_description = serializer.validated_data.get("gnbInstanceDescription") if "gnbInstanceDescription" in serializer.validated_data else gnb_template.templateDescription
    namespace = serializer.validated_data.get("namespace") or gnb_template.namespace
    node_name = serializer.validated_data.get("nodeName") or None

    try:
        deployer = GnbDeployer(
            gnb_name=gnb_instance_name,
            namespace=namespace,
            yaml_content=gnb_template.yamlContent,
            node_name=node_name,
        )
        gnb_instance = deployer.deploy()
        gnb_instance.gnbInstanceDescription = gnb_instance_description
        gnb_instance.save()
        return Response(GnbInstanceSerializer(gnb_instance).data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET", "POST"])
def gnb_instances_list(request):
    if request.method == "GET":
        instances = GnbInstance.objects.all().order_by("-createdAt")
        return Response(GnbInstanceSerializer(instances, many=True).data)

    serializer = GnbInstanceCreateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            deployer = GnbDeployer(
                gnb_name=serializer.validated_data["gnbInstanceName"],
                namespace=serializer.validated_data.get("namespace", "default"),
                yaml_content=serializer.validated_data["yamlContent"],
                node_name=serializer.validated_data.get("nodeName") or None,
            )
            gnb_instance = deployer.deploy()
            if serializer.validated_data.get("gnbInstanceDescription"):
                gnb_instance.gnbInstanceDescription = serializer.validated_data["gnbInstanceDescription"]
                gnb_instance.save()
            return Response(GnbInstanceSerializer(gnb_instance).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "DELETE"])
def gnb_instance_detail(request, gnb_id):
    try:
        gnb_instance = GnbInstance.objects.get(id=gnb_id)
    except GnbInstance.DoesNotExist:
        return Response({"error": "gNB instance not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(GnbInstanceSerializer(gnb_instance).data)

    try:
        deployer = GnbDeployer(
            gnb_name=gnb_instance.gnbInstanceName,
            namespace=gnb_instance.namespace,
            yaml_content=gnb_instance.yamlContent,
        )
        deployer.undeploy()
        gnb_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def all_services_list(request):
    from NSLifecycleManagement.models import NsInstance
    from NSLifecycleManagement.serializers import NsInstanceSerializer

    ns_instances = NsInstance.objects.all()
    gnb_instances = GnbInstance.objects.all()
    ue_instances = UeInstance.objects.all()
    return Response({
        "nsInstances": NsInstanceSerializer(ns_instances, many=True).data,
        "gnbInstances": GnbInstanceSerializer(gnb_instances, many=True).data,
        "ueInstances": UeInstanceSerializer(ue_instances, many=True).data,
    })
