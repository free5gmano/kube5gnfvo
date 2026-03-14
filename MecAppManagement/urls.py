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
    path('mec/v1/mec_app_instances', views.mec_app_instances_list, name='mec-app-instances-list'),
    path('mec/v1/mec_app_instances/<uuid:mec_app_id>', views.mec_app_instance_detail, name='mec-app-instance-detail'),
]
