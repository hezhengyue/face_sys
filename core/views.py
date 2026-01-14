import time
import base64
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from .services import BaiduService, RedisService, PersonService, redis_client
from .models import Person
from .utils import import_logger, face_logger

executor = ThreadPoolExecutor(2)

@login_required
def face_search_view(request):
    """人脸搜索（嵌入Admin）"""
    context = admin.site.each_context(request)
    context.update({'title': '人脸搜索'})
    return render(request, 'admin/face_search.html', context)

@login_required
def batch_import_view(request):
    """批量导入页面（嵌入Admin）"""
    context = admin.site.each_context(request)
    context.update({'title': '批量导入人员'})
    return render(request, 'admin/batch_import.html', context)

@login_required
def api_search_face(request):
    """人脸搜索 API"""
    if request.method == 'POST':
        f = request.FILES.get('image')
        if not f: return JsonResponse({'status':'error', 'message':'无文件'})
        b64 = base64.b64encode(f.read()).decode()
        
        face_logger.info(f"搜索请求 | 用户[{request.user}]")
        res = BaiduService.search_face(b64)
        
        # 结果处理
        if res.get('error_code') == 0:
            user_list = res['result']['user_list']
            if user_list:
                top = user_list[0]
                # 查找本地数据库信息
                p = Person.objects.filter(id_card=top['user_id']).first()
                if p:
                    top['name'] = p.name
                    top['class_name'] = p.class_name
                    top['face_url'] = p.face_image.url if p.face_image else ''
                else:
                    top['name'] = '未知(本地无记录)'
        
        return JsonResponse({'status':'success', 'result': res})
    return JsonResponse({'status':'error'})

@login_required
def api_batch_import(request):
    """批量导入提交 API"""
    if request.method == 'POST':
        f = request.FILES.get('file')
        task_id = f"{request.user.username}_{int(time.time())}"
        
        if not os.path.exists(settings.TEMP_ROOT): os.makedirs(settings.TEMP_ROOT)
        path = os.path.join(settings.TEMP_ROOT, f"{task_id}_{f.name}")
        
        with open(path, 'wb+') as d:
            for chunk in f.chunks(): d.write(chunk)
            
        RedisService.save_progress(task_id, {'status': 'processing', 'total': 0, 'success': 0, 'fail': 0, 'details': [], 'start_time': time.time()})
        executor.submit(run_import_thread, path, task_id)
        return JsonResponse({'status': 'success', 'task_id': task_id})
    return JsonResponse({'status': 'error'})

def run_import_thread(path, task_id):
    """后台导入线程"""
    task = RedisService.load_progress(task_id)
    if not task: return
    import_logger.info(f"任务开始: {task_id}")
    
    try:
        if path.endswith('.csv'): df = pd.read_csv(path)
        else: df = pd.read_excel(path)
        df = df.where(pd.notnull(df), None)
        task['total'] = len(df)
        RedisService.save_progress(task_id, task)
        
        for idx, row in df.iterrows():
            row_num = idx + 1
            p_data = {
                "name": str(row.get('姓名', '')).strip(),
                "class_name": str(row.get('班级', '')).strip(),
                "user_type": str(row.get('用户类型', '')).strip(),
                "id_card": str(row.get('身份证号', '')).strip(),
                "source_image_url": str(row.get('source_image_url', '')).strip()
            }
            
            suc, msg = PersonService.process_person_data(p_data, True)
            
            if suc:
                import_logger.info(f"行[{row_num}] 成功: {p_data['id_card']}")
                task['success'] += 1
            else:
                import_logger.error(f"行[{row_num}] 失败: {msg}")
                task['fail'] += 1
                task['details'].append({'row': row_num, 'msg': msg})
            
            if idx % 10 == 0: RedisService.save_progress(task_id, task)
            
        task['status'] = 'completed'
    except Exception as e:
        task['status'] = 'failed'
        task['details'].append({'row': 0, 'msg': str(e)})
        import_logger.error(f"任务崩溃: {e}")
    finally:
        RedisService.save_progress(task_id, task)
        if os.path.exists(path): os.remove(path)

@login_required
def api_get_progress(request, task_id):
    data = RedisService.load_progress(task_id)
    if data: return JsonResponse({'status': 'success', 'data': data})
    return JsonResponse({'status': 'error'}, status=404)


@login_required
def face_search_view(request):
    context = admin.site.each_context(request)
    context.update({
        'title': '人脸搜索',
        # Unfold 需要的一些额外上下文可以在这里补（通常不用）
    })
    # 注意：模板里我用了 base_simple.html，如果你想要左侧菜单，请改用 base.html
    # 但 base.html 需要复杂的 navigation 数据，Unfold 的机制是在 sidebar 渲染时自动注入的
    # 最简单的做法是直接用 base_site.html，Unfold 已经重写了它
    return render(request, 'admin/face_search.html', context)