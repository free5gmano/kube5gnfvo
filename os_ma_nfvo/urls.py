from django.urls import include, path, re_path
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

vnf_pkg = [path("", include("VnfPackageManagement.urls")), path("", include("VnfPackageSubscription.urls"))]
nsd = [path("", include("NSDManagement.urls")), path("", include("NSDSubscription.urls"))]
ns_instance = [path("", include("NSLifecycleManagement.urls")), path("", include("NSLifecycleSubscriptions.urls"))]
ns_fault = [path("", include("NSFaultManagement.urls")), path("", include("NSFaultSubscription.urls"))]

ns_fault_schema_view = get_schema_view(
    openapi.Info(
        title="SOL005 - NS Fault Management Interface",
        default_version="v1",
        description="SOL005 - NS Fault Management Interface.",
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
        default_version="v1",
        description="SOL005 - NS Lifecycle Management Interface.",
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
        default_version="v1",
        description="SOL005 - NSD Management Interface.",
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
        default_version="v1",
        description="SOL005 - VNF Package Management Interface.",
        terms_of_service="https://github.com/free5gmano/kube5gnfvo",
        contact=openapi.Contact(email="free5gmano@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=False,
    permission_classes=(permissions.AllowAny,),
    patterns=vnf_pkg,
)

urlpatterns = [
    re_path(r"^swagger/v1/ns_fault/$", ns_fault_schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    re_path(r"^swagger/v1/nsd/$", nsd_schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    re_path(r"^swagger/v1/vnfpkgm/$", vnf_pkg_schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui1"),
    re_path(r"^swagger/v1/ns_instance/$", ns_instance_schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui1"),
    path("", include("VnfPackageManagement.urls")),
    path("", include("VnfPackageSubscription.urls")),
    path("", include("NSDManagement.urls")),
    path("", include("NSDSubscription.urls")),
    path("", include("NSLifecycleManagement.urls")),
    path("", include("NSLifecycleSubscriptions.urls")),
    path("", include("NSLCMOperationOccurrences.urls")),
    path("", include("VIMManagement.urls")),
    path("", include("NSFaultManagement.urls")),
    path("", include("NSFaultSubscription.urls")),
    path("", include("UEManagement.urls")),
    path("", include("GnbManagement.urls")),
]
