from django.urls import path, include
from .views import *


urlpatterns = [
    path('get-user-settings/', get_user_settings, name='get-user-settings'), # get 메서드
]
