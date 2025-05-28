from django.urls import path, include
from .views import *


urlpatterns = [
    path('add-event-for-parent/', add_event_for_parent, name='add-event-for-parent'), # 1번 일정추가
    path("get-events-for-specific-date/", get_events_for_specific_date, name="get-events-for-specific-date"), # 2번 해당 parent 일정 전부 가져오기
    path('get-medicine-plan/', get_medicine_plan, name='get-medicine-plan'), # 3번 뷰 GET
    path('add-medicine-items/', add_medicine_items, name='add-medicine-items'), # 4번
]
