import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from .services import BaiduService
from .models import Person
from .utils import face_logger, system_logger

@staff_member_required(login_url='/admin/login/')
def face_search_view(request):
    return render(request, 'admin/face_search.html', {
        'title': '人脸识别搜索', 'is_popup': False, 'site_title': '人脸识别系统', 'site_header': '人脸识别系统'
    })

@csrf_exempt
@staff_member_required(login_url='/admin/login/')
def api_search_face(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'msg': '仅支持POST'}, status=405)
    
    try:
        data = json.loads(request.body)
        image_base64 = data.get('image', '').replace('data:image/jpeg;base64,', '')
        
        if not image_base64: return JsonResponse({'status': 'fail', 'msg': '无效图片'})
        
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