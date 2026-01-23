from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.password_validation import validate_password
from django import forms
from django.core.exceptions import ValidationError

# 第三方库
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields

# 本地模型
from .models import User, Person, FaceScan
from .services import ImageDownloadService
from .log_utils import log_system_error

# =========================================================
# 标准化配置
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
                log_system_error(f"导入触发下载失败: {e}")

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
# 3. 人脸识别菜单入口配置 (FaceScan)
# =========================================================
@admin.register(FaceScan)
class FaceScanAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
        return {
            'add': False,
            'change': False,
            'delete': False,
            'view': True,
        }

    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect(reverse('face_search'))




# =========================================================
# 4. auditlog显示IP
# =========================================================
from auditlog.models import LogEntry
from auditlog.admin import LogEntryAdmin

# 1. 先取消 auditlog 默认的注册
if admin.site.is_registered(LogEntry):
    admin.site.unregister(LogEntry)

# 2. 定义新的 Admin 类
@admin.register(LogEntry)
class CustomLogEntryAdmin(LogEntryAdmin):
    
    list_display = [
    # 核心必显字段（优先级从高到低）
    'timestamp',       # 1. 操作时间（最核心，排查问题先看时间）
    'user_url',        # 2. 操作用户（谁做的）
    'remote_addr',     # 3. IP地址（从哪来的）
    'action',          # 4. 操作类型（增/删/改）
    'resource_url',    # 5. 操作资源（改了哪个对象）
    'msg_short',       # 6. 操作内容（改了什么）
]

    # 搜索和筛选保持实用即可
    search_fields = ['timestamp', 'actor__username', 'remote_addr', 'object_repr', 'changes']
    list_filter = ['action', 'timestamp', 'actor', 'remote_addr']  


# =========================================================
# 4. 最终注册逻辑
# =========================================================

# 4.1 注册 User
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)

# 4.2 注册 Person
admin.site.register(Person, PersonAdmin)

# 4.3 注册 Group
if not admin.site.is_registered(Group):
    admin.site.register(Group)

