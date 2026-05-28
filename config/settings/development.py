from .base import *

DATABASS = os.getenv("DATABASS")

DATABASES = {
    "default":{
        "ENGINE":"django.db.backends.mysql",
        "NAME":os.getenv("DB_NAME"),
        "USER":os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST":"host.docker.internal",
        "PORT":"53306",
        "ATOMIC_REQUESTS":True
    }
}