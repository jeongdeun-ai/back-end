from django.urls import path, include
from .views import *

urlpatterns = [
    path('get-user-settings/', get_user_settings, name='get-user-settings'), # get 메서드
    path('update-user-settings/', update_user_settings, name='update-user-settings'), # patch 메서드
]
