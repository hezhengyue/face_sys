# core/urls.py

from django.urls import path
from . import views

# 注意：为了兼容你之前代码里的 reverse('home')，
# 这里暂时不加 app_name = 'core'，保持全局命名空间。

urlpatterns = [
    # 首页 / 人脸搜索页
    path('', views.face_search_view, name='home'),
    
    # 为了兼容可能的旧链接，也可以保留 explicit 的路径
    path('face_search/', views.face_search_view, name='face_search'),
    
    # API 接口
    path('api/search-face/', views.api_search_face, name='api_search_face'),
]