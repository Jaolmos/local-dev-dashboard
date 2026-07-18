from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="list"),
    path("<int:pk>/git/", views.GitStatusView.as_view(), name="git-status"),
    path("<int:pk>/readme/", views.ReadmeView.as_view(), name="readme"),
    path("<int:pk>/open/", views.OpenVSCodeView.as_view(), name="open-vscode"),
    path("<int:pk>/open/button/", views.OpenButtonView.as_view(), name="open-button"),
]
