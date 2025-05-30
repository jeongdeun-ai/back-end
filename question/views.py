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
from django.utils.timezone import now

# 1번 - Parent 객체의 ContextSummary와 오늘 대화 기록을 바탕으로 오늘의 AI 추천 질문을 생성해주는 api
import json
import re

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_recommend_question(request):
    user = request.user
    today = now().date()

    # 보호자-어르신 관계 확인
    try:
        relation = UserParentRelation.objects.get(user=user)
        parent = relation.parent
    except UserParentRelation.DoesNotExist:
        return Response({"error": "해당 어르신 없음"}, status=404)

    # 오늘 대화 수 확인
    chat_logs = ChatLog.objects.filter(parent=parent, created_at__date=today).order_by('created_at')
    chat_count_now = chat_logs.count()

    if chat_count_now == 0:
        return Response({"error": "오늘 대화가 없습니다."}, status=400)

    # 기존에 저장된 질문이 있으면 재활용
    existing_question = Question.objects.filter(parent=parent, created_at__date=today).order_by('-created_at').first()
    if existing_question and existing_question.chat_count == chat_count_now:
        return Response({
            "question": existing_question.recommaned_question,
            "reason": existing_question.recommaned_reason
        }, status=200)

    # ContextSummary 불러오기
    try:
        context = ContextSummary.objects.get(parent=parent).content
    except ContextSummary.DoesNotExist:
        return Response({"error": "ContextSummary 없음"}, status=404)

    # 대화 로그 텍스트화
    chat_text = "\n".join([f"{log.sender}: {log.message}" for log in chat_logs])

    # 프롬프트 구성
    prompt = f"""
    다음은 GPT와 어르신의 오늘 대화 내용입니다.
    이 흐름을 참고하여 어르신에게 여쭤볼 수 있는 가장 합리적이고 적절한 질문 1개와 자세한 이유를 추천해주세요.

    조건:
    - 질문은 무조건 하나만.
    - 질문을 뽑을 땐 대화 내용과 어르신의 맥락 정보를 활용해서 뽑아주세요.
    - 해당 질문이 가장 적절하다고 생각하는 이유(reason)를 자세히 알려주세요.
    - 꼭 JSON 형태로 반환해야함:

    {{
        "question": "...",
        "reason": "..."
    }}

    어르신 맥락 정보:
    {context}

    오늘의 대화 내용:
    """
    {chat_text}
    """
    """

    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 노인 대상 대화 보조 챗봇이야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        content = response['choices'][0]['message']['content'].strip()

        try:
            question_obj = json.loads(content)
        except json.JSONDecodeError:
            cleaned = re.search(r"\{[\s\S]*?\}", content)
            if cleaned:
                question_obj = json.loads(cleaned.group())
            else:
                return Response({"error": "JSON 응답 형식 오류", "raw": content}, status=500)

        # 질문 저장
        new_question = Question.objects.create(
            parent=parent,
            recommaned_question=question_obj['question'],
            recommaned_reason=question_obj['reason'],
            chat_count=chat_count_now
        )

        return Response({
            "question": new_question.recommaned_question,
            "reason": new_question.recommaned_reason
        }, status=201)

    except Exception as e:
        return Response({"error": "GPT 요청 실패", "detail": str(e)}, status=500)
