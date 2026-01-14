# config/__init__.py

import django.db.backends.mysql.base

# 这里的代码是为了绕过 Django 对 MySQL 版本的强制检查
# 强行覆盖版本检查函数，让它什么都不做
def pass_check_database_version_supported(self):
    pass

django.db.backends.mysql.base.DatabaseWrapper.check_database_version_supported = pass_check_database_version_supported