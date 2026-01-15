# config/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views  # 导入刚才写的 views

urlpatterns = [
    # 1. 【新增】拦截 Admin 登录请求，使用我们自定义的跳转逻辑
    #    注意：这行必须放在 admin.site.urls 之前！
    path('admin/login/', views.custom_login),

    # 2. 标准 Django Admin (处理剩下的 /admin/logout, /admin/auth/ 等请求)
    path('admin/', admin.site.urls),
    
    # 3. 首页
    path('', views.face_search_view, name='home'),
    
    # 4. API
    path('api/search/', views.api_search_face, name='api_search_face'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])