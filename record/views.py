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

from datetime import date

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')


# 대화시간 산출하는 함수
def get_total_chat_time(parent, target_date):
    """
    어르신이 특정 날짜에 나눈 전체 대화 횟수를 분 단위로 반환 (1 발화 = 1분)
    """
    talking_time = ChatLog.objects.filter(
        parent=parent,
        timestamp__date=target_date  # ✅ 핵심: 날짜만 필터링
    ).count()
    return talking_time


# 일정 수행률 반환하는 함수
def get_event_success_ratio(parent, target_date):
    today_events = Event.objects.filter(parent=parent, date=target_date)
    event_total_count = today_events.count()

    success_event_count = 0
    for e in today_events:
        if e.is_checked == True:
            success_event_count += 1
        
    if success_event_count == 0: # 제로디비전 에러 막기 위한 분기
        return 0
    else:
        task_success_rate = int(success_event_count / event_total_count * 100)
        return task_success_rate


# 대화 내용 요약해주는 함수
def summarize_chat_logs(parent, target_date):
    """
    특정 날짜의 ChatLog를 기반으로 GPT에게 요약을 요청하고 요약된 텍스트를 반환합니다.
    
    :param parent: Parent 객체
    :param target_date: datetime.date 객체 (예: date.today())
    :return: 요약된 텍스트 (str) / 대화 없을 시 None 반환
    """
    chat_logs = ChatLog.objects.filter(
        parent=parent,
        timestamp__date=target_date
    ).order_by('timestamp')

    if not chat_logs.exists():
        print("대화 기록 없음")
        return None

    # 대화 내용을 문자열로 구성
    content = ""
    for chat in chat_logs:
        sender_label = "어르신" if chat.sender == "parent" else "GPT"
        content += f"{sender_label}: {chat.message}\n"

    # GPT 요약 요청
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "다음은 하루 동안의 GPT와 사용자 대화입니다. 여기서 GPT와 대화하는 어르신에 중점을 둔 채로 전체 대화를 요약, 정리해주세요."},
                {"role": "user", "content": content}
            ]
        )
        summary = response['choices'][0]['message']['content']
        print("요약 완료")
        return summary
    except Exception as e:
        print("요약 실패:", str(e))
        return None


# 1번 뷰 - 특정 날짜를 프론트로부터 받아서 해당 날짜의 데일리 리포트 생성하기!
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_target_date_record(request):
    user = request.user
    target_date = request.query_params.get('date')  # 예: '2025-05-27'

    try:
        relation = UserParentRelation.objects.get(user=user)
        parent = relation.parent
    except UserParentRelation.DoesNotExist:
        return Response({"error":"해당 어르신 없음"}, status=status.HTTP_404_NOT_FOUND)


    # 1. 이미 발송된 리포트가 있으면 덮어쓰기 금지!!
    existing_report = DailyReport.objects.filter(parent=parent, date=target_date, is_sent=True).first()
    if existing_report:
        # # # 여기서 기존에 발송된 리포트가 있으면 그 객체를 반환!! 
        serializer = DailyReportSerializers(existing_report)

        return Response(serializer.data, status=status.HTTP_200_OK)


    # target_date의 DailyReport 요약
    summarized_text = summarize_chat_logs(parent, target_date)
    if summarized_text is None:
        print("GPT 요약 실패: 대화 없음 또는 오류")
        return Response({"error": "요약 생성 실패 (대화 없음 또는 GPT 오류)"}, status=status.HTTP_400_BAD_REQUEST)

    # 대화 시간 & 일정 성공률 계산
    total_chat_time = get_total_chat_time(parent, target_date)
    event_success_ratio = get_event_success_ratio(parent, target_date)

    # 4. 감정 추출 요청
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
    
    # target_date가 today면 -> is_sent_flag = False
    # target_date 가 today보다 이전 날이면 -> is_sent_flag = True
    is_sent_flag = True if target_date < date.today() else False  # 이거 핵심!!

    # 6. 기존 리포트 삭제 후 새로 생성
    DailyReport.objects.filter(parent=parent, date=target_date).delete()
    DailyReport.objects.create(
        parent=parent,
        date=target_date,
        summary=summarized_text,
        is_sent=is_sent_flag,
        total_chat_time=total_chat_time,
        event_success_ratio=event_success_ratio,
        parent_emotion=emotion,
    )

    return Response({
        "message": "DailyReport 생성 완료",
        "summary": summarized_text,
        "emotion": emotion,
        "chat_time": total_chat_time,
        "task_success_rate": event_success_ratio
    }, status=status.HTTP_201_CREATED)

  
