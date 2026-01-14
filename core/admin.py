from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.urls import path
import pandas as pd
from datetime import datetime
# [核心修改] 引入 Unfold 的 ModelAdmin
from unfold.admin import ModelAdmin
from .models import User, Person
from .utils import user_logger

@admin.register(User)
class UserAdmin(ModelAdmin): # 继承 Unfold ModelAdmin
    list_display = ('username', 'department', 'is_active', 'status_badge', 'pwd_error_count')
    list_filter = ('is_locked', 'department')
    search_fields = ('username',)
    actions = ['unlock_users']

    # Unfold 特性：使用 badge 显示状态
    def status_badge(self, obj):
        if obj.is_locked:
            return format_html('<span class="bg-red-100 text-red-800 px-2 py-1 rounded text-xs">已锁定</span>')
        return format_html('<span class="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">正常</span>')
    status_badge.short_description = "状态"

    def unlock_users(self, request, queryset):
        queryset.update(is_locked=False, pwd_error_count=0, lock_time=None)
        self.message_user(request, "已解锁选定账户")
        user_logger.warning(f"管理员[{request.user}]批量解锁账户")
    unlock_users.short_description = "🔓 解锁账户"

@admin.register(Person)
class PersonAdmin(ModelAdmin):
    list_display = ('face_preview', 'name', 'id_card', 'class_name', 'user_type', 'create_time')
    list_filter = ('user_type', 'class_name')
    search_fields = ('name', 'id_card')
    list_per_page = 20
    actions = ['export_excel']

    def face_preview(self, obj):
        if obj.face_image:
            # 使用 Tailwind 样式
            return format_html(
                '<img src="{}" class="h-10 w-10 rounded-full object-cover border border-gray-200" onclick="window.open(this.src)" style="cursor:pointer"/>', 
                obj.face_image.url
            )
        return "-"
    face_preview.short_description = "照片"

    def export_excel(self, request, queryset):
        # ... (导出逻辑保持不变) ...
        data = list(queryset.values('name', 'id_card', 'class_name', 'user_type'))
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.ms-excel')
        fname = f"Export_{datetime.now().strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename={fname}'
        df.to_excel(response, index=False)
        return response
    export_excel.short_description = "📂 导出Excel"