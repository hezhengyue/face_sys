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
from django.apps import apps
from django.contrib.admin import AdminSite
from django.utils.text import capfirst

# 第三方库
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from auditlog.models import LogEntry
from auditlog.admin import LogEntryAdmin
from axes.models import AccessLog
from axes.admin import AccessLogAdmin

# 本地模型
from .models import User, Person, FaceScan
from .services import ImageDownloadService
from .utils import system_logger
from .views import face_search_view   # 导入你的扫描视图

# =========================================================
# 标准化配置：直接修改默认 admin.site 的标题
# =========================================================
admin.site.site_header = '人脸识别系统管理'
admin.site.site_title = '人脸识别系统'
admin.site.index_title = '数据管理'

# =========================================================
# 用户管理 (UserAdmin)
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
        # fields = ("username", "department")

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
        # ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        # ('重要日期', {'fields': ('last_login', 'date_joined')}),
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
# 人员管理 (PersonAdmin)
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
# 人脸识别菜单入口配置
# =========================================================
@admin.register(FaceScan)
class FaceScanAdmin(admin.ModelAdmin):
    """
    这是一个虚拟的 Admin，只为了在侧边栏生成菜单。
    点击该菜单时，直接跳转到自定义的人脸扫描页面。
    """
    def get_model_perms(self, request):
        """
        确保只有有权限的用户能看到这个菜单
        """
        return {
            'add': False,
            'change': False,
            'delete': False,
            'view': True,
        }

    def changelist_view(self, request, extra_context=None):
        """
        重写列表视图：当点击菜单进入此视图时，
        直接重定向到 urls.py 中定义的 'face_search' 路由
        """
        return HttpResponseRedirect(reverse('face_search'))

# =========================================================
# 注册所有模型到后台（修正重复注册问题）
# =========================================================
# 先取消注册（防止重复注册报错）
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

# 注册核心业务模型
admin.site.register(User, UserAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Group)  # 使用默认的 GroupAdmin

# 注册 Auditlog (数据审计) - 检查是否已注册
if not admin.site.is_registered(LogEntry):
    admin.site.register(LogEntry, LogEntryAdmin)

# 注册 Axes (安全日志)
if not admin.site.is_registered(AccessLog):
    admin.site.register(AccessLog, AccessLogAdmin)