from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DataSourceDiscoveryViewSet, DataSourceViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'datasource', DataSourceViewSet, basename='datasource')

collection_view = DataSourceDiscoveryViewSet.as_view({'post': 'databases'})
table_view = DataSourceDiscoveryViewSet.as_view({'post': 'tables'})
column_view = DataSourceDiscoveryViewSet.as_view({'post': 'columns'})

urlpatterns = [
    path('', include(router.urls)),
    path('collection/databases', collection_view),
    path('collection/tables', table_view),
    path('collection/columns', column_view),
]
