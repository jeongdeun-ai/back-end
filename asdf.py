import os
import django
import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from table.models import (
    Parent, User, UserParentRelation, Event, MedicationSchedule, MedicationItem,
    ChatLog, DailyReport, Question
)
from django.utils import timezone

# 김영익 할아버지와 김민지 보호자 쿼리로 찾기
parent = Parent.objects.get(name="김영익")
user = User.objects.get(email="wjdrlfyd2@naver.com")

# 날짜 설정
target_date = datetime.date(2025, 6, 5)

# # 1. 일정 생성
# Event.objects.bulk_create([
#     Event(
#         parent=parent,
#         title="무릎약 복용",
#         date=target_date,
#         start_time=datetime.time(8, 0),
#         end_time=datetime.time(8, 10),
#         event_type="normal"
#     ),
#     Event(
#         parent=parent,
#         title="서울의료원 무릎 통증 진료",
#         date=target_date,
#         start_time=datetime.time(10, 30),
#         end_time=datetime.time(11, 30),
#         event_type="hospital"
#     ),
#     Event(
#         parent=parent,
#         title="아파트 단지 산책",
#         date=target_date,
#         start_time=datetime.time(15, 0),
#         end_time=datetime.time(15, 40),
#         event_type="normal"
#     ),
# ])


# # 2. 복약 스케줄 및 약 정보
# time_slots = ['morning', 'lunch', 'dinner']
# med_sched_objs = []
# for slot in time_slots:
#     sched = MedicationSchedule.objects.create(parent=parent, time_slot=slot)
#     MedicationItem.objects.create(medication_schedule=sched, name="무릎약", dose="1정")
#     med_sched_objs.append(sched)

# 기존 복약 스케줄 초기화 (optional, 시연용)
# MedicationSchedule.objects.filter(parent=parent).delete()

# # 복약 스케줄 상세 버전
# medication_plan = {
#     'morning': [
#         {"name": "아모디핀", "dose": "5mg"},  # 고혈압약
#         {"name": "조인스정", "dose": "1정"},   # 무릎약
#         {"name": "고려은단 비타민C 1000", "dose": "1알"}
#     ],
#     'lunch': [
#         {"name": "조인스정", "dose": "1정"},
#         {"name": "고려은단 비타민C 1000", "dose": "1알"}
#     ],
#     'dinner': [
#         {"name": "아모디핀", "dose": "5mg"},
#         {"name": "조인스정", "dose": "1정"},
#         {"name": "아로나민골드", "dose": "1정"}
#     ]
# }

# # 삽입
# for slot, items in medication_plan.items():
#     sched = MedicationSchedule.objects.create(parent=parent, time_slot=slot)
#     for item in items:
#         MedicationItem.objects.create(
#             medication_schedule=sched,
#             name=item["name"],
#             dose=item["dose"]
#         )

# # 3. GPT 대화 로그
# now = timezone.now()
# ChatLog.objects.bulk_create([
#     ChatLog(parent=parent, sender="parent", message="오늘 날씨 어때?", timestamp=now.replace(hour=8, minute=10)),
#     ChatLog(parent=parent, sender="gpt", message="오늘 맑고 따뜻해요. 산책하기 좋아요!", timestamp=now.replace(hour=8, minute=11)),
#     ChatLog(parent=parent, sender="parent", message="그럼 점심 먹고 산책 가야겠다.", timestamp=now.replace(hour=12, minute=30)),
# ])

# # 4. 데일리 리포트
# DailyReport.objects.create(
#     parent=parent,
#     date=target_date,
#     summary="김영익 어르신은 오늘 GPT와 날씨에 대해 이야기하고, 무릎 진료와 산책을 잘 마치셨습니다.",
#     is_sent=True,
#     total_chat_time=12,
#     event_success_ratio=100,
#     parent_emotion="happy"
# )

# # 5. 질문 추천
# Question.objects.bulk_create([
#     Question(
#         parent=parent,
#         recommaned_question="예전에 무릎이 안 아프던 시절엔 주로 어떤 활동을 하셨어요?",
#         recommaned_reason="오늘 진료 및 산책을 바탕으로 과거 추억을 회상하게 유도할 수 있습니다.",
#         chat_count=3
#     ),
#     Question(
#         parent=parent,
#         recommaned_question="오늘 하루 중 가장 기분 좋았던 순간은 언제였나요?",
#         recommaned_reason="긍정적인 감정을 유도하기 위한 질문입니다.",
#         chat_count=5
#     ),
# ])

print("🎉 김영익 어르신의 더미 데이터가 성공적으로 생성되었습니다!")
