import requests
import time
import base64  # 新增
import os      # 新增
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction

# 导入模型
from .models import Person

# 导入日志
from .utils import system_logger, import_logger, face_logger # 确保引入了 face_logger

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
        params = {"grant_type": "client_credentials", "client_id": settings.FACE_API_KEY, "client_secret": settings.FACE_SECRET_KEY}
        try:
            resp = requests.post(url, params=params, timeout=5).json()
            if "access_token" in resp:
                cls._access_token = resp["access_token"]
                cls._token_expire = now + resp.get("expires_in", 2592000) - 60
                return cls._access_token
        except Exception as e:
            system_logger.error(f"Baidu Token Error: {e}")
        return None

    @classmethod
    def search_face(cls, image_base64):
        """人脸搜索 (现有功能)"""
        token = cls.get_token()
        if not token: return {"error_msg": "Token Error"}
        url = f"https://aip.baidubce.com/rest/2.0/face/v3/search?access_token={token}"
        data = {"group_id_list": settings.FACE_GROUP_ID, "image": image_base64, "image_type": "BASE64"}
        try:
            return requests.post(url, json=data, timeout=10).json()
        except Exception as e:
            system_logger.error(f"Baidu API Error: {str(e)}")
            return {"error_msg": str(e)}

    # ==================== 新增：同步人脸方法 ====================
    @classmethod
    def sync_face(cls, person):
        """
        同步人员图片到百度人脸库 (新增或更新)
        :param person: Person 模型对象
        """
        if not person.face_image or not os.path.exists(person.face_image.path):
            return False, "本地图片文件不存在"

        token = cls.get_token()
        if not token: return False, "无法获取百度Token"

        # 1. 读取文件转 Base64
        try:
            with open(person.face_image.path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode("utf8")
        except Exception as e:
            return False, f"图片读取失败: {e}"

        # 2. 准备请求数据
        url_add = f"https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/add?access_token={token}"
        url_update = f"https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/update?access_token={token}"
        
        payload = {
            "group_id": settings.FACE_GROUP_ID,
            "user_id": person.id_card, # 使用身份证作为百度库的 user_id
            "user_info": person.name,  # 可选：将姓名存入 user_info
            "image": image_base64,
            "image_type": "BASE64",
            "action_type": "REPLACE"   # 新增时若已存在则替换(仅add接口有效，但为了保险我们保留你的双重逻辑)
        }
        headers = {'Content-Type': 'application/json'}

        try:
            # 3. 尝试新增
            resp = requests.post(url_add, json=payload, headers=headers, timeout=10).json()
            if resp.get("error_code") == 0:
                face_logger.info(f"百度人脸库新增成功: {person.name}")
                return True, "新增成功"
            
            # 4. 如果错误码是 223105 (用户已存在)，则执行更新
            if resp.get("error_code") == 223105:
                resp_up = requests.post(url_update, json=payload, headers=headers, timeout=10).json()
                if resp_up.get("error_code") == 0:
                    face_logger.info(f"百度人脸库更新成功: {person.name}")
                    return True, "更新成功"
                
                err_msg = resp_up.get('error_msg')
                face_logger.warning(f"百度更新失败 [{person.name}]: {err_msg}")
                return False, f"更新失败: {err_msg}"
                
            err_msg = resp.get('error_msg')
            face_logger.warning(f"百度新增失败 [{person.name}]: {err_msg}")
            return False, f"百度API错误: {err_msg}"
            
        except Exception as e:
            face_logger.error(f"百度同步异常 [{person.name}]: {e}")
            return False, str(e)


class ImageDownloadService:
    @staticmethod
    def _download_worker(person_id, url):
        try:
            person = Person.objects.get(pk=person_id)
            import_logger.info(f"开始下载图片: {person.name} - {url}")
            
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                img_content = ContentFile(resp.content)
                # 保存图片 (注意：save=True 会自动触发数据库保存)
                person.face_image.save(f"{person.id_card}.jpg", img_content, save=True)
                import_logger.success(f"图片下载成功: {person.name}")

                # # ==================== 新增：下载成功后同步到百度 ====================
                # # 直接在线程中调用同步，不阻塞主线程
                # success, msg = BaiduService.sync_face(person)
                # if not success:
                #     import_logger.warning(f"图片同步百度失败: {person.name} - {msg}")
                # # ================================================================

            else:
                import_logger.warning(f"图片下载失败 HTTP {resp.status_code}: {person.name}")
        except Exception as e:
            system_logger.error(f"图片下载异常: {e}")

    @staticmethod
    def trigger_download(person_id, url):
        if person_id and url:
            transaction.on_commit(
                lambda: image_download_executor.submit(
                    ImageDownloadService._download_worker, person_id, url
                )
            )