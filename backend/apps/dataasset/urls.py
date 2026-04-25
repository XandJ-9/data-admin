from django.urls import path, include
from rest_framework import routers

from .views import (
    AssetNamespaceViewSet,
    DataAssetColumnViewSet,
    DataAssetViewSet,
    MetaTableViewSet,
    MetaColumnViewSet,
    TableLineageViewSet
)

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'asset-namespace', AssetNamespaceViewSet, basename='dataasset-asset-namespace')
router.register(r'asset', DataAssetViewSet, basename='dataasset-asset')
router.register(r'asset-column', DataAssetColumnViewSet, basename='dataasset-asset-column')
router.register(r'meta-table', MetaTableViewSet, basename='dataasset-meta-table')
router.register(r'meta-column', MetaColumnViewSet, basename='dataasset-meta-column')
router.register(r'lineage', TableLineageViewSet, basename='dataasset-lineage')

urlpatterns = [
    path('', include(router.urls)),
]
