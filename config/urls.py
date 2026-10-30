"""Root URL configuration for Basha Pass.

Integrates admin and public URLs allow-list.
"""

from django.contrib import admin
from django.urls import include, path

from config.urls_public import public_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(public_urlpatterns)),
]
