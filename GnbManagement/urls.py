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

from django.urls import path
from . import views

urlpatterns = [
    path('gnb/v1/gnb_templates', views.gnb_templates_list, name='gnb-templates-list'),
    path('gnb/v1/gnb_templates/<uuid:template_id>', views.gnb_template_detail, name='gnb-template-detail'),
    path('gnb/v1/gnb_templates/<uuid:template_id>/deploy', views.gnb_template_deploy, name='gnb-template-deploy'),
    path('gnb/v1/gnb_instances', views.gnb_instances_list, name='gnb-instances-list'),
    path('gnb/v1/gnb_instances/<uuid:gnb_id>', views.gnb_instance_detail, name='gnb-instance-detail'),
    # 統一查詢所有服務的端點
    path('services/v1/all', views.all_services_list, name='all-services-list'),
]
