from django import forms
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
from django.contrib.auth import login as auth_login
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import render 
from django.contrib.auth.models import Group 
from django.contrib.auth.admin import GroupAdmin

# 导入第三方管理类
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from auditlog.models import LogEntry
from auditlog.admin import LogEntryAdmin
from axes.models import AccessLog
from axes.admin import AccessLogAdmin

from .models import User, Person
from .services import ImageDownloadService
from .utils import system_logger

# 1. 自定义 Site
class FaceAdminSite(AdminSite):
    site_header = '人脸识别系统管理'
    site_title = '人脸识别系统'
    index_title = '数据管理'

    def login(self, request, extra_context=None):
        if request.method == 'GET' and self.has_permission(request):
            return HttpResponseRedirect(reverse('home'))

        context = {
            **self.each_context(request),
            **(extra_context or {}),
            'title': '登录',
            'app_path': request.get_full_path(),
            'username': request.user.get_username(),
        }

        if request.method == 'POST':
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                auth_login(request, user)
                messages.success(request, f'欢迎回来，{user.username}!')
                return HttpResponseRedirect(reverse('home'))
            else:
                messages.error(request, '用户名或密码错误')
        else:
            form = AuthenticationForm(request)

        context['form'] = form
        return render(request, 'admin/login.html', context)

face_admin_site = FaceAdminSite(name='face_admin')

# 2. 用户管理 (UserAdmin)
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
    list_display = ('username', 'department', 'is_active', 'is_staff', 'is_superuser', 'change_password_btn')
    list_filter = ('department', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'department')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('department',)}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'department', 'password_1', 'password_2'),
        }),
        ('权限设置', {
            'classes': ('wide',),
            'fields': ('is_staff', 'is_superuser'),
        }),
    )

    def change_password_btn(self, obj):
        try:
            url = reverse("admin:core_user_password_change", args=[obj.pk])
        except:
            url = f"{obj.pk}/password/"
        return format_html('<a class="button" href="{}" style="padding:3px 10px; background-color:#79aec8; color:white;">修改密码</a>', url)
    change_password_btn.short_description = "操作"

    def response_add(self, request, obj, post_url_continue=None):
        if "_continue" not in request.POST and "_addanother" not in request.POST:
            return HttpResponseRedirect(reverse("admin:core_user_changelist"))
        return super().response_add(request, obj, post_url_continue)

# 3. 人员管理 (PersonAdmin)
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

    def after_save_instance(self, instance, row,** kwargs):
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
            return format_html('<img src="{}" style="height:50px; border-radius:4px;" />', obj.face_image.url)
        return "-"
    face_preview.short_description = "照片"

    def face_preview_large(self, obj):
        if obj.face_image:
            return format_html('<img src="{}" style="max-width:300px;" />', obj.face_image.url)
        return "暂无照片"
    face_preview_large.short_description = "照片预览"

# 4. 注册所有模型到自定义后台
face_admin_site.register(User, UserAdmin)
face_admin_site.register(Person, PersonAdmin)
face_admin_site.register(Group, GroupAdmin)
# 注册 Auditlog (数据审计)
face_admin_site.register(LogEntry, LogEntryAdmin)
# 注册 Axes (安全日志)
face_admin_site.register(AccessLog, AccessLogAdmin)