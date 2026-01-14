from django.urls import path
from . import views

urlpatterns = [
    # 页面路由
    path('face_search/', views.face_search_view, name='face_search'),
    path('batch_import_page/', views.batch_import_view, name='batch_import_page'),
    
    # API 路由
    path('api/search_face/', views.api_search_face, name='api_search_face'),
    path('api/batch_import/', views.api_batch_import, name='api_batch_import'),
    path('api/progress/<str:task_id>/', views.api_get_progress, name='api_get_progress'),
]