from django.urls import path
from UEManagement import views

urlpatterns = [
    path("ue/v1/ue_instances", views.ue_instances_list, name="ue-instances-list"),
    path("ue/v1/ue_instances/<uuid:ue_id>", views.ue_instance_detail, name="ue-instance-detail"),
]
