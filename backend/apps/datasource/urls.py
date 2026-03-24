from django.urls import path, include
from rest_framework import routers

from .views import DataSourceViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'datasource', DataSourceViewSet, basename='datasource')

urlpatterns = [
    path('', include(router.urls)),
]
