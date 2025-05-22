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

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from datetime import datetime
from django.http import HttpResponse
import base64

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

# gpt에게 Parent 객체의 핵심 정보를 넘겨주고 가장 적절한 질문 텍스트 생성하는 함수
def generate_question_for_parent(parent):
    """
    GPT가 Parent에게 할 적절한 질문을 생성하되, 어르신에 대한 정보를 바탕으로 맞춤형으로 설계함.
    """
    try:
        latest_context = parent.context_summary.latest('created_at')
        context_text = latest_context.content
    except parent.context_summary.model.DoesNotExist:
        context_text = "해당 어르신에 대한 정보가 충분하지 않습니다."

    system_prompt = f"""
너는 치매 증상이 있는 어르신 {parent.name}님의 가상 자녀 역할을 맡은 AI야.

목표는 다음과 같아:
1. {parent.name}님이 따뜻하고 편안하게 느끼도록 자연스럽게 말을 건넨다.
2. 오늘 하루 기분, 건강 상태, 식사 여부, 복약 여부 등을 자연스럽게 확인한다.
3. 같은 내용의 반복을 피하고, 어르신의 상태에 따라 적절한 질문을 만들어야 한다.

다음은 {parent.name}님에 대한 정보들이야. 이 정보를 최대한 활용해서 지금 상황에 맞는 최선의 질문을 만들어줘:
\"\"\"
{context_text}
\"\"\"

질문은 한 문장으로 만들어줘.
반드시 존댓말을 사용하고, 너무 길지 않게 해줘.
"""

    client = openai.OpenAI(api_key=openai_api_key)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{parent.name}님에게 지금 가장 적절한 질문을 만들어줘."}
        ],
        max_tokens=150,
        temperature=0.7,
    )

    return response.choices[0].message.content

# gpt의 질문에 대한 Parent 객체의 답변을 듣고 이거에 대한 답변을 다시 생성하는 함수






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
    # 또는 wav 파일 자체를 넘겨줘도 됨. 지금 코드는 후자로 결정!
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.audio.speech.create(
        model="tts-1",  # 또는 "tts-1-hd"
        voice="nova",  # "nova", "shimmer", "echo", "fable", "onyx", "alloy" 등
        input=question_text,
        response_format="wav",
    )

    audio_content = response.read()

    # 파일 직접 응답 (Content-Disposition: attachment 사용 가능)
    response = HttpResponse(audio_content, content_type='audio/wav') # Content-Type: audio/wav
    response['Content-Disposition'] = 'inline; filename="question.wav"'  # or attachment
    response['X-Question-Text'] = question_text  # 필요 시 커스텀 헤더로 텍스트도 전달 가능


    audio_content = response.read()

    # Base64로 인코딩해서 JSON으로 넘기기
    encoded_audio = base64.b64encode(audio_content).decode('utf-8')  #지금 상황엔 Base64 방식이 제일 적합해 보여. 프론트에서 바로 <audio>로 재생도 쉽게 할 수 있어.

    return Response({
        'question_text': question_text,
        'audio_base64': encoded_audio,
    }, status=200)


# Parent가 GPT에게 답변 → 답변 저장 + 핵심 정보 저장 View