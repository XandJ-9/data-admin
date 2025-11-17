from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, MenuViewSet, RoleViewSet, LoginView, CaptchaView, GetInfoView, LogoutView, GetRoutersView,
    DictTypeViewSet, DictDataViewSet,
)

router = DefaultRouter()
router.trailing_slash = '/?'
router.register(r'user', UserViewSet, basename='user')
router.register(r'menu', MenuViewSet, basename='menu')
router.register(r'role', RoleViewSet, basename='role')
router.register(r'dict/type', DictTypeViewSet, basename='dict-type')
router.register(r'dict/data', DictDataViewSet, basename='dict-data')

urlpatterns = [
    path('system/', include(router.urls)),
    # 兼容前端 PUT /system/menu（集合更新）
    path('system/menu', MenuViewSet.as_view({'put': 'update_by_body'}), name='menu-update-body'),
    # 兼容前端 PUT /system/role（集合更新）
    path('system/role', RoleViewSet.as_view({'put': 'update_by_body'}), name='role-update-body'),
    path('login', LoginView.as_view(), name='login'),
    path('captchaImage/', CaptchaView.as_view(), name='captcha-image'),
    path('getInfo', GetInfoView.as_view(), name='get-info'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('getRouters', GetRoutersView.as_view(), name='get-routers'),
]