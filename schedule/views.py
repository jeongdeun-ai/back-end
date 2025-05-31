from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


from table.models import *
from .serializers import *

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.db import IntegrityError
from django.db import transaction

# Open AI API 사용하기 위한 header
import os
from dotenv import load_dotenv
import openai

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from datetime import datetime
from django.http import HttpResponse
import base64

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

# 1번 - 보호자인 User가 Parent의 일정을 추가하는 API
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # 로그인 인증!
def add_event_for_parent(request):
    user = request.user 

    # 프론트한테 받아야 하는 것
    # title, date(YYYY-MM-DD), start_time(HH:MM:SS), end_time(HH:MM:SS)
    
    try:
        relation = UserParentRelation.objects.get(user=user)
        parent = relation.parent # User와 연결된 어르신 정보 가져오기
    except UserParentRelation.DoesNotExist:
        return Response({"error":"등록된 어르신 정보가 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    
    data = request.data  #프론트로부터 받은 데이터들 여기에!

    try:
        Event.objects.create(
            parent = parent,
            title = data.get('title'),
            date = data.get("date"),
            start_time = data.get("start_time"),
            end_time = data.get("end_time"),
        )

        context = {
            "message" : "새로운 일정이 추가되었습니다.",
            "parent_name" : parent.name,
            "title" : str(data.get('title')),
            "date" : data.get('date'),
            "start_time" : data.get("start_time"),
            "end_time" : data.get("end_time"),
        }

        return Response(context, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error":str(e)}, status=status.HTTP_400_BAD_REQUEST)


# 2번 - 프론트로부터 특정 날짜 파라미터로 전달 받고, 그 날 일정을 전부 GET으로 보내기
@api_view(["GET"])
@permission_classes([IsAuthenticated]) 
def get_events_for_specific_date(request):
    user = request.user
    target_date = request.query_params.get('date')  # 예: '2025-05-27'

    try:
        relation = UserParentRelation.objects.get(user=user)
        parent = relation.parent
    except UserParentRelation.DoesNotExist:
        return Response({"error":"등록된 어르신 정보가 없습니다."}, status=status.HTTP_404_NOT_FOUND)
    
    events = Event.objects.filter(parent=parent, date=target_date).order_by('start_time')

    serializer = GetEventsForSpecificDateSerializers(events, many=True)

    return Response(serializer.data, status = status.HTTP_200_OK)



# 3번 - User와 대응되는 Parent의 복약 일정 전부 가져오기! (GET)
# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def get_medicine_plan(request):
#     user = request.user

#     try:
#         relation = UserParentRelation.objects.get(user=user)
#         parent = relation.parent
#     except UserParentRelation.DoesNotExist:
#         return Response({"error": "해당 어르신 없음"}, status=status.HTTP_404_NOT_FOUND)

#     schedules = MedicationSchedule.objects.filter(parent=parent)
    
#     result = []
#     for schedule in schedules:
#         items = schedule.medication_item.all()  # related_name='medication_item'
#         item_list = [
#             {
#                 "name": item.name,
#                 "dose": item.dose
#             } for item in items
#         ]
#         result.append({
#             "time_slot": schedule.time_slot,
#             "items": item_list
#         })

#     return Response(result, status=status.HTTP_200_OK)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_medicine_plan(request):
    user = request.user

    try:
        relation = UserParentRelation.objects.get(user=user)
        parent = relation.parent
    except UserParentRelation.DoesNotExist:
        return Response({"error": "해당 어르신 없음"}, status=status.HTTP_404_NOT_FOUND)

    schedules = MedicationSchedule.objects.filter(parent=parent)

    result = []
    for schedule in schedules:
        items = schedule.medication_item.all()
        item_list = [
            {
                "name": item.name,
                "dose": item.dose
            } for item in items
        ]
        result.append({
            "time_slot": schedule.time_slot,
            "items": item_list
        })

    # ✅ 여기서 "schedules" 키로 감싸줌
    return Response({"schedules": result}, status=status.HTTP_200_OK)


# 4번 - User가 자신의 Parent의 복약 일정 추가하기! (POST)
# 복용약 정보 추가할 때 어떤 방식으로 할지 고민
# 프론트로부터 받아야 할 때 이런식의 json으로 만들기 
# {
#   "schedules": [
#     {
#       "time_slot": "morning",
#       "items": [
#         {"name": "비타민C", "dose": "1정"},
#         {"name": "감기약", "dose": "1정"}
#       ]
#     },
#     {
#       "time_slot": "lunch",
#       "items": [
#         {"name": "아미노산", "dose": "2포"},
#         {"name": "감기약", "dose": "1정"}
#       ]
#     }
#   ]
# }
@api_view(['POST']) # PUT, PATCH 따로 만들 필요 없이 이 view 하나로 끝내버리기!
@permission_classes([IsAuthenticated])
def add_medicine_items(request):
    user = request.user
    data = request.data

    try:
        relation = UserParentRelation.objects.get(user=user)
        parent = relation.parent
    except UserParentRelation.DoesNotExist:
        return Response({'error': 'Parent not found.'}, status=status.HTTP_404_NOT_FOUND)

    schedules = data.get("schedules", [])

    for schedule_data in schedules:
        time_slot = schedule_data.get("time_slot")
        items = schedule_data.get("items", [])

        # 기존 스케줄 삭제 (있으면)
        MedicationSchedule.objects.filter(parent=parent, time_slot=time_slot).delete()

        # MedicationSchedule 생성
        schedule = MedicationSchedule.objects.create(
            parent=parent,
            time_slot=time_slot
        )

        # 각각의 약 저장
        for item in items:
            MedicationItem.objects.create(
                medication_schedule=schedule,
                name=item.get("name"),
                dose=item.get("dose")
            )

    return Response({"message": "약 복용 스케줄 저장 완료"}, status=status.HTTP_201_CREATED)
