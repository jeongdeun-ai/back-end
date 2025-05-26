import os
import django
from datetime import date, time

# 1. Django 세팅 연결
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from table.models import Parent, UserParentRelation, Event
from django.db import IntegrityError

# 2. 기존 DB 삭제
DB_PATH = 'db.sqlite3'
if os.path.exists(DB_PATH):
    print("🔄 기존 DB 삭제 중...")
    os.remove(DB_PATH)

# 3. 마이그레이션 수행
print("⚙️  마이그레이션 실행 중...")
call_command("makemigrations") # python3 manage.py makemigrations
call_command("migrate") # python3 manage.py migrate

# 4. 슈퍼유저 생성
User = get_user_model()
if not User.objects.filter(email='admin@naver.com').exists():
    print("👑 슈퍼유저 생성 중...")
    User.objects.create_superuser(
        email='admin@naver.com',
        username='admin',
        phone_number='01012345678',
        password='12345678'
    )

# 5. 더미 유저/부모/관계 생성
try:
    print("👨‍👩‍👧‍👦 더미 보호자 및 어르신 생성 중...")

    guardian = User.objects.create_user(
        email='jeongdeun_kim@example.com',
        username='김정든',
        phone_number='01099998888',
        password='test1234',
        is_active=True,  # ✅ 이거 추가!
    )



    parent = Parent.objects.create(
        name='김철수',
        birth_date='1940-03-15',
        sex='M',
        address='서울 강남구',
        disease_info='고혈압',
        medication_info='아침 약 1정',
        additional_notes='아침마다 산책함'
    )

    UserParentRelation.objects.create(
        user=guardian,
        parent=parent,
        relation_type='son',
        ai_name_called='정든이'
    )

    # 6. 더미 일정 추가
    print("📅 더미 일정 추가 중...")
    Event.objects.create(
        parent=parent,
        title="병원 방문",
        date=date(2025, 6, 11),
        start_time=time(10, 0),
        end_time=time(11, 0)
    )

    Event.objects.create(
        parent=parent,
        title="가족 통화",
        date=date(2025, 6, 11),
        start_time=time(20, 0),
        end_time=time(20, 30)
    )

    Event.objects.create(
        parent=parent,
        title="자기전 롤 한판",
        date=date(2025, 6, 11),
        start_time=time(22, 0),
        end_time=time(23, 0)
    )

    print("✅ 초기화 완료!")

except IntegrityError as e:
    print(f"❌ 중복 오류 발생: {e}")
except Exception as e:
    print(f"❌ 오류 발생: {e}")
