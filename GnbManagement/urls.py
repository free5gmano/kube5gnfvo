from django.urls import path
from . import views

urlpatterns = [
    path("gnb/v1/gnb_templates", views.gnb_templates_list, name="gnb-templates-list"),
    path("gnb/v1/gnb_templates/<uuid:template_id>", views.gnb_template_detail, name="gnb-template-detail"),
    path("gnb/v1/gnb_templates/<uuid:template_id>/deploy", views.gnb_template_deploy, name="gnb-template-deploy"),
    path("gnb/v1/gnb_instances", views.gnb_instances_list, name="gnb-instances-list"),
    path("gnb/v1/gnb_instances/<uuid:gnb_id>", views.gnb_instance_detail, name="gnb-instance-detail"),
    path("services/v1/all", views.all_services_list, name="all-services-list"),
]
