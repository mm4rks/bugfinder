from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("samples/", views.samples, name="samples"),
    path("sample/<str:sample_hash>/", views.sample, name="sample"),
    path("case/<int:row_id>/", views.dewolf_error, name="dewolf_error"),
    path("issue/<int:case_id>/", views.create_github_issue, name="create_github_issue"),
    path("download/<str:sample_hash>/", views.download_sample, name="download_sample"),
]
