from django.urls import path, include
from .views import *


urlpatterns = [
    path('add-event-for-parent/', add_event_for_parent, name='add-event-for-parent'), # 1번 일정추가
    path("get-events-for-specific-date/", get_events_for_specific_date, name="get-events-for-specific-date"), # 2번 해당 parent 일정 전부 가져오기
]
