# config/urls.py

from django.contrib import admin
from django.urls import path, include  # 【关键】导入 include
from django.conf import settings
from django.conf.urls.static import static

# 导入自定义 admin site
from core.admin import face_admin_site

urlpatterns = [
    # 1. 后台管理路由 (保持在主路由)
    path('admin/', face_admin_site.urls),

    # 2. 业务路由 (分发给 core.urls 处理)
    # 凡是空路径开头的请求，都转交给 core/urls.py
    path('', include('core.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)