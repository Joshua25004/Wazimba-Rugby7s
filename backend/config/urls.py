from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from team.views import DashboardView, CurrentUserView, LogoutView, TokenLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/', TokenLoginView.as_view(), name='api-token-auth'),
    path('api/auth/me/', CurrentUserView.as_view(), name='current-user'),
    path('api/auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/', include('team.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
