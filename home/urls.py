from django.urls import path, include
from .views import *

urlpatterns = [
    path('get-daily-report-update/', get_daily_report_update, name='get-daily-report-update'), # 1번 
    path('get-parent-event-info/', get_parent_event_info, name='get-parent-event-info'), # 2번
]