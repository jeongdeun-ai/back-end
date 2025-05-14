from django.contrib import admin
from .models import *


admin.site.register(User)
admin.site.register(Parent)
admin.site.register(UserParentRelation)
admin.site.register(ChatLog)
admin.site.register(DailyReport)
admin.site.register(ContextSummary)
