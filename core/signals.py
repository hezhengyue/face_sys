# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Person
from .services import BaiduService
from .utils import face_logger

@receiver(post_save, sender=Person)
def sync_face_on_save(sender, instance, created, **kwargs):
    """
    监听 Person 模型保存事件：
    如果有人脸图片，尝试同步到百度。
    注意：为了避免导入时下载线程和这里重复同步，可以做一些判断，
    或者因为百度接口支持 update 覆盖，重复调用也无害，只是多一次请求。
    """
    # 只有当 face_image 有值，且文件确实存在时才同步
    if instance.face_image and hasattr(instance.face_image, 'path'):
        try:
            # 这是一个同步调用，如果百度API很慢会稍微卡顿后台保存
            # 如果介意卡顿，可以将此处也放入线程池
            success, msg = BaiduService.sync_face(instance)
            if not success:
                # 仅记录日志，不抛出异常阻断保存
                face_logger.warning(f"Signal同步百度失败: {instance.name} - {msg}")
        except Exception as e:
            pass