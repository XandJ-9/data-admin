from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MetaTableViewSet, MetaColumnViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'meta-table', MetaTableViewSet, basename='meta-table')
router.register(r'meta-column', MetaColumnViewSet, basename='meta-column')

urlpatterns = [
    path('', include(router.urls)),
]
