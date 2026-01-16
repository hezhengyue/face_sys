from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django import forms
from django.utils.text import capfirst

# 第三方库
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from auditlog.models import LogEntry
from auditlog.admin import LogEntryAdmin
from axes.models import AccessLog, AccessAttempt
from axes.admin import AccessLogAdmin, AccessAttemptAdmin

# 本地模型
from .models import User, Person, FaceScan
from .services import ImageDownloadService
from .utils import system_logger

# =========================================================
# 标准化配置：直接修改默认 admin.site 的标题
# =========================================================
admin.site.site_header = '人脸识别系统管理'
admin.site.site_title = '人脸识别系统'
admin.site.index_title = '数据管理'


# =========================================================
# 1. 用户管理 (UserAdmin)
# =========================================================
class CustomUserCreationForm(forms.ModelForm):
    password_1 = forms.CharField(label="密码", widget=forms.PasswordInput)
    password_2 = forms.CharField(label="确认密码", widget=forms.PasswordInput)
    department = forms.CharField(label="部门", required=False)
    is_staff = forms.BooleanField(label="允许登录后台", required=False, initial=True)
    is_superuser = forms.BooleanField(label="超级管理员", required=False)

    class Meta:
        model = User
        fields = ("username", "department", "is_staff", "is_superuser")

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password_1")
        p2 = cleaned_data.get("password_2")
        if p1 and p2 and p1 != p2:
            self.add_error("password_2", "两次输入的密码不一致")
        if p1:
            try:
                validate_password(p1, self.instance)
            except ValidationError as error:
                self.add_error("password_1", error)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password_1"])
        user.department = self.cleaned_data.get("department")
        user.is_staff = self.cleaned_data.get("is_staff")
        user.is_superuser = self.cleaned_data.get("is_superuser")
        if commit:
            user.save()
        return user

class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = UserChangeForm
    list_display = ('username', 'department', 'is_active', 'is_staff', 'is_superuser', 'last_login')
    list_filter = ('department', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'department')
    
    fieldsets = (
        ('用户', {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('department',)}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        ('用户', {
            'classes': ('wide',),
            'fields': ('username', 'department', 'password_1', 'password_2'),
        }),
        ('权限设置', {
            'classes': ('wide',),
            'fields': ('is_staff', 'is_superuser'),
        }),
    )


# =========================================================
# 2. 人员管理 (PersonAdmin)
# =========================================================
class PersonResource(resources.ModelResource):
    name = fields.Field(attribute='name', column_name='姓名')
    class_name = fields.Field(attribute='class_name', column_name='班级')
    user_type = fields.Field(attribute='user_type', column_name='用户类型')
    id_card = fields.Field(attribute='id_card', column_name='身份证号')
    source_image_url = fields.Field(attribute='source_image_url', column_name='source_image_url')

    class Meta:
        model = Person
        import_id_fields = ('id_card',) 
        fields = ('name', 'class_name', 'user_type', 'id_card', 'source_image_url')
        skip_unchanged = True
        raise_errors = True

    def after_save_instance(self, instance, row, **kwargs):
        dry_run = kwargs.get('dry_run', False)
        if not dry_run and instance.source_image_url:
            try:
                ImageDownloadService.trigger_download(instance.pk, instance.source_image_url)
            except Exception as e:
                system_logger.error(f"导入触发下载失败: {e}")

class PersonAdmin(ImportExportModelAdmin):
    resource_class = PersonResource
    list_display = ('name', 'id_card', 'class_name', 'user_type', 'update_time', 'face_preview')
    list_filter = ('user_type', 'class_name')
    search_fields = ('name', 'id_card')
    list_per_page = 20
    readonly_fields = ('face_preview_large', 'create_time', 'update_time')
    
    fieldsets = (
        ('基本信息', {'fields': ('name', 'id_card', 'class_name', 'user_type')}),
        ('人脸信息', {'fields': ('face_image', 'face_preview_large', 'source_image_url')}),
        ('时间记录', {'fields': ('create_time', 'update_time')}),
    )

    def face_preview(self, obj):
        if obj.face_image:
            return format_html('<img src="{}" style="max-height:50px; border-radius:4px;" />', obj.face_image.url)
        return "-"
    face_preview.short_description = "照片"

    def face_preview_large(self, obj):
        if obj.face_image:
            return format_html('<img src="{}" style="max-width:200px;" />', obj.face_image.url)
        return "暂无照片"
    face_preview_large.short_description = "照片预览"


# =========================================================
# 3. 审计日志增强 (LogEntryAdmin)
# =========================================================
# ⚠️ 关键修改：自定义 Auditlog Admin 以显示 IP 和更友好的搜索
class CustomLogEntryAdmin(LogEntryAdmin):
    list_display = [
        'created', 
        'resource_url', 
        'action', 
        'msg_short', 
        'user_url', 
        'remote_addr'  # 显示真实 IP (配合中间件)
    ]
    search_fields = [
        'timestamp', 
        'object_repr', 
        'changes', 
        'actor__username',
        'remote_addr'  # 支持搜 IP
    ]
    list_filter = ['action', 'timestamp', 'actor']


# =========================================================
# 4. 人脸识别菜单入口配置 (FaceScan)
# =========================================================
@admin.register(FaceScan)
class FaceScanAdmin(admin.ModelAdmin):
    """
    这是一个虚拟的 Admin，只为了在侧边栏生成菜单。
    点击该菜单时，直接跳转到自定义的人脸扫描页面。
    """
    def get_model_perms(self, request):
        """
        权限控制：只有有权限的用户能看到这个菜单
        """
        return {
            'add': False,
            'change': False,
            'delete': False,
            'view': True,
        }

    def changelist_view(self, request, extra_context=None):
        """
        拦截列表视图：点击后重定向到人脸识别页面
        """
        return HttpResponseRedirect(reverse('face_search'))


# =========================================================
# 5. 最终注册逻辑 (避免重复注册)
# =========================================================

# 5.1 注册 User
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)

# 5.2 注册 Person
admin.site.register(Person, PersonAdmin)

# 5.3 注册 Auditlog (使用自定义 Admin)
try:
    admin.site.unregister(LogEntry)
except admin.sites.NotRegistered:
    pass
admin.site.register(LogEntry, CustomLogEntryAdmin)

# 5.4 注册 Axes (使用默认，确保已注册)
if not admin.site.is_registered(AccessLog):
    admin.site.register(AccessLog, AccessLogAdmin)
if not admin.site.is_registered(AccessAttempt):
    admin.site.register(AccessAttempt, AccessAttemptAdmin)

# 5.5 注册 Group (保持默认)
if not admin.site.is_registered(Group):
    admin.site.register(Group)