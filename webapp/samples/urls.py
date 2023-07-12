from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("samples/", views.samples, name="samples"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("search/", views.search, name="search"),
    path("update/", views.update_issues, name="update"),
    path("samples/upload/", views.upload, name="upload"),
    path("case/<int:row_id>/", views.dewolf_error, name="dewolf_error"),
    path("issue/<int:case_id>/", views.create_github_issue, name="create_github_issue"),
    path("download/<str:sample_hash>/", views.download_sample, name="download_sample"),
]
