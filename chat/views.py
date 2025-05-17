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

# gpt에게 Parent 객체의 핵심 정보를 넘겨주고 가장 적절한 질문 텍스트 생성하는 함수
def generate_question_for_parent(parent):
    """
    Parent 객체의 가장 최신 ContextSummary 기반으로 GPT가 질문 생성
    """
    try:
        latest_context = parent.context_summary.latest('created_at')
        context_text = latest_context.content
    except ContextSummary.DoesNotExist:
        context_text = "이전 대화 정보가 없습니다."

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


# GPT가 질문 생성 → Parent에게 질문하는 View
@api_view(['POST'])
def gpt_ask_parent(request):

    parent_id = request.data.get('parent_id')

    if not parent_id:
        return Response({'error': 'parent_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        parent = Parent.objects.get(id=parent_id)
    except Parent.DoesNotExist:
        return Response({'error': 'Parent not found.'}, status=status.HTTP_404_NOT_FOUND)

    # GPT 질문 생성 (핵심 정보 포함)
    question_text = generate_question_for_parent(parent) # 위에서 만든 함수 사용

    # ChatLog에 저장 (GPT 발화)
    ChatLog.objects.create(parent=parent, sender='gpt', message=question_text)

    # 해당 GPT 발화를 음성 파일로도 전환하고, 그 파일을 AWS S3 저장소에 저장해야함
    #
    #
    #

    # 여기서 텍스트랑 음성 파일 둘 다 줘야
    return Response({'question_text': question_text}, status=status.HTTP_200_OK) 




# Parent가 GPT에게 답변 → 답변 저장 + 핵심 정보 저장 View