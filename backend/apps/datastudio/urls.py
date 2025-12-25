from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DataStudioTaskViewSet

router = DefaultRouter()
router.register(r'tasks', DataStudioTaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
