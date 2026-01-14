from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
from core.admin import face_admin_site

urlpatterns = [
    path('admin/', face_admin_site.urls),
    path('', views.face_search_view, name='home'),
    path('face_search/', views.face_search_view, name='face_search'),
    path('api/search-face/', views.api_search_face, name='api_search_face'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)