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