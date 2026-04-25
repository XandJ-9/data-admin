from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DataSourceDiscoveryViewSet, DataSourceViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'datasource', DataSourceViewSet, basename='datasource')

collection_view = DataSourceDiscoveryViewSet.as_view({'post': 'databases'})
table_view = DataSourceDiscoveryViewSet.as_view({'post': 'tables'})
column_view = DataSourceDiscoveryViewSet.as_view({'post': 'columns'})
collect_view = DataSourceDiscoveryViewSet.as_view({'post': 'collect'})
collect_table_view = DataSourceDiscoveryViewSet.as_view({'post': 'collect_table'})
collect_async_view = DataSourceDiscoveryViewSet.as_view({'post': 'collect_async'})
collect_status_view = DataSourceDiscoveryViewSet.as_view({'get': 'collect_status'})
collect_cancel_view = DataSourceDiscoveryViewSet.as_view({'post': 'collect_cancel'})

urlpatterns = [
    path('', include(router.urls)),
    path('collection/databases', collection_view),
    path('collection/tables', table_view),
    path('collection/columns', column_view),
    path('collection/collect', collect_view),
    path('collection/collect-table', collect_table_view),
    path('collection/collect-async', collect_async_view),
    path('collection/collect-status', collect_status_view),
    path('collection/collect-cancel', collect_cancel_view),
]

