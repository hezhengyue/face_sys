from django.utils.deprecation import MiddlewareMixin
from .utils import user_logger, get_client_ip

class ExportAuditMiddleware(MiddlewareMixin):
    """
    轻量级中间件：专门负责记录 django-import-export 的导出操作。
    其他增删改查交给 auditlog，登录交给 axes。
    """
    def process_response(self, request, response):
        # 拦截导出请求: POST 且路径包含 export 且 成功返回
        if request.method == 'POST' and '/export/' in request.path and response.status_code == 200:
            try:
                if request.user.is_authenticated:
                    ip = get_client_ip(request)
                    fmt = request.POST.get('file_format', 'file')
                    
                    user_logger.info(f"数据导出 | 路径: {request.path} | 格式: {fmt} | 用户: {request.user.username} | IP: {ip}")
            except Exception:
                pass # 日志错误不影响业务
        return response


class RealIPMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 1. 优先尝试获取 Nginx 传过来的 X-Real-IP (最准确)
        real_ip = request.META.get('HTTP_X_REAL_IP')
        
        # 2. 如果没有，再尝试 X-Forwarded-For
        if not real_ip:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                real_ip = x_forwarded_for.split(',')[0].strip()

        # 3. 只有当获取到了有效 IP，才进行覆盖
        if real_ip:
            old_ip = request.META.get('REMOTE_ADDR')
            request.META['REMOTE_ADDR'] = real_ip
            # 同时也覆盖 X_REAL_IP，确保 auditlog 能读取到
            request.META['HTTP_X_REAL_IP'] = real_ip
            
            print(f"✅ [IP修正] 原IP={old_ip} -> 真实IP={real_ip}", flush=True)
        else:
            print(f"⚠️ [IP未修正] 未发现代理头，IP保持: {request.META.get('REMOTE_ADDR')}", flush=True)