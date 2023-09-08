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

"""os_ma_nfvo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from rest_framework import permissions
from django.conf.urls import url
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib import admin

vnf_pkg = [path('', include('VnfPackageManagement.urls')),
           path('', include('VnfPackageSubscription.urls'))]

nsd = [path('', include('NSDManagement.urls')),
       path('', include('NSDSubscription.urls'))]

ns_instance = [path('', include('NSLifecycleManagement.urls')),
               path('', include('NSLifecycleSubscriptions.urls'))]

ns_fault = [path('', include('NSFaultManagement.urls')),
            path('', include('NSFaultSubscription.urls'))]

ns_fault_schema_view = get_schema_view(
    openapi.Info(
        title="SOL005 - NS Fault Management Interface",
        default_version='v1',
        description="SOL005 - NS Fault Management Interface IMPORTANT: \
        Please note that this file might be not aligned to the current version of the ETSI Group Specification \
        it refers to and has not been approved by the ETSI NFV ISG. \
        In case of discrepancies the published ETSI Group Specification takes precedence. \
        refer https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/005/02.07.01_60/gs_NFV-SOL005v020701p.pdf",
        terms_of_service="https://github.com/free5gmano/kube5gnfvo",
        contact=openapi.Contact(email="free5gmano@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=False,
    permission_classes=(permissions.AllowAny,),
    patterns=ns_fault,
)
ns_instance_schema_view = get_schema_view(
    openapi.Info(
        title="SOL005 - NS Lifecycle Management Interface",
        default_version='v1',
        description=" SOL005 - NS Lifecycle Management Interface IMPORTANT: \
        Please note that this file might be not aligned to the current version of the ETSI Group Specification \
        it refers to and has not been approved by the ETSI NFV ISG. \
        In case of discrepancies the published ETSI Group Specification takes precedence. \
        refer https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/005/02.07.01_60/gs_NFV-SOL005v020701p.pdf",
        terms_of_service="https://github.com/free5gmano/kube5gnfvo",
        contact=openapi.Contact(email="free5gmano@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=False,
    permission_classes=(permissions.AllowAny,),
    patterns=ns_instance,
)

nsd_schema_view = get_schema_view(
    openapi.Info(
        title="SOL005 - NSD Management Interface",
        default_version='v1',
        description="SOL005 - NSD Management Interface IMPORTANT: \
        Please note that this file might be not aligned to the current version of the ETSI Group Specification \
        it refers to and has not been approved by the ETSI NFV ISG. \
        In case of discrepancies the published ETSI Group Specification takes precedence. \
        refer https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/005/02.07.01_60/gs_NFV-SOL005v020701p.pdf",
        terms_of_service="https://github.com/free5gmano/kube5gnfvo",
        contact=openapi.Contact(email="free5gmano@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=False,
    permission_classes=(permissions.AllowAny,),
    patterns=nsd,
)

vnf_pkg_schema_view = get_schema_view(
    openapi.Info(
        title="SOL005 - VNF Package Management Interface",
        default_version='v1',
        description="SOL005 - VNF Package Management Interface IMPORTANT: \
        Please note that this file might be not aligned to the current version of the ETSI Group Specification \
        it refers to and has not been approved by the ETSI NFV ISG. \
        In case of discrepancies the published ETSI Group Specification takes precedence. \
        refer https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/005/02.07.01_60/gs_NFV-SOL005v020701p.pdf",
        terms_of_service="https://github.com/free5gmano/kube5gnfvo",
        contact=openapi.Contact(email="free5gmano@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=False,
    permission_classes=(permissions.AllowAny,),
    patterns=vnf_pkg,
)

urlpatterns = [
    url(r'^swagger/v1/ns_fault/$', ns_fault_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^swagger/v1/nsd/$', nsd_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^swagger/v1/vnfpkgm/$', vnf_pkg_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui1'),
    url(r'^swagger/v1/ns_instance/$', ns_instance_schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui1'),
    path('', include('VnfPackageManagement.urls')),
    path('', include('VnfPackageSubscription.urls')),
    path('', include('NSDManagement.urls')),
    path('', include('NSDSubscription.urls')),
    path('', include('NSLifecycleManagement.urls')),
    path('', include('NSLifecycleSubscriptions.urls')),
    path('', include('NSLCMOperationOccurrences.urls')),
    path('', include('VIMManagement.urls')),
    path('', include('NSFaultManagement.urls')),
    path('', include('NSFaultSubscription.urls')),
    path('admin/', admin.site.urls),
]
