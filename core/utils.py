import os
import sys

def get_client_ip(request):
    return request.META.get('REMOTE_ADDR', '0.0.0.0')