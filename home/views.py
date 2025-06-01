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
from django.http import HttpResponse
import base64

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import date

from table.models import ChatLog
import openai
from django.utils.timezone import now

## import 해올 것들 리스트 ##

# def get_total_chat_time(parent, target_date)
# def get_event_success_ratio(parent, target_date)
# def summarize_chat_logs(parent, target_date)

from record.views import get_total_chat_time, get_event_success_ratio, summarize_chat_logs
from record.serializers import DailyReportSerializers

# 1번 - 데일리 레포트의 약식 정보들을 현재 시간 기준 최신화 하기!
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_daily_report_update(request):

    user = request.user
    today_date = date.today().isoformat()  # 결과: '2025-05-27' 

    try:
        relation = UserParentRelation.objects.get(user=user)
        parent = relation.parent
    except UserParentRelation.DoesNotExist:
        return Response({"error":"해당 어르신 없음"}, status=status.HTTP_404_NOT_FOUND)


    # 대화 시간 & 일정 성공률 계산
    total_chat_time = get_total_chat_time(parent, today_date)
    event_success_ratio = get_event_success_ratio(parent, today_date)
    
    todays_report = DailyReport.objects.filter(parent=parent, date=today_date).first()

    if todays_report is None: # 만약 현재 레포트가 존재하지 않는다면~ 감정 추출까지 해서 새롭게 만들어야 함
        # 4. 감정 추출 요청

        # today_date의 DailyReport 요약
        summarized_text = summarize_chat_logs(parent, today_date)
        if summarized_text is None:
            print("GPT 요약 실패: 대화 없음 또는 오류")
            return Response({"error": "요약 생성 실패 (대화 없음 또는 GPT 오류)"}, status=status.HTTP_400_BAD_REQUEST)

        openai.api_key = os.getenv("OPENAI_API_KEY")
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "다음은 어르신과 GPT의 하루 대화 요약입니다. 이 텍스트를 기반으로 어르신의 감정을 happy, sad, anxious, angry, neutral 중 하나로 추정해주세요. 다른 말 없이 딱 그 중 하나의 단어만 반환하세요."
                    },
                    {
                        "role": "user",
                        "content": summarized_text
                    }
                ]
            )
            emotion = response['choices'][0]['message']['content'].strip()

            # 5. 감정 결과 유효성 검사
            allowed_emotions = {"happy", "sad", "anxious", "angry", "neutral"}
            if emotion not in allowed_emotions:
                print(f"GPT 감정 응답 '{emotion}' 은 유효하지 않아 'neutral'로 대체함")
                emotion = "neutral"

        except Exception as e:
            print("감정 분석 실패:", str(e))
            return Response({"error": "감정 분석 실패"}, status=status.HTTP_400_BAD_REQUEST)
        
        DailyReport.objects.create(
        parent=parent,
        date=today_date,
        summary=summarized_text,
        is_sent=False,
        total_chat_time=total_chat_time,
        event_success_ratio=event_success_ratio,
        parent_emotion=emotion,
        )

        return Response({
            "message": "DailyReport 생성 완료",
            "chat_time": total_chat_time,
            "task_success_rate": event_success_ratio,
            "emotion": emotion
        }, status=status.HTTP_201_CREATED)
      
    else:
    # 여긴 기존에 레포트가 있긴 한 것

        todays_report.total_chat_time = total_chat_time
        todays_report.event_success_ratio = event_success_ratio
        todays_report.save() 

        current_emotion = todays_report.parent_emotion
        
        return Response({
            "message": "DailyReport 반환 완료",
            "chat_time": total_chat_time,
            "task_success_rate": event_success_ratio,
            "emotion": current_emotion
        }, status=status.HTTP_200_OK)
    

# 2번 - parent 신상 정보와 오늘 하루 일정 반환하기!
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_parent_event_info(request):
    user = request.user
    today_date = date.today().isoformat()  # 오늘 날짜!!
    try:
        relation = UserParentRelation.objects.get(user=user)
        parent = relation.parent
    except UserParentRelation.DoesNotExist:
        return Response({"error":"해당 어르신 없음"}, status=status.HTTP_404_NOT_FOUND)
    
    # parent 정보 반환할 것들!
    parent_info = {
        "name" : parent.name,
        "photo_url": request.build_absolute_uri(parent.photo.url) if parent.photo else None,
        "birth_date" : parent.birth_date,
    }
 

    # 일정 정보 
    todays_events = Event.objects.filter(parent=parent, date=today_date).order_by('start_time') # 아래로 오름차순이 되도록 정렬

    # 3. 일정 정보 구성
    if not todays_events.exists():
        event_info = {
            "message": "오늘 등록된 일정이 없습니다."
        }
    else:
        event_info = {
            "events": [
                {
                    "title": event.title,
                    "start_time": event.start_time.strftime("%H:%M"),
                    "end_time": event.end_time.strftime("%H:%M") if event.end_time else None,
                    "is_checked": event.is_checked
                }
                for event in todays_events
            ]
        }

    # 4. 응답 반환
    return Response({
        "parent_info": parent_info,
        "event_info": event_info
    }, status=status.HTTP_200_OK)


