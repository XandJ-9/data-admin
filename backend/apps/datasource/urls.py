from django.urls import path, include
from .views import DataSourceViewSet, QueryLogViewSet


from rest_framework.routers import DefaultRouter

router = DefaultRouter(trailing_slash=False)
router.register(r'query-log', QueryLogViewSet, basename='query-log')
# 没有url前缀得路由放最后，避免与其他路由冲突
router.register(r'', DataSourceViewSet, basename='data-source')

urlpatterns = [
    path('', include(router.urls)),
]
