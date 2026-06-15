from .base import *

DATABASES = {
    "default":{
        "ENGINE":"django.db.backends.mysql",
        "NAME":os.getenv("DB_NAME"),
        "USER":os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "host.docker.internal"),
        "PORT": os.getenv("DB_PORT", "53306"),
        "ATOMIC_REQUESTS":True
    }
}