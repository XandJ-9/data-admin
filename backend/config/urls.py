"""
URL configuration for ruoyi-django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.decorators.clickjacking import xframe_options_exempt
from rest_framework.permissions import AllowAny

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('admin/', admin.site.urls),
    # 1. 前端入口页面：访问根路径时返回 Vue 的 index.html
    path('data-admin/', TemplateView.as_view(template_name='index.html')),
    # # 2. 处理 Vue 路由的 History 模式（可选，若 Vue 用了 History 模式）
    re_path(r'^data-admin/.*$', TemplateView.as_view(template_name='index.html')),
    path('data-api/', include('apps.system.urls')),
    path('data-api/monitor/', include('apps.monitor.urls')),
    # 业务路由api
    path('data-api/datasource/', include('apps.datasource.urls')),  # 数据源管理模块
    path('data-api/dataasset/', include('apps.dataasset.urls')),  # 数据资产管理模块（包含元数据管理）
    path('data-api/dataservice/', include('apps.dataservice.urls')),
    path('data-api/datadev/', include('apps.datadev.urls')),       # 数据开发模块
    path('data-api/terminal/', include('apps.terminal.urls')),     # Web Terminal

    # path('data-api/dataintegration/', include('apps.dataintegration.urls')),
    # path('data-api/datataskmonitor/', include('apps.datataskmonitor.urls')),
    # path('data-api/datastudio/', include('apps.datastudio.urls')),
    # 验证码路由
    path('data-api/captcha/', include('captcha.urls')),
    # swagger api
    path('api/schema/', xframe_options_exempt(SpectacularAPIView.as_view(permission_classes=[AllowAny])), name='schema'),
    path('api/docs/', xframe_options_exempt(SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[AllowAny])), name='swagger-ui'),

]+ static('/data-api' + settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
