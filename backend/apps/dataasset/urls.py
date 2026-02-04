from django.urls import path, include
from rest_framework import routers

from .views import (
    DataSourceViewSet,
    MetaTableViewSet,
    MetaColumnViewSet,
    MetadataCollectionViewSet,
    TableLineageViewSet
)

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'datasource', DataSourceViewSet, basename='dataasset-datasource')
router.register(r'meta-table', MetaTableViewSet, basename='dataasset-meta-table')
router.register(r'meta-column', MetaColumnViewSet, basename='dataasset-meta-column')
router.register(r'collection', MetadataCollectionViewSet, basename='dataasset-collection')
router.register(r'lineage', TableLineageViewSet, basename='dataasset-lineage')

urlpatterns = [
    path('', include(router.urls)),
]
