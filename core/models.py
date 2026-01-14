import os
from django.db import models
from django.contrib.auth.models import AbstractUser

def face_upload_to(instance, filename):
    ext = filename.split('.')[-1].lower()
    return f'faces/{instance.id_card}.{ext}'

class User(AbstractUser):
    department = models.CharField("部门", max_length=100, blank=True, null=True)
    pwd_error_count = models.IntegerField("密码错误次数", default=0)
    is_locked = models.BooleanField("是否锁定", default=False)
    lock_time = models.DateTimeField("锁定时间", blank=True, null=True)

    class Meta:
        verbose_name = "系统用户"
        verbose_name_plural = verbose_name

class Person(models.Model):
    name = models.CharField("姓名", max_length=50)
    class_name = models.CharField("班级", max_length=50, default='未设置')
    user_type = models.CharField("用户类型", max_length=50, default='未设置')
    id_card = models.CharField("身份证号", max_length=20, unique=True)
    face_image = models.ImageField("人脸照片", upload_to=face_upload_to, blank=True, null=True, max_length=255)
    source_image_url = models.CharField("源图片URL", max_length=500, blank=True)
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    update_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "人员档案"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.name} ({self.id_card})"