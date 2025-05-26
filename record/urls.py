from django.urls import path, include
from .views import *

urlpatterns = [
    path('get-target-date-report/', get_target_date_record, name='get-target-date-report'), # 1번 뷰!
]
