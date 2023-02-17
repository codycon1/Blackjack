from django.urls import path

from game import views

urlpatterns = [
    path('', views.home),
    path('play', views.play),
    path('singleplayer', views.singleplayer),
]