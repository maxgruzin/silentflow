from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import RedirectView
from sf import views

urlpatterns = [
    path('robots.txt', views.robots, name='robots'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
    path('', views.index, name='index'),
    re_path(r'^release/(?P<slug>[-\w]+)/$', views.release, name='release'),
    path('releases/', views.catalogue, name='catalogue'),
    path('catalogue/', RedirectView.as_view(pattern_name='catalogue', permanent=True, query_string=True), name='legacy_catalogue'),
    path('artists/', views.artists, name='artists'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('control/', admin.site.urls),
    re_path(r'^(?P<slug>[-\w]+)/$', views.legacy_release, name='legacy_release_url'),
]
