from django.urls import path, include
from users import views

urlpatterns = [
    path('signup/', views.user_signup),
    path('', include('django.contrib.auth.urls')),
]