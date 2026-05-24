from django.urls import path
from . import views

urlpatterns = [
    path("backend/",views.Backend.as_view()), #api/hello/backendというリクエストが来たらviews.pyのBackendというクラスを参照する
]