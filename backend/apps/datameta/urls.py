from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MetaTableViewSet, MetaColumnViewSet, BusinessDataView

router = DefaultRouter(trailing_slash=False)
router.register(r'meta-table', MetaTableViewSet, basename='meta-table')
router.register(r'meta-column', MetaColumnViewSet, basename='meta-column')
router.register(r'business', BusinessDataView, basename='business')

urlpatterns = [
    path('', include(router.urls)),
]
