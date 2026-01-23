from django.dispatch import receiver
from django.db.models.signals import post_save
# 1. 修改导入：从 django 原生信号导入 user_login_failed，不再引用 axes
from django.contrib.auth.signals import user_logged_in, user_login_failed
from .utils import get_client_ip
from .log_utils import log_business
from .models import Person
from .services import BaiduService

# ==================== 监听登录事件 ====================
@receiver(user_logged_in)
def log_login_success(sender, user, request, **kwargs):
    """登录成功日志"""
    log_business(
        user=user,
        ip=get_client_ip(request),
        action="登录",
        obj="系统",
        detail="登录成功"
    )

@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    """
    登录失败日志
    使用 Django 原生信号，credentials 包含尝试登录的用户名
    """
    username = credentials.get('username', '未知用户')
    log_business(
        user=username,
        ip=get_client_ip(request),
        action="登录失败",
        obj="系统",
        detail="密码错误或用户不存在"
    )


# ==================== 业务逻辑：同步人脸到百度 ====================
@receiver(post_save, sender=Person)
def sync_face_on_save(sender, instance, created, **kwargs):
    if instance.face_image and hasattr(instance.face_image, 'path'):
        try:
            # 仅触发同步，日志在 Service 内部记录
            BaiduService.sync_face(instance)
        except Exception:
            pass