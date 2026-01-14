import os
import json
import base64
import time
import requests
import pandas as pd
from redis import Redis
from django.conf import settings
from django.core.files.base import ContentFile
from .models import Person
from .utils import face_logger, import_logger, system_logger

try:
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    system_logger.error(f"Redis Error: {e}")
    redis_client = None

class RedisService:
    @staticmethod
    def save_progress(task_id, data):
        if redis_client:
            redis_client.setex(f"import_task:{task_id}", 3600, json.dumps(data, ensure_ascii=False))

    @staticmethod
    def load_progress(task_id):
        if redis_client:
            data = redis_client.get(f"import_task:{task_id}")
            return json.loads(data) if data else None
        return None

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
            face_logger.error(f"Baidu Token Error: {e}")
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

class PersonService:
    @staticmethod
    def process_person_data(data, is_batch=False):
        try:
            id_card = str(data.get('id_card', '')).strip()
            name = str(data.get('name', '')).strip()
            source_url = str(data.get('source_image_url', '')).strip()
            
            if not id_card: return False, "身份证为空"

            person, created = Person.objects.get_or_create(id_card=id_card)
            
            img_content = None
            if source_url:
                try:
                    resp = requests.get(source_url, timeout=10)
                    if resp.status_code == 200:
                        img_content = ContentFile(resp.content)
                except Exception as e:
                    if not is_batch: return False, f"下载失败: {e}"

            person.name = name
            person.class_name = data.get('class_name', '')
            person.user_type = data.get('user_type', '')
            person.source_image_url = source_url
            
            if img_content:
                if person.face_image:
                    person.face_image.delete(save=False)
                person.face_image.save(f"{id_card}.jpg", img_content, save=False)
            
            person.save()
            return True, "成功"
        except Exception as e:
            return False, str(e)