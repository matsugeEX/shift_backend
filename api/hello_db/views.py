from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Hello

class Db(APIView):
    def get (self,requset,format=None):
        entry = Hello.objects.get(id=1)
        return Response({"message":entry.world})