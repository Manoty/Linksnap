# core/urls.py
# Root URL configuration.
# All app routes are namespaced and mounted here.

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerUIView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API routes
    path('api/', include('common.urls')),         # health check
    path('api/auth/', include('accounts.urls')),  # auth endpoints
    path('api/links/', include('links.urls')),     # link management

    # OpenAPI schema + Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerUIView.as_view(url_name='schema'), name='swagger-ui'),
]