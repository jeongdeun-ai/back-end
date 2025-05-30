from django.urls import path, include
from .views import *

urlpatterns = [ 
    path('generate-recommend-question/',generate_recommend_question, name='generate-recommend-question'), # 1번 
]
