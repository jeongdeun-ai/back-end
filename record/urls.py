from django.urls import path, include
from .views import *

urlpatterns = [
    path('get-target-date-report/', get_target_date_record, name='get-target-date-report'), # 1번 뷰!
    path('get-target-date-chat-logs/', get_target_date_chat_logs, name='get-target-date-chat-logs'), # 2번 뷰!
]
