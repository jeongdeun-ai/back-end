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
from openai import OpenAI

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from datetime import datetime
from django.http import HttpResponse
import base64
from io import BytesIO


load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')


# 이 페이지에 있는 wav 내용을 mp3로 꼭 바꾸기!!

# gpt에게 Parent 객체의 핵심 정보를 넘겨주고 가장 적절한 질문 텍스트 생성하는 함수
def generate_initial_question(parent):
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
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{parent.name}님에게 지금 가장 적절한 질문을 만들어줘."}
            ],
            max_tokens=200,
            temperature=0.7,
        )
        question_text = response.choices[0].message.content.strip()

        if not question_text:
            return None
        elif len(question_text) > 4000:
            question_text = question_text[:4000]

        return question_text

    except Exception as e:
        print("GPT 오류:", e)
        return None


# 2. 어르신 응답 → 그에 대한 GPT 반응 생성
def generate_reply_and_followup(parent, user_message):
    """
    어르신의 최근 발화(user_message)를 바탕으로 GPT가 따뜻한 반응 + 다음 질문을 생성

    - parent: Parent 객체
    - user_message: 어르신이 GPT 질문에 대해 한 응답 (문자열)
    - return: GPT가 생성한 반응 + 다음 질문 텍스트 (문자열)
    """

    try:
        latest_context = parent.context_summary.latest('created_at')
        context_text = latest_context.content
    except parent.context_summary.model.DoesNotExist:
        context_text = "이전에 저장된 어르신 정보가 없습니다."

    # 시스템 프롬프트 설계
    system_prompt = f"""
너는 치매 증상이 있는 어르신 {parent.name}님의 가상 자녀 역할을 맡은 AI야.

너의 역할은 다음과 같아:
1. 어르신의 말에 따뜻하게 공감하고,
2. 어르신이 혼란스럽지 않도록 짧고 명확하게 반응하며,
3. 자연스럽게 다음 질문으로 이어가는 것.

아래는 {parent.name}님에 대한 참고 정보야:
\"\"\"
{context_text}
\"\"\"

이번에 어르신이 이렇게 말씀하셨어:
\"{user_message}\"

이 응답을 기반으로:
- 진심 어린 리액션을 하고
- 대화를 이어갈 수 있는 다음 질문을 한 문장으로 만들어줘.
- 말투는 존댓말로 하고 너무 길거나 복잡한 표현은 피해야 해.
- 처음 말은 반응, 그 다음 문장은 질문.

예시)
“아 그렇군요 아버님, 오늘 아침은 입맛이 없으셨군요. 혹시 점심은 조금 드셨을까요?”

"""

    # GPT API 호출
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{parent.name}님의 응답에 적절한 반응과 다음 질문을 해줘."}
            ],
            max_tokens=200,
            temperature=0.7,
        )
    except Exception as e: 
        return Response({"error": "GPT API 호출 실패"}, status=status.HTTP_400_BAD_REQUEST)
    
    return response.choices[0].message.content


#1. GPT가 질문 생성 → Parent에게 질문하는 View
from django.utils.timezone import now

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gpt_ask_parent(request):
    user = request.user

    try:
        relation = UserParentRelation.objects.get(user=user)
        parent = relation.parent
    except UserParentRelation.DoesNotExist:
        return Response({'error': 'Parent not found.'}, status=status.HTTP_404_NOT_FOUND)

    today = now().date()

    # 오늘 GPT 발화가 있었는지 확인
    is_first_today = not ChatLog.objects.filter(parent=parent, sender='gpt', timestamp__date=today).exists()

    # 질문 생성
    if is_first_today:
        question_text = generate_initial_question(parent)
    else:
        try:
            latest_user_msg = ChatLog.objects.filter(parent=parent, sender='parent').latest('timestamp').message
        except ChatLog.DoesNotExist:
            return Response({'error': '대화 기록 없음'}, status=status.HTTP_404_NOT_FOUND)
        question_text = generate_reply_and_followup(parent, latest_user_msg)

    # GPT 발화 저장
    ChatLog.objects.create(parent=parent, sender='gpt', message=question_text)

    # TTS 변환 (최신 SDK 방식)
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        tts_response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=question_text,
            response_format="mp3",
        )
        audio_content = tts_response.read()
        encoded_audio = base64.b64encode(audio_content).decode('utf-8')

    except Exception as e:
        print("TTS 실패:", e)
        return Response({'error': 'TTS 변환 실패'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'question_text': question_text,
        'audio_base64': encoded_audio,
        'is_first_today': is_first_today,
    }, status=status.HTTP_200_OK)


# #2. Parent가 GPT에게 답변 → 답변 저장 + 핵심 정보 저장 View
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def parent_reply_to_gpt(request):
    
#     user = request.user
#     audio_base64 = request.data.get('audio_base64')

#     try:
#         relation = UserParentRelation.objects.get(user = user)
#         parent = relation.parent
#     except UserParentRelation.DoesNotExist:
#         return Response({'error': 'Parent not found.'}, status=status.HTTP_404_NOT_FOUND)

#     # 1. base64 → 바이너리 변환
#     try:
#         audio_bytes = base64.b64decode(audio_base64)
#     except Exception as e:
#         return Response({'error': f'Invalid base64 audio: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

#     # 2. Whisper STT 요청 (OpenAI API)
#     client = openai.OpenAI(api_key=openai_api_key)

#     from io import BytesIO
#     audio_file = BytesIO(audio_bytes)
#     audio_file.name = 'voice.mp3'  # 파일 이름은 필수 (확장자 포함)

#     try:
#         transcript_response = client.audio.transcriptions.create(
#             model="whisper-1",
#             file=audio_file,
#             response_format="text"
#         )
#     except Exception as e:
#         return Response({'error': f'STT failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     user_message = transcript_response.strip()

#     # 3. 어르신 응답 ChatLog에 저장
#     ChatLog.objects.create(parent=parent, sender='parent', message=user_message)

#     # 4. GPT에게 요약 요청
#     summary_prompt = f"""
# 너는 치매 어르신과 대화하는 챗봇 AI야.

# 아래는 어르신이 방금 한 발화야:
# \"\"\"
# {user_message}
# \"\"\"

# 너의 역할은 다음과 같아:
# 1. 어르신의 발화 내용에서 **건강 상태**, **기분**, **식사 여부**, **복약 여부**와 관련된 **핵심 정보만** 추출한다.
# 2. 발화가 장황하거나 반복되더라도, 중요한 내용만 뽑아 **간결하고 핵심적으로 요약**한다.
# 3. **추측, 감정 유도, 의도 해석은 하지 않고**, 어르신이 말한 내용 그대로 요약한다.
# 4. **말투는 제3자 보고 형식**으로 작성하며, 예를 들면 다음과 같다:
#    - “기분이 우울하다고 하심”
#    - “점심은 드시지 않았다고 함”
#    - “약은 아직 복용하지 않으셨다고 함”

# 이 기준에 맞춰 다음 발화 내용을 요약해줘.
# """

#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {"role": "system", "content": summary_prompt},
#             {"role": "user", "content": "어르신의 응답 내용을 요약해줘."}
#         ],
#         max_tokens=150,
#         temperature=0.4,
#     )

#     summary_text = response.choices[0].message.content.strip()

#     # 5. ContextSummary 저장 (기존에 있으면 이어쓰기)
#     latest_context = ContextSummary.objects.filter(parent=parent).order_by('-created_at').first()
#     if latest_context:
#         latest_context.content = f"{latest_context.content.strip()}\n\n{summary_text}"
#         latest_context.created_at = now()
#         latest_context.save()
#     else:
#         ContextSummary.objects.create(parent=parent, content=summary_text)

#     # 6. 응답 반환
#     return Response({"message": "응답이 정상적으로 저장되었습니다."}, status=status.HTTP_200_OK)


client = OpenAI(api_key=openai_api_key)
# 2. Parent가 GPT에게 답변 → 답변 저장 + 핵심 정보 저장 View (이건 tts 이후 mp3 인코딩하여 반환)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def parent_reply_to_gpt(request):
    user = request.user
    audio_base64 = request.data.get('audio_base64')

    # 1. 보호자와 연결된 어르신 찾기
    try:
        relation = UserParentRelation.objects.get(user=user)
        parent = relation.parent
    except UserParentRelation.DoesNotExist:
        return Response({'error': 'Parent not found.'}, status=status.HTTP_404_NOT_FOUND)

    # 2. base64 → Bytes 변환
    try:
        audio_bytes = base64.b64decode(audio_base64)
        audio_file = BytesIO(audio_bytes)
        audio_file.name = 'voice.mp3'  # Whisper 모델용
    except Exception as e:
        return Response({'error': f'Invalid base64 audio: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    # 3. Whisper STT 요청
    try:
        transcript_response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        user_message = transcript_response.strip()
    except Exception as e:
        return Response({'error': f'STT failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 4. 어르신 발화 저장
    ChatLog.objects.create(parent=parent, sender='parent', message=user_message)

    # 5. GPT 요약 요청
    system_prompt = f"""
너는 치매 어르신과 대화하는 챗봇 AI야.

아래는 어르신이 방금 한 발화야:
\"\"\"
{user_message}
\"\"\"

너의 역할은 다음과 같아:
1. 어르신의 발화 내용에서 **건강 상태**, **기분**, **식사 여부**, **복약 여부**와 관련된 **핵심 정보만** 추출한다.
2. 발화가 장황하거나 반복되더라도, 중요한 내용만 뽑아 **간결하고 핵심적으로 요약**한다.
3. **추측, 감정 유도, 의도 해석은 하지 않고**, 어르신이 말한 내용 그대로 요약한다.
4. **말투는 제3자 보고 형식**으로 작성하며, 예를 들면 다음과 같다:
   - “기분이 우울하다고 하심”
   - “점심은 드시지 않았다고 함”
   - “약은 아직 복용하지 않으셨다고 함”
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "어르신의 응답 내용을 요약해줘."}
            ],
            max_tokens=150,
            temperature=0.4,
        )
        summary_text = response.choices[0].message.content.strip()
    except Exception as e:
        return Response({'error': f'GPT 요약 실패: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 6. ContextSummary 저장
    latest_context = ContextSummary.objects.filter(parent=parent).order_by('-created_at').first()
    if latest_context:
        latest_context.content = f"{latest_context.content.strip()}\n\n{summary_text}"
        latest_context.created_at = now()
        latest_context.save()
    else:
        ContextSummary.objects.create(parent=parent, content=summary_text)

    return Response({"message": "응답이 정상적으로 저장되었습니다."}, status=status.HTTP_201_CREATED)


# # 이거 실험용 코드!!(mp3 파일 자체를 받아서 하기)
# from io import BytesIO
# from django.utils.timezone import now
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def parent_reply_to_gpt(request):
#     user = request.user
#     audio_file = request.FILES.get("audio")  # mp3 파일

#     # 1. 보호자와 연결된 어르신 찾기
#     try:
#         relation = UserParentRelation.objects.get(user=user)
#         parent = relation.parent
#     except UserParentRelation.DoesNotExist:
#         return Response({'error': 'Parent not found.'}, status=status.HTTP_404_NOT_FOUND)

#     # 2. 파일을 BytesIO로 변환
#     try:
#         audio_bytes = audio_file.read()
#         audio_stream = BytesIO(audio_bytes)
#         audio_stream.name = "voice.mp3"  # Whisper API용 파일명 필수
#     except Exception as e:
#         return Response({'error': f'파일 처리 실패: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

#     # 3. Whisper STT 요청
#     try:
#         transcript_response = client.audio.transcriptions.create(
#             model="whisper-1",
#             file=audio_stream,
#             response_format="text"
#         )
#         user_message = transcript_response.strip()
#     except Exception as e:
#         return Response({'error': f'STT failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     # 4. 어르신 발화 저장
#     ChatLog.objects.create(parent=parent, sender='parent', message=user_message)

#     # 5. GPT 요약 요청
#     system_prompt = f"""
# 너는 치매 어르신과 대화하는 챗봇 AI야.

# 아래는 어르신이 방금 한 발화야:
# \"\"\"
# {user_message}
# \"\"\"

# 너의 역할은 다음과 같아:
# 1. 어르신의 발화 내용에서 **건강 상태**, **기분**, **식사 여부**, **복약 여부**와 관련된 **핵심 정보만** 추출한다.
# 2. 발화가 장황하거나 반복되더라도, 중요한 내용만 뽑아 **간결하고 핵심적으로 요약**한다.
# 3. **추측, 감정 유도, 의도 해석은 하지 않고**, 어르신이 말한 내용 그대로 요약한다.
# 4. **말투는 제3자 보고 형식**으로 작성하며, 예를 들면 다음과 같다:
#    - “기분이 우울하다고 하심”
#    - “점심은 드시지 않았다고 함”
#    - “약은 아직 복용하지 않으셨다고 함”
# """

#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": "어르신의 응답 내용을 요약해줘."}
#             ],
#             max_tokens=150,
#             temperature=0.4,
#         )
#         summary_text = response.choices[0].message.content.strip()
#     except Exception as e:
#         return Response({'error': f'GPT 요약 실패: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     # 6. ContextSummary 저장
#     latest_context = ContextSummary.objects.filter(parent=parent).order_by('-created_at').first()
#     if latest_context:
#         latest_context.content = f"{latest_context.content.strip()}\n\n{summary_text}"
#         latest_context.created_at = now()
#         latest_context.save()
#     else:
#         ContextSummary.objects.create(parent=parent, content=summary_text)

#     return Response({"message": "응답이 정상적으로 저장되었습니다."}, status=status.HTTP_200_OK)
