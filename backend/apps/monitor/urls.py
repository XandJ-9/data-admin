from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ServerView, OnlineViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'online', OnlineViewSet, basename='monitor-online')

urlpatterns = [
    path('server', ServerView.as_view({'get': 'get'}), name='monitor-server'),
    path('', include(router.urls)),
]

