"""philmnight URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from film_management import views as fm_views
from . import views, settings


urlpatterns = [
    path('', views.index),
    path('', include('social_django.urls', namespace='social')),
    path('config/', views.config, name='config'),
    path('admin/', admin.site.urls),
    path('film_management/', include('film_management.urls')),
    path('dashboard/', fm_views.dashboard),
    path('films/', fm_views.films),
    path('films/<str:tmdb_id>', fm_views.film),
    path('logout/', views.logout_view)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
