from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DataSourceDiscoveryViewSet, DataSourceViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'datasource', DataSourceViewSet, basename='datasource')

collection_view = DataSourceDiscoveryViewSet.as_view({'post': 'databases'})
table_view = DataSourceDiscoveryViewSet.as_view({'post': 'tables'})
column_view = DataSourceDiscoveryViewSet.as_view({'post': 'columns'})
collect_table_view = DataSourceDiscoveryViewSet.as_view({'post': 'collect_table'})
collect_database_view = DataSourceDiscoveryViewSet.as_view({'post': 'collect_database'})
collect_database_run_view = DataSourceDiscoveryViewSet.as_view({'get': 'collect_database_run'})

urlpatterns = [
    path('', include(router.urls)),
    path('collection/databases', collection_view),
    path('collection/tables', table_view),
    path('collection/columns', column_view),
    path('collection/collect-table', collect_table_view),
    path('collection/collect-database', collect_database_view),
    path('collection/collect-database/<str:run_id>', collect_database_run_view),
]
