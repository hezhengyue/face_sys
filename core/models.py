from django.db import models
from django.contrib.auth.models import AbstractUser
from auditlog.registry import auditlog # 导入审计注册器

def face_upload_to(instance, filename):
    ext = filename.split('.')[-1].lower()
    return f'faces/{instance.id_card}.{ext}'

class User(AbstractUser):
    # 只保留业务字段，锁定字段已由 axes 接管
    department = models.CharField("部门", max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "系统用户"
        verbose_name_plural = verbose_name

class Person(models.Model):
    name = models.CharField("姓名", max_length=50)
    class_name = models.CharField("班级", max_length=50, blank=True, null=True, default="")
    user_type = models.CharField("用户类型", max_length=50, blank=True, null=True, default="")
    id_card = models.CharField("身份证号", max_length=20, unique=True)
    face_image = models.ImageField("人脸照片", upload_to=face_upload_to, max_length=255)
    source_image_url = models.CharField("源图片URL", max_length=500, blank=True, default="")
    
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    update_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "人员档案"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.name} ({self.id_card})"

# 1. 定义一个假模型，专门用于在后台生成菜单
class FaceScan(Person):
    class Meta:
        proxy = True  # 代理模型，不创建新表
        verbose_name = '人脸识别'        # 菜单子项名称
        verbose_name_plural = '人脸识别' # 复数名

# === 注册审计 ===
# 这两行代码会让 django-auditlog 自动监听增删改
auditlog.register(User)
auditlog.register(Person)