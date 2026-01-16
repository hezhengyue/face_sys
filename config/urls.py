from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from core import views

urlpatterns = [
    # 1. 【核心修改】访问根目录 / 时，直接重定向到 /admin/
    path('', RedirectView.as_view(url='/admin/')),

    # 2. 【移动】给扫描页面一个新的路径，不再占用根目录
    path('face-scan/', views.face_search_view, name='face_search'),

    # 3. 原有配置保持不变
    path('admin/', admin.site.urls),
    path('api/search/', views.api_search_face, name='api_search_face'),
]


# 静态文件
if settings.DEBUG and settings.STATICFILES_DIRS:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# 媒体文件路由
if settings.DEBUG and settings.MEDIA_ROOT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)