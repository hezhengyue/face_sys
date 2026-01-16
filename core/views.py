from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_sameorigin 
import json
from .services import BaiduService
from .models import Person
from .utils import face_logger, system_logger
from .models import FaceScan # 导入刚才定义的模型

# =========================================================
# 人脸识别页面视图
# =========================================================
@staff_member_required(login_url='/admin/login/')
def face_search_view(request):
    # 构造 context
    context = {
        'title': '人脸识别扫描',
        'site_title': admin.site.site_title,
        'site_header': admin.site.site_header,
        'has_permission': True,
        'user': request.user,
        # === 下面这几行是为了让原生 Admin 的面包屑导航正常显示 ===
        # 告诉模板：我们现在处于 "Core" 应用下的 "FaceScan" 页面
        'opts': FaceScan._meta,  
        'app_label': 'core',
        # ====================================================
    }
    return render(request, 'admin/face_search.html', context)

# =========================================================
# 人脸识别API接口
# =========================================================
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
                    'user_type': person.user_type if person else '',
                    'id_card': top['user_id'],
                    'score': round(top['score'], 1),
                    'photo_url': person.face_image.url if person and person.face_image else ''
                }})
        
        face_logger.warning(f"识别无匹配 | {res.get('error_msg')}")
        return JsonResponse({'status': 'fail', 'msg': '未找到匹配人员'})
        
    except Exception as e:
        system_logger.error(f"API系统错误: {e}")
        return JsonResponse({'status': 'error', 'msg': '系统内部错误'}, status=500)

