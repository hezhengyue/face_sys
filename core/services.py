import time
import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from .models import Person

logger = logging.getLogger(__name__)

# 创建全局线程池，最大并发10
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
        params = {"grant_type": "client_credentials", "client_id": settings.FACE_API_KEY, "client_secret": settings.FACE_SECRET_KEY}
        try:
            resp = requests.post(url, params=params, timeout=5).json()
            if "access_token" in resp:
                cls._access_token = resp["access_token"]
                cls._token_expire = now + resp.get("expires_in", 2592000) - 60
                return cls._access_token
        except Exception as e:
            logger.error(f"Baidu Token Error: {e}")
        return None

    @classmethod
    def search_face(cls, image_base64):
        token = cls.get_token()
        if not token: return {"error_msg": "Token Error"}
        url = f"https://aip.baidubce.com/rest/2.0/face/v3/search?access_token={token}"
        data = {"group_id_list": settings.FACE_GROUP_ID, "image": image_base64, "image_type": "BASE64"}
        try:
            return requests.post(url, json=data, timeout=10).json()
        except Exception as e:
            return {"error_msg": str(e)}

class ImageDownloadService:
    @staticmethod
    def _download_worker(person_id, url):
        """后台线程：下载并保存图片"""
        try:
            person = Person.objects.get(pk=person_id)
            print(f"[开始下载] {person.name} - {url}")
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                img_content = ContentFile(resp.content)
                person.face_image.save(f"{person.id_card}.jpg", img_content, save=True)
                print(f"[下载成功] {person.name}")
            else:
                print(f"[下载失败] HTTP {resp.status_code}")
        except Exception as e:
            print(f"[下载异常] {e}")

    @staticmethod
    def trigger_download(person_id, url):
        """触发异步下载"""
        if person_id and url:
            transaction.on_commit(
                lambda: image_download_executor.submit(
                    ImageDownloadService._download_worker, person_id, url
                )
            )