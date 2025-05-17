from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from table.models import *
from serializers import *

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.db import IntegrityError
from django.db import transaction

# Open AI API 사용하기 위한 header
import os
from dotenv import load_dotenv
import openai

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

# gpt에게 Parent 객체의 핵심 정보를 넘겨주고 가장 적절한 질문 텍스트 받아오기!
def generate_question_for_parent(parent):
    """
    특정 Parent 정보를 기반으로 GPT가 질문 생성
    """
    # Parent context 기반 질문 생성 (ContextSummary 사용 가능)
    context_list = parent.context_summary.order_by('-created_at')[:5]  # 최신 5개 context 참고 (원하면 더 늘려도 됨)
    context_text = "\n".join([c.content for c in context_list])

    system_prompt = f"""너는 치매 노인인 {parent.name} 님의 가상 자식 역할을 하는 AI야.
이전에 대화한 주요 정보:
{context_text}

{parent.name}님께 오늘 하루 인사와 건강 상태, 최근 식사, 복약 여부 등을 따뜻하게 질문해줘.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "오늘 어떤 질문을 드릴까요?"}
        ],
        max_tokens=300,
        temperature=0.7,
    )

    question = response['choices'][0]['message']['content']
    return question

