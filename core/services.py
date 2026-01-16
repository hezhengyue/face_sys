import requests
import time
import base64
import os
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction

# 导入模型
from .models import Person

# 统一日志工具
from .utils import log_system_error, log_business

# 全局线程池
image_download_executor = ThreadPoolExecutor(max_workers=10)

class BaiduService:
    _access_token = None
    _token_expire = 0

    @classmethod
    def get_token(cls):
        now = time.time()
        if cls._access_token and now < cls._token_expire:
            return cls._access_token
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials", 
            "client_id": settings.FACE_API_KEY, 
            "client_secret": settings.FACE_SECRET_KEY
        }
        try:
            resp = requests.post(url, params=params, timeout=5).json()
            if "access_token" in resp:
                cls._access_token = resp["access_token"]
                cls._token_expire = now + resp.get("expires_in", 2592000) - 60
                return cls._access_token
        except Exception as e:
            log_system_error(f"Baidu Token Error: {e}")
        return None

    @classmethod
    def search_face(cls, image_base64):
        """人脸搜索"""
        token = cls.get_token()
        if not token: return {"error_msg": "Token Error"}
        url = f"https://aip.baidubce.com/rest/2.0/face/v3/search?access_token={token}"
        data = {
            "group_id_list": settings.FACE_GROUP_ID, 
            "image": image_base64, 
            "image_type": "BASE64"
        }
        try:
            return requests.post(url, json=data, timeout=10).json()
        except Exception as e:
            log_system_error(f"Baidu API Error: {str(e)}")
            return {"error_msg": str(e)}

    @classmethod
    def sync_face(cls, person):
        """同步人员图片到百度人脸库"""
        if not person.face_image or not os.path.exists(person.face_image.path):
            return False, "本地图片文件不存在"

        token = cls.get_token()
        if not token: return False, "无法获取百度Token"

        try:
            with open(person.face_image.path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode("utf8")
        except Exception as e:
            return False, f"图片读取失败: {e}"

        url_add = f"https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/add?access_token={token}"
        url_update = f"https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/update?access_token={token}"
        
        payload = {
            "group_id": settings.FACE_GROUP_ID,
            "user_id": person.id_card,
            "user_info": person.name,
            "image": image_base64,
            "image_type": "BASE64",
            "action_type": "REPLACE"
        }
        headers = {'Content-Type': 'application/json'}

        try:
            resp = requests.post(url_add, json=payload, headers=headers, timeout=10).json()
            if resp.get("error_code") == 0:
                log_business("System", "127.0.0.1", "同步百度", person.name, "新增成功")
                return True, "新增成功"
            
            if resp.get("error_code") == 223105:
                resp_up = requests.post(url_update, json=payload, headers=headers, timeout=10).json()
                if resp_up.get("error_code") == 0:
                    log_business("System", "127.0.0.1", "同步百度", person.name, "更新成功")
                    return True, "更新成功"
                
                err_msg = resp_up.get('error_msg')
                log_system_error(f"百度更新失败 [{person.name}]: {err_msg}")
                return False, f"更新失败: {err_msg}"
                
            err_msg = resp.get('error_msg')
            log_system_error(f"百度新增失败 [{person.name}]: {err_msg}")
            return False, f"百度API错误: {err_msg}"
            
        except Exception as e:
            log_system_error(f"百度同步异常 [{person.name}]: {e}")
            return False, str(e)


class ImageDownloadService:
    @staticmethod
    def _download_worker(person_id, url):
        try:
            person = Person.objects.get(pk=person_id)
            
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                img_content = ContentFile(resp.content)
                # 直接保存，不再需要 Auditlog 的 context wrapper
                person.face_image.save(f"{person.id_card}.jpg", img_content, save=True)
                
                # 记录到 access.log
                log_business(
                    user="System", 
                    ip="127.0.0.1", 
                    action="自动下载", 
                    obj=person.name, 
                    detail=f"图片下载成功"
                )
            else:
                log_system_error(f"图片下载失败 HTTP {resp.status_code}: {person.name}")
                
        except Exception as e:
            log_system_error(f"图片下载异常: {e}")

    @staticmethod
    def trigger_download(person_id, url):
        if person_id and url:
            transaction.on_commit(
                lambda: image_download_executor.submit(
                    ImageDownloadService._download_worker, person_id, url
                )
            )