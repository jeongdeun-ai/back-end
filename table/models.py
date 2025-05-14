from django.db import models
from django.conf import settings

from django.contrib.auth.models import AbstractUser

# 보호자 릴레이션
class User(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True)


# 어르신 릴레이션
class Parent(models.Model):
    name = models.CharField(max_length=100)
    birth_date = models.DateField()
    disease_info = models.TextField(blank=True)
    medication_info = models.TextField(blank=True)
    additional_notes = models.TextField(blank=True)


# 보호자와 어르신의 일대일 연결 관계 릴레이션
class UserParentRelation(models.Model):
    user = models.ForeignKey(User, related_name='user_parent_relation', on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, related_name='user_parent_relation', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user'),
            models.UniqueConstraint(fields=['parent'], name='unique_parent')
        ]

# 채팅 기록 릴레이션
class ChatLog(models.Model):
    parent = models.ForeignKey(Parent,related_name='chat_log', on_delete=models.CASCADE)
    sender = models.CharField(
        max_length=10,
        choices=[
            ('parent', 'Parent'),
            ('gpt', 'GPT'),
        ]
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


# 데일리 리포트 요약 릴레이션
class DailyReport(models.Model):
    parent = models.ForeignKey(Parent, related_name='daily_report', on_delete=models.CASCADE)
    date = models.DateField()  # 예: 2025-05-09, 하루에 한 번 요약해서 저장
    summary = models.TextField()  # GPT 요약 결과
    created_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)  # 보호자에게 발송 완료 여부


# GPT API시 전달할 핵심 문맥 요약 릴레이션
class ContextSummary(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='context_summary')
    content = models.TextField()  # GPT가 참고할 핵심 요약 내용
    created_at = models.DateTimeField(auto_now_add=True)