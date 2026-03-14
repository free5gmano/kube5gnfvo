# All Rights Reserved.
#
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import GnbInstance
from .serializers import GnbInstanceSerializer, GnbInstanceCreateSerializer
from utils.process_gnb.gnb_deployer import GnbDeployer


@api_view(['GET', 'POST'])
def gnb_instances_list(request):
    """
    GET: 列出所有 gNB 實例
    POST: 創建新的 gNB 實例
    """
    if request.method == 'GET':
        instances = GnbInstance.objects.all()
        serializer = GnbInstanceSerializer(instances, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = GnbInstanceCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                deployer = GnbDeployer(
                    gnb_name=serializer.validated_data['gnbInstanceName'],
                    namespace=serializer.validated_data.get('namespace', 'default'),
                    yaml_content=serializer.validated_data['yamlContent']
                )
                
                gnb_instance = deployer.deploy()
                
                if serializer.validated_data.get('gnbInstanceDescription'):
                    gnb_instance.gnbInstanceDescription = serializer.validated_data['gnbInstanceDescription']
                    gnb_instance.save()
                
                response_serializer = GnbInstanceSerializer(gnb_instance)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
def gnb_instance_detail(request, gnb_id):
    """
    GET: 獲取特定 gNB 實例詳情
    DELETE: 刪除特定 gNB 實例
    """
    try:
        gnb_instance = GnbInstance.objects.get(id=gnb_id)
    except GnbInstance.DoesNotExist:
        return Response(
            {'error': 'gNB instance not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = GnbInstanceSerializer(gnb_instance)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        try:
            deployer = GnbDeployer(
                gnb_name=gnb_instance.gnbInstanceName,
                namespace=gnb_instance.namespace,
                yaml_content=gnb_instance.yamlContent
            )
            deployer.undeploy()
            gnb_instance.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def all_services_list(request):
    """
    統一查詢所有服務（包含 NS Instances、gNB Instances 和 MEC App Instances）
    
    回傳格式：
    {
        "nsInstances": [...],
        "gnbInstances": [...],
        "mecAppInstances": [...]
    }
    """
    from NSLifecycleManagement.models import NsInstance
    from NSLifecycleManagement.serializers import NsInstanceSerializer
    from MecAppManagement.models import MecAppInstance
    from MecAppManagement.serializers import MecAppInstanceSerializer
    
    # 查詢所有 NS Instances (5GC 等)
    ns_instances = NsInstance.objects.all()
    ns_serializer = NsInstanceSerializer(ns_instances, many=True)
    
    # 查詢所有 gNB Instances
    gnb_instances = GnbInstance.objects.all()
    gnb_serializer = GnbInstanceSerializer(gnb_instances, many=True)
    
    # 查詢所有 MEC App Instances
    mec_app_instances = MecAppInstance.objects.all()
    mec_app_serializer = MecAppInstanceSerializer(mec_app_instances, many=True)
    
    return Response({
        'nsInstances': ns_serializer.data,
        'gnbInstances': gnb_serializer.data,
        'mecAppInstances': mec_app_serializer.data
    })
