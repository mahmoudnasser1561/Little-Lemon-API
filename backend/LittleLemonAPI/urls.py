"""
URL configuration for LittleLemonAPI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),

    # app endpoints
    path("api/", include("restaurant.urls")),
    path("api/", include("cart.urls")),
    path("api/", include("delivery_crew.urls")),
    path("api/", include("checkout.urls")),

    # djoser endpoints
    path("api/", include("djoser.urls")),

    # token endpoint
    path("", include("djoser.urls.authtoken")),
]

# Only when using local-disk media storage (see settings.py) - S3/MinIO serves its own
# URLs directly and needs no route here. Django's own django.conf.urls.static.static()
# helper only adds this when DEBUG=True, but this project runs DEBUG=False in
# docker-compose by design, so the route is added directly rather than through it.
if not os.environ.get('MINIO_ENDPOINT'):
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

