from django.urls import path, include
from .views import *

urlpatterns = [
    path('get-daily-report-update/', get_daily_report_update, name='get-daily-report-updatet'), # 1번
]