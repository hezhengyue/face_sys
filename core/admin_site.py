# core/admin_site.py

from django.contrib.admin import AdminSite
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login

class FaceAdminSite(AdminSite):
    """自定义AdminSite，覆盖登录跳转逻辑"""
    site_header = '人脸识别系统管理'
    site_title = '人脸识别系统'
    index_title = '数据管理'

    def login(self, request, extra_context=None):
        """
        重写登录方法，强制登录后跳转到首页
        """
        # 1. 如果用户已登录，直接跳首页
        if request.method == 'GET' and self.has_permission(request):
            return HttpResponseRedirect(reverse('home'))

        # 2. 初始化上下文
        context = {
            **self.each_context(request),
            **(extra_context or {}),
            'title': '登录',
            'app_path': request.get_full_path(),
            'username': request.user.get_username(),
        }

        # 3. 处理 POST 登录请求
        if request.method == 'POST':
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                auth_login(request, user)
                messages.success(request, f'欢迎回来，{user.username}!')
                # 登录成功，强制跳转到首页
                return HttpResponseRedirect(reverse('home'))
            else:
                messages.error(request, '用户名或密码错误')
        else:
            form = AuthenticationForm(request)

        context['form'] = form
        return self.render_to_response('admin/login.html', context)

# 实例化放在这里
face_admin_site = FaceAdminSite(name='face_admin')