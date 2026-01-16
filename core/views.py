from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
import json

from .services import BaiduService
from .models import Person, FaceScan
from .utils import log_business, log_system_error, get_client_ip

@staff_member_required(login_url='/admin/login/')
def face_search_view(request):
    context = {
        'title': '人脸识别扫描',
        'site_title': admin.site.site_title,
        'site_header': admin.site.site_header,
        'has_permission': True,
        'user': request.user,
        'opts': FaceScan._meta,
        'app_label': 'core',
    }
    return render(request, 'admin/face_search.html', context)

@csrf_exempt
@staff_member_required(login_url='/admin/login/')
def api_search_face(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'msg': '仅支持POST'}, status=405)
    
    try:
        data = json.loads(request.body)
        raw_image = data.get('image', '')
        if ';base64,' in raw_image:
            image_base64 = raw_image.split(';base64,')[1]
        else:
            image_base64 = raw_image
        
        res = BaiduService.search_face(image_base64)
        client_ip = get_client_ip(request)
        
        if res.get('error_code') == 0:
            user_list = res.get('result', {}).get('user_list', [])
            if user_list:
                top = user_list[0]
                person = Person.objects.filter(id_card=top['user_id']).first()
                name = person.name if person else "未知"
                score = round(top['score'], 1)
                
                # 记录业务日志：人脸识别成功
                log_business(
                    user=request.user,
                    ip=client_ip,
                    action="人脸识别",
                    obj=name,
                    detail=f"识别成功，身份证：{top['user_id']}，匹配度: {score}%"
                )
                
                return JsonResponse({'status': 'success', 'data': {
                    'name': name,
                    'class_name': person.class_name if person else '',
                    'user_type': person.user_type if person else '',
                    'id_card': top['user_id'],
                    'score': score,
                    'photo_url': person.face_image.url if person and person.face_image else ''
                }})
        
        # 记录业务日志：识别失败（但属于正常业务流程）
        log_business(
            user=request.user,
            ip=client_ip,
            action="人脸识别",
            obj="未知人员",
            detail=f"识别无匹配: {res.get('error_msg')}"
        )
        return JsonResponse({'status': 'fail', 'msg': '未找到匹配人员'})
        
    except Exception as e:
        log_system_error(f"API Exception: {e}")
        return JsonResponse({'status': 'error', 'msg': '系统内部错误'}, status=500)