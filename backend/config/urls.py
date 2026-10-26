from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from team.views import (AccountManagementView, CurrentUserView, DashboardView, LogoutView,
                        PasswordResetConfirmView, PasswordResetRequestView, RegistrationView,
                        TokenLoginView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/', TokenLoginView.as_view(), name='api-token-auth'),
    path('api/auth/register/', RegistrationView.as_view(), name='api-register'),
    path('api/auth/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('api/auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('api/admin/accounts/', AccountManagementView.as_view(), name='account-list'),
    path('api/admin/accounts/<int:pk>/', AccountManagementView.as_view(), name='account-detail'),
    path('api/auth/me/', CurrentUserView.as_view(), name='current-user'),
    path('api/auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/', include('team.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
