from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IntegrationTaskViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'task', IntegrationTaskViewSet, basename='dataintegration-task')

urlpatterns = [
    path('', include(router.urls)),
]

