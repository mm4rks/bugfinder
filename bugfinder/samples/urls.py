from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<str:sample_hash>/", views.sample, name="sample"),
    path("case/<int:case_id>/", views.case, name="case"),
]
