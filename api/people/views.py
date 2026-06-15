from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import People
from .serializers import PeopleSerializer
from rest_framework import status,generics,views,viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from api.people.authentication import RefreshJWTAuthentication
from .allocation import allocate_shift

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User

# Create your views here.

class CreateTestUserView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "user already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        User.objects.create_user(
            username=username,
            password=password
        )

        return Response(
            {"message": "user created"},
            status=status.HTTP_201_CREATED
        )

class PeopleView(APIView):
    #認証クラスの指定
    
    #アクセス許可の指定
    #認証済みのリクエストの許可
    permission_classes = [IsAuthenticated]
    """
    人物操作に関する関数
    """
    def get(self,request,format=None):
        """
        人物の一覧を取得する
        """
        queryset = People.objects.all()
        serializer = PeopleSerializer(queryset,many=True)
        return Response(serializer.data,status.HTTP_200_OK)
    
    def post(self,request,format=None):
        serializer = PeopleSerializer(data=request.data)
        #validationが通らなかった場合
        serializer.is_valid(raise_exception=True)
        #検証したデータを永続化する
        serializer.save()
        return Response(serializer.data,status.HTTP_201_CREATED)

class AllocationView(APIView):

    #認証済みのみ許可
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):

        workers = request.data.get("workers", [])

        result = allocate_shift(workers)

        return Response(result)


class LoginView(APIView):
    """ユーザーのログイン処理
    Args:
    APIView (class): rest_framework.viewsのAPIViewを受け取る
    """
    # 認証クラスの指定
    # リクエストヘッダーにtokenを差し込むといったカスタム動作をしないので素の認証クラスを使用する
    authentication_classes = [JWTAuthentication]
    # アクセス許可の指定
    permission_classes = []

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access = serializer.validated_data.get("access", None)
        refresh = serializer.validated_data.get("refresh", None)
        if access:
            response = Response(status=status.HTTP_200_OK)
            max_age = settings.COOKIE_TIME
            response.set_cookie('access', access, httponly=True, max_age=max_age)
            response.set_cookie('refresh', refresh, httponly=True, max_age=max_age)
            return response
        return Response({'errMsg': 'ユーザーの認証に失敗しました'}, status=status.HTTP_401_UNAUTHORIZED)
    
class RetryView(APIView):
    authentication_classes = [RefreshJWTAuthentication]
    permission_classes = []

    def post(self, request):
        try:
            data = request.data.copy()
            #request.data['refresh'] = request.META.get('HTTP_REFRESH_TOKEN')
            data['refresh'] = request.META.get('HTTP_REFRESH_TOKEN')
            print("1")
            serializer = TokenRefreshSerializer(data=data)
            print("2")
            serializer.is_valid(raise_exception=True)
            print("3")
            access = serializer.validated_data.get("access", None)
            refresh = serializer.validated_data.get("refresh", None)
            print("4")
            if access:
                response = Response(status=status.HTTP_200_OK)
                max_age = settings.COOKIE_TIME
                response.set_cookie('access', access, httponly=True, max_age=max_age)
                response.set_cookie('refresh', refresh, httponly=True, max_age=max_age)
                print("OK2")
                return response
            return Response({'errMsg': 'ユーザーの認証に失敗しました'}, status=status.HTTP_401_UNAUTHORIZED)
        except (TokenError, ValidationError):
            print("Not")
            return Response({'errMsg': 'Token Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args):
        response = Response(status=status.HTTP_200_OK)
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response