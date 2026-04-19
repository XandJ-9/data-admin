from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    QueryServiceView, QueryLogViewSet,
    InterfaceInfoViewSet, InterfaceFieldViewSet, ReportInfoViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register(r'query-log', QueryLogViewSet, basename='dataservice-query-log')
router.register(r'interface-info', InterfaceInfoViewSet, basename='dataservice-interface-info')
router.register(r'interface-field', InterfaceFieldViewSet, basename='dataservice-interface-field')
router.register(r'report-info', ReportInfoViewSet, basename='dataservice-report-info')

urlpatterns = [
    path('query', QueryServiceView.as_view({'post': 'query'}), name='dataservice-query'),
    path('export', QueryServiceView.as_view({'post': 'export'}), name='dataservice-export'),
    path('', include(router.urls)),
]