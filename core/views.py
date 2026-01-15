from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from django.http import HttpResponseRedirect
from .services import BaiduService
from .models import Person
from .utils import face_logger, system_logger
import json


@staff_member_required(login_url='/admin/login/')
def face_search_view(request):
    # 这里不需要传 site_title 等参数了，因为不是继承 admin/base_site.html，或者让它用默认值
    return render(request, 'admin/face_search.html', {
        'title': '人脸识别搜索', 
        # 兼容一下模板里可能用到的变量
        'site_title': '人脸识别系统',
        'site_header': '人脸识别系统',
        # === 核心修改：添加这行代码 ===
        'has_permission': True,  
        # ===========================
        
        'is_popup': False,
        'user': request.user,  # 确保 user 对象传入（通常 request context 会自动包含，但显式加上更保险）
    })

@csrf_exempt
@staff_member_required(login_url='/admin/login/')
def api_search_face(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'msg': '仅支持POST'}, status=405)
    
    try:
        data = json.loads(request.body)
        raw_image = data.get('image', '')
        
        if not raw_image:
            return JsonResponse({'status': 'fail', 'msg': '无效图片'})

        # === 修改开始：通用去除 Base64 头部 ===
        # 不管是 png, jpg, jpeg 还是 gif，只要包含 ;base64, 就切分
        if ';base64,' in raw_image:
            image_base64 = raw_image.split(';base64,')[1]
        else:
            image_base64 = raw_image
        
        res = BaiduService.search_face(image_base64)
        
        if res.get('error_code') == 0:
            user_list = res.get('result', {}).get('user_list', [])
            if user_list:
                top = user_list[0]
                person = Person.objects.filter(id_card=top['user_id']).first()
                name = person.name if person else "未知"
                
                # 记录业务日志
                face_logger.info(f"识别成功 | 姓名: {name} | 分数: {top['score']}")
                
                return JsonResponse({'status': 'success', 'data': {
                    'name': name,
                    'class_name': person.class_name if person else '',
                    'id_card': top['user_id'],
                    'score': round(top['score'], 1),
                    'photo_url': person.face_image.url if person and person.face_image else ''
                }})
        
        face_logger.warning(f"识别无匹配 | {res.get('error_msg')}")
        return JsonResponse({'status': 'fail', 'msg': '未找到匹配人员'})
        
    except Exception as e:
        system_logger.error(f"API系统错误: {e}")
        return JsonResponse({'status': 'error', 'msg': '系统内部错误'}, status=500)


def custom_login(request, extra_context=None):
    """
    自定义登录视图：
    复用 Django 原生登录逻辑，但强制登录后跳转到首页
    """
    # 1. 如果用户已经登录，直接踢回首页
    if request.method == 'GET' and request.user.is_authenticated:
        return HttpResponseRedirect('/')

    # 2. 调用 Django 原生的 Admin 登录视图
    #    这样能保留原生的界面、验证逻辑和错误提示
    response = admin.site.login(request, extra_context)

    # 3. 关键点：检测是否登录成功
    #    如果请求是 POST (提交表单) 并且状态码是 302 (跳转)，说明登录成功了
    if request.method == 'POST' and response.status_code == 302:
        # 强制修改跳转地址为首页 '/'
        return HttpResponseRedirect('/')

    # 4. 如果登录失败或者只是 GET 请求，返回原生响应 (显示登录页或报错)
    return response