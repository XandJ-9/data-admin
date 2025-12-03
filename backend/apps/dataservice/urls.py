from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import QueryServiceView, QueryLogViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'query-log', QueryLogViewSet, basename='dataservice-query-log')

urlpatterns = [
    path('query', QueryServiceView.as_view({'post': 'query'}), name='dataservice-query'),
    path('', include(router.urls)),
]