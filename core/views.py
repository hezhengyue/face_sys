import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from .services import BaiduService
from .models import Person

# 配置日志
logger = logging.getLogger(__name__)

@staff_member_required(login_url='/admin/login/')  # 显式指定登录跳转地址，避免配置缺失
def face_search_view(request):
    """
    渲染人脸搜索页面
    装饰器说明：
    @staff_member_required → 要求用户必须登录，且 is_staff=True（后台工作人员）
    未满足条件时自动跳转到 /admin/login/
    """
    context = {
        'title': '人脸识别搜索',
        'is_popup': False,
        'has_permission': True,
        'site_title': '人脸识别系统',  # 统一标题，和模板匹配
        'site_header': '人脸识别系统',
    }
    # 模板路径注意：你的模板在 admin/face_search.html，需确认路径正确
    return render(request, 'admin/face_search.html', context)

@csrf_exempt  # API接口关闭CSRF验证（前端POST请求无需传CSRF token）
@staff_member_required(login_url='/admin/login/')  # API也需要登录验证
def api_search_face(request):
    """
    API: 处理人脸搜索请求
    请求方式：POST
    请求体：{"image": "base64编码的图片字符串"}
    返回格式：JSON
    """
    # 仅允许POST请求
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'msg': '仅支持POST请求'}, status=405)
    
    try:
        # 解析请求体
        data = json.loads(request.body)
        image_base64 = data.get('image', '')
        
        # 处理base64前缀（如 "data:image/jpeg;base64,xxxx"）
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        # 空图片校验
        if not image_base64:
            return JsonResponse({'status': 'fail', 'msg': '请上传有效图片'})
        
        # 调用百度人脸识别接口
        res = BaiduService.search_face(image_base64)
        
        # 百度接口调用成功且有匹配结果
        if res.get('error_code') == 0:
            user_list = res.get('result', {}).get('user_list', [])
            
            if user_list:
                # 取相似度最高的第一个结果
                top_match = user_list[0]
                score = top_match.get('score', 0)
                user_id = top_match['user_id']
                
                # 从本地数据库查询人员信息
                person = Person.objects.filter(id_card=user_id).first()
                
                # 构造返回数据
                data_resp = {
                    'name': person.name if person else '本地无记录',
                    'class_name': person.class_name if person else '未知',
                    'id_card': user_id,
                    'score': round(score, 1),
                    'photo_url': person.face_image.url if (person and person.face_image) else ''
                }
                return JsonResponse({'status': 'success', 'data': data_resp})
        
        # 无匹配结果（百度接口成功但无数据）
        return JsonResponse({'status': 'fail', 'msg': '未找到匹配人员'})
        
    except json.JSONDecodeError:
        logger.error("请求体解析失败：非合法JSON格式")
        return JsonResponse({'status': 'error', 'msg': '请求参数格式错误'}, status=400)
    except Exception as e:
        # 捕获所有未知异常，记录日志并返回友好提示
        logger.error(f"人脸搜索异常: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'msg': '系统内部错误，请联系管理员'}, status=500)