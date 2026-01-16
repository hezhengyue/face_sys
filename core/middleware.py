from django.utils.deprecation import MiddlewareMixin
from .utils import log_business, get_client_ip

class RealIPMiddleware(MiddlewareMixin):
    """必须放在最前面，修正 request.META['REMOTE_ADDR']"""
    def process_request(self, request):
        real_ip = request.META.get('HTTP_X_REAL_IP')
        if not real_ip:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                real_ip = x_forwarded_for.split(',')[0].strip()
        
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