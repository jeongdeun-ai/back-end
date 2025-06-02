from django.db import models
from django.conf import settings

from django.contrib.auth.models import AbstractUser

# 보호자 릴레이션
class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone_number']  # username은 장고 기본 필수 필드

    def __str__(self):
        return f"{self.email} ({self.username})"

# 어르신 릴레이션
class Parent(models.Model):
    SEX_CHOICE = [
        ('M', '남성'),
        ('F', '여성'),
    ]

    name = models.CharField(max_length=100)
    birth_date = models.DateField()
    sex = models.CharField(max_length=1, choices=SEX_CHOICE) # 성별 정보
    photo = models.ImageField(upload_to="photos/", null=True, blank=True)
    address = models.TextField(blank=True, null=True) # 어르신 주소
    disease_info = models.TextField(blank=True)
    medication_info = models.TextField(blank=True, null=True)
    additional_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} 어르신"


# 보호자와 어르신의 일대일 연결 관계 릴레이션
class UserParentRelation(models.Model):

    RELATION_CHOICES = [
        ('son', '아들'),
        ('daughter', '딸'),
        ('grandchild', '손자/손녀'),
        ('nephew', '조카'),
        ('other', '기타'),
    ]

    user = models.ForeignKey(User, related_name='user_parent_relation', on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, related_name='user_parent_relation', on_delete=models.CASCADE)
    relation_type = models.CharField(max_length=20, choices=RELATION_CHOICES) 
    ai_name_called = models.CharField(max_length=40)  # ai 부를 호칭
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user'),
            models.UniqueConstraint(fields=['parent'], name='unique_parent')
        ]
    
    def __str__(self):
        return f"{self.user.username}과 {self.parent.name}의 관계 릴레이션"

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
    timestamp = models.DateTimeField(auto_now_add=True) # 여긴 연-월-일-시-분-초 다 포함되어있는 정보

    def __str__(self):
        return f"sender: {self.sender} / {self.parent.name}와 대화 {self.timestamp}"

# 데일리 리포트 요약 릴레이션
class DailyReport(models.Model):

    EMOTION_CHOICES = [
        ('happy', '행복'),
        ('sad', '슬픔'),
        ('anxious', '불안'),
        ('angry', '분노'),
        ('neutral', '보통'),
    ]

    parent = models.ForeignKey(Parent, related_name='daily_report', on_delete=models.CASCADE)
    date = models.DateField()  # 예: 2025-05-09, 하루에 한 번 요약해서 저장
    summary = models.TextField()  # GPT 요약 결과
    created_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)  # 보호자에게 발송 완료 여부
    total_chat_time = models.IntegerField(default=0) # 총 대화 시간 (분 단위)
    event_success_ratio = models.IntegerField(default=0) # 일정 수행률 (%)
    parent_emotion = models.CharField(max_length=20, choices=EMOTION_CHOICES, default='neutral')


# GPT API시 전달할 핵심 문맥 요약 릴레이션
class ContextSummary(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='context_summary')
    content = models.TextField()  # GPT가 참고할 핵심 요약 내용
    created_at = models.DateTimeField(auto_now_add=True)


# 일정(Event) 모델 - Parent(보호자) 기준
class Event(models.Model):

    EVENT_TYPE_CHOICES = [
        ('normal', '일반 일정'),
        ('hospital', '병원 일정'),
    ]
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='event')
    
    title = models.CharField(max_length=200)  # 일정 제목
    # description = models.TextField(blank=True)  # 상세 내용 (선택)
    date = models.DateField()  # 날짜 (YYYY-MM-DD)
    start_time = models.TimeField()  # 시작 시간 (예: HH:MM:SS)
    end_time = models.TimeField(blank=True, null=True)  # 종료 시간 (예: HH:MM:SS)
    created_at = models.DateTimeField(auto_now_add=True)
    
    is_checked = models.BooleanField(default=False) # 일정 완료 여부 기본값 False

    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default='normal',  # 기본값은 일반 일정
    )
    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ('parent', 'date', 'start_time', 'title')  # 같은 시간 같은 제목 중복 방지

    def __str__(self):
        return f"{self.title} ({self.date} {self.start_time})- {self.get_event_type_display()}"


# Parent의 약 복용 스케쥴 DB
class MedicationSchedule(models.Model): 
    TIME_SLOT_CHOICES = [
        ('morning', '아침'),
        ('lunch', '점심'),
        ('dinner', '저녁'),
        ('before_sleep', '취침 전'),
    ]

    parent = models.ForeignKey(Parent, related_name='medication_schedule', on_delete=models.CASCADE)
    time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES) # ex) 오전 8:30

    class Meta:
        unique_together = ('parent', 'time_slot')  # Parent 당 각 시간대 1개만 존재

    def __str__(self):
        return f"{self.parent.name} - {self.get_time_slot_display()}"


class MedicationItem(models.Model):
    medication_schedule = models.ForeignKey(MedicationSchedule, related_name='medication_item', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    dose = models.CharField(max_length=50, blank=True)  # ex: 1정, 500mg

    def __str__(self):
        return f"{self.medication_schedule} - {self.name} {self.dose}"


# AI 기반 질문 추천 서비스를 위한 모델
class Question(models.Model):
    parent = models.ForeignKey(Parent, related_name='question', on_delete=models.CASCADE)
    
    recommaned_question = models.CharField(max_length=150)
    recommaned_reason = models.TextField()  # GPT가 해당 질문을 추천한 이유
    
    chat_count = models.PositiveIntegerField()  # 이 질문이 생성될 당시의 대화 수
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.parent.name}님의 보호자에게 추천된 질문: {self.recommaned_question}"
