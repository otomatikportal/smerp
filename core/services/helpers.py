import hashlib
import time
from django.conf import settings

def nginx_signed_url(path, secret=settings.NGINX_SECRET_KEY, expires_in=3600):
    expires = int(time.time()) + expires_in
    to_hash = f"{secret}{path}{expires}"
    signature = hashlib.md5(to_hash.encode('utf-8')).hexdigest()
    url = f"{path}?st={signature}&expires={expires}"
    return url

# Usage:
url = nginx_signed_url('/protected/myfile.pdf')