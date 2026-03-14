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
from .models import MecAppInstance
from .serializers import MecAppInstanceSerializer, MecAppInstanceCreateSerializer
from utils.process_mec.mec_app_deployer import MecAppDeployer


@api_view(['GET', 'POST'])
def mec_app_instances_list(request):
    """
    GET: 列出所有 MEC App 實例
    POST: 創建新的 MEC App 實例
    """
    if request.method == 'GET':
        instances = MecAppInstance.objects.all()
        serializer = MecAppInstanceSerializer(instances, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = MecAppInstanceCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                deployer = MecAppDeployer(
                    mec_app_name=serializer.validated_data['mecAppInstanceName'],
                    namespace=serializer.validated_data.get('namespace', 'default'),
                    yaml_content=serializer.validated_data['yamlContent']
                )
                
                mec_app_instance = deployer.deploy()
                
                if serializer.validated_data.get('mecAppInstanceDescription'):
                    mec_app_instance.mecAppInstanceDescription = serializer.validated_data['mecAppInstanceDescription']
                
                if serializer.validated_data.get('mecAppType'):
                    mec_app_instance.mecAppType = serializer.validated_data['mecAppType']
                
                mec_app_instance.save()
                
                response_serializer = MecAppInstanceSerializer(mec_app_instance)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
def mec_app_instance_detail(request, mec_app_id):
    """
    GET: 獲取特定 MEC App 實例詳情
    DELETE: 刪除特定 MEC App 實例
    """
    try:
        mec_app_instance = MecAppInstance.objects.get(id=mec_app_id)
    except MecAppInstance.DoesNotExist:
        return Response(
            {'error': 'MEC App instance not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = MecAppInstanceSerializer(mec_app_instance)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        try:
            deployer = MecAppDeployer(
                mec_app_name=mec_app_instance.mecAppInstanceName,
                namespace=mec_app_instance.namespace,
                yaml_content=mec_app_instance.yamlContent
            )
            deployer.undeploy()
            mec_app_instance.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
