from django.contrib import admin
from django.urls import path, re_path
from sf import views

urlpatterns = [
    path('', views.index, name='index'),
    re_path(r'^release/(?P<slug>[-\w]+)/$', views.release, name='release'),
    path('catalogue/', views.catalogue, name='catalogue'),
    path('artists/', views.artists, name='artists'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('control/', admin.site.urls),
    re_path(r'^(?P<slug>[-\w]+)/$', views.legacy_release, name='legacy_release_url'),
]
