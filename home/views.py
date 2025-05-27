# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status

# from table.models import *
# from .serializers import *

# from rest_framework.permissions import IsAuthenticated
# from rest_framework.decorators import api_view, permission_classes
# from django.db import IntegrityError
# from django.db import transaction

# # Open AI API 사용하기 위한 header
# import os
# from dotenv import load_dotenv
# import openai

# from django.core.files.base import ContentFile
# from django.core.files.storage import default_storage
# from django.http import HttpResponse
# import base64

# load_dotenv()
# openai_api_key = os.getenv('OPENAI_API_KEY')

# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# from datetime import date

# from table.models import ChatLog
# import openai
# from django.utils.timezone import now

# def summarize_chat_logs(parent, target_date):
#     """
#     특정 날짜의 ChatLog를 기반으로 GPT에게 요약을 요청하고 요약된 텍스트를 반환합니다.
    
#     :param parent: Parent 객체
#     :param target_date: datetime.date 객체 (예: date.today())
#     :return: 요약된 텍스트 (str) / 대화 없을 시 None 반환
#     """
#     chat_logs = ChatLog.objects.filter(
#         parent=parent,
#         timestamp__date=target_date
#     ).order_by('timestamp')

#     if not chat_logs.exists():
#         print("📭 대화 기록 없음")
#         return None

#     # 대화 내용을 문자열로 구성
#     content = ""
#     for chat in chat_logs:
#         sender_label = "👵 어르신" if chat.sender == "parent" else "🤖 GPT"
#         content += f"{sender_label}: {chat.message}\n"

#     # GPT 요약 요청
#     openai.api_key = os.getenv("OPENAI_API_KEY")
#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": "다음은 하루 동안의 GPT와 사용자 대화입니다. 여기서 GPT와 대화하는 어르신에 중점을 둔 채로 전체 대화를 요약, 정리해주세요."},
#                 {"role": "user", "content": content}
#             ]
#         )
#         summary = response['choices'][0]['message']['content']
#         print("요약 완료")
#         return summary
#     except Exception as e:
#         print("요약 실패:", str(e))
#         return None


# # @api_view(['GET'])
# # @permission_classes([IsAuthenticated])
# # def home_view(request):
# #     user = request.user
# #     today = date.today()

# #     try:
# #         relation = UserParentRelation.objects.get(user=user)
# #         parent = relation.parent
# #     except UserParentRelation.DoesNotExist:
# #         return Response({"error": "연결된 어르신 정보가 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    
# #     # # 오늘의 DailyReport 요약
# #     # summarized_text = summarize_chat_logs(parent, today)
    
# #     # if summarized_text:
# #     #     # 기존 DailyReport가 있다면 삭제
# #     #     DailyReport.objects.filter(parent=parent, date=today).delete()

# #     #     # 새롭게 저장
# #     #     DailyReport.objects.create(
# #     #         parent=parent,
# #     #         date=today,
# #     #         summary=summarized_text,
# #     #         is_sent=False  # 처음 저장 시 미전송 상태
# #     #     )

# #     # # 대화시간 계산
# #     # talking_time = ChatLog.objects.filter(parent=parent).count() # 발화 한번당 1분이라고 간주 = 대화시간    
    
# #     # # 일정 수행 % 계산
# #     # today_events = Event.objects.filter(parent=parent, date=today)
# #     # event_total_count = today_events.count()

# #     # success_event_count = 0
# #     # for e in today_events:
# #     #     if e.is_checked == True:
# #     #         success_event_count += 1
        
# #     # if success_event_count == 0: # 제로디비전 에러 막기 위한 분기
# #     #     task_success_rate = 0
# #     # else:
# #     #     task_success_rate = int(success_event_count / event_total_count * 100)
    


# #     # 오늘의 스케줄 정렬
# #     events = Event.objects.filter(parent=parent, date=today).order_by('start_time')
# #     event_data = [
# #         {
# #             'title': e.title,
# #             'start_time': e.start_time,
# #             'end_time': e.end_time,
# #             'is_checked': e.is_checked
# #         } for e in events
# #     ]

# #     # 프론트에 내려줄 응답
