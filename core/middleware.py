from django.utils.deprecation import MiddlewareMixin
from .utils import get_client_ip
from .log_utils import log_business

class RealIPMiddleware(MiddlewareMixin):
    """
    修正 IP 获取逻辑
    1. 优先获取 X-Forwarded-For 的第一个 IP (通常是真实客户端 IP)
    2. 其次获取 X-Real-IP
    """
    def process_request(self, request):
        # print("=== META DEBUG ===")
        # print("X-Forwarded-For:", request.META.get('HTTP_X_FORWARDED_FOR'))
        # print("X-Real-IP:", request.META.get('HTTP_X_REAL_IP'))
        # print("REMOTE_ADDR:", request.META.get('REMOTE_ADDR'))
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        real_ip = None

        if x_forwarded_for:
            # 必须用 split，防止多层代理导致 IP 格式错误
            real_ip = x_forwarded_for.split(',')[0].strip()
        
        # 兜底：如果 Nginx 没传 XFF，尝试 X-Real-IP
        if not real_ip:
            real_ip = request.META.get('HTTP_X_REAL_IP')
        
        # 修正 Django 的 REMOTE_ADDR
        if real_ip:
            request.META['REMOTE_ADDR'] = real_ip
            request.META['HTTP_X_REAL_IP'] = real_ip

class ExportAuditMiddleware(MiddlewareMixin):
    """
    拦截导出操作并记录到 access.log
    """
    def process_response(self, request, response):
        if request.method == 'POST' and '/export/' in request.path and response.status_code == 200:
            if request.user.is_authenticated:
                # 不再解析格式，简化逻辑
                resource = "未知数据"
                if 'person' in request.path:
                    resource = "人员档案"
                elif 'user' in request.path:
                    resource = "用户列表"
                
                log_business(
                    user=request.user,
                    ip=get_client_ip(request),
                    action="数据导出",
                    obj=resource,
                    detail="成功执行导出操作"
                )
        return response