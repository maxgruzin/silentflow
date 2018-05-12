"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from sf import views
from django.views.generic.base import RedirectView


urlpatterns = [
    url(r'^release/(?P<slug>[-\w]+)/$', views.release, name='release'),
    url(r'^$', views.index, name='index'),
    url(r'^catalogue/', views.catalogue, name='catalogue'),
    url(r'^artists/', views.artists, name='artists'),
    url(r'^about/', views.about, name='about'),
    url(r'^contact/', views.contact, name='contact'),

    # admin
    url(r'^control/', admin.site.urls),

    # legacy release urls
    url(r'^(?P<slug>[-\w]+)/$', RedirectView.as_view(url='/', permanent=True), name='legacy_release_url')
]
