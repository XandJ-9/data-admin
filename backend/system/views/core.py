from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status, viewsets
from rest_framework_simplejwt.views import TokenObtainPairView
from captcha.models import CaptchaStore
from captcha.views import captcha_image
import base64

from ..models import UserRole, Menu, DictType, DictData
from ..serializers import DictTypeSerializer, DictDataSerializer, UserProfileSerializer, UserInfoSerializer
from django.db.models import Q
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from ..common import audit_log, normalize_input

from drf_spectacular.utils import extend_schema


 


class CaptchaView(TokenObtainPairView):
    def get(self, request, *args, **kwargs):
        hashkey = CaptchaStore.generate_key()
        img_response = captcha_image(request._request, hashkey)
        img_base64 = base64.b64encode(img_response.content).decode()
        resp = Response({
            'img': img_base64,
            'uuid': hashkey,
            'captchaEnabled': True
        })
        resp['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp['Pragma'] = 'no-cache'
        resp['Expires'] = '0'
        return resp


class LoginView(TokenObtainPairView):
    @audit_log
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({'msg': '用户名或密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'token': serializer.validated_data.get('access')})


class GetInfoView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserInfoSerializer)
    def get(self, request):
        user = request.user
        user_data = {
            'userId': user.id,
            'userName': user.username,
            'nickName': getattr(user, 'nick_name', '') or user.username,
            'avatar': getattr(user, 'avatar', '') or '',
            'phonenumber': getattr(user, 'phonenumber', '') or '',
            'email': getattr(user, 'email', '') or '',
            'sex': getattr(user, 'sex', '2'),
        }

        try:
            user_roles = UserRole.objects.filter(user=user).select_related('role')
            roles = [ur.role.role_key for ur in user_roles]
        except Exception:
            roles = []
        if "admin" in roles:
            permissions = ["*:*:*"]
        else:
            permissions = []

        resp = {
            'code': 200,
            'msg': '操作成功',
            'user': user_data,
            'roles': roles,
            'permissions': permissions,
            'isDefaultModifyPwd': False,
            'isPasswordExpired': False,
        }
        return Response(resp)


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @audit_log
    def post(self, request):
        return Response({'code': 200, 'msg': '操作成功'})


class GetRoutersView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cached = cache.get('routers')
        if cached is not None:
            return Response({"code": 200, "msg": "操作成功", "data": cached})
        menus = list(Menu.objects.filter(status='0', del_flag='0').order_by('parent_id', 'order_num'))

        def build_tree(items, pid=0):
            nodes = []
            for m in items:
                if m.parent_id == pid:
                    children = build_tree(items, m.menu_id)
                    nodes.append({"menu": m, "children": children})
            return nodes

        def to_router(node):
            m = node["menu"]
            children = node["children"]
            hidden = (m.visible == '1')
            is_outer = (m.is_frame == '0')

            meta = {
                "title": m.menu_name,
                "icon": m.icon or None,
                "noCache": (m.is_cache == '1')
            }
            if m.query:
                meta["query"] = m.query

            if m.menu_type == 'M':
                route = {
                    "path": m.path or ("/" + str(m.menu_id)),
                    "component": "Layout" if m.parent_id == 0 else "ParentView",
                    "hidden": hidden,
                    "alwaysShow": True,
                    "name": m.menu_name.replace('-', '').replace('_', ''),
                    "meta": meta
                }
                route["children"] = [r for r in [to_router(c) for c in children] if r is not None]
                return route
            elif m.menu_type == 'C':
                if is_outer and (m.path.startswith('http://') or m.path.startswith('https://')):
                    return {
                        "path": m.path,
                        "component": "InnerLink",
                        "hidden": hidden,
                        "name": m.menu_name.replace('-', '').replace('_', ''),
                        "meta": meta
                    }
                return {
                    "path": m.path or ("/" + str(m.menu_id)),
                    "component": m.component or "Layout",
                    "hidden": hidden,
                    "name": m.menu_name.replace('-', '').replace('_', ''),
                    "meta": meta
                }
            else:
                return None

        tree = build_tree(menus, 0)
        routers = [r for r in [to_router(n) for n in tree] if r is not None]
        cache.set('routers', routers, timeout=3600)
        return Response({"code": 200, "msg": "操作成功", "data": routers})


class BaseViewSet(viewsets.ModelViewSet):
    required_roles = None

    def get_queryset(self):
        qs = super().get_queryset()
        model = qs.model
        if hasattr(model, 'del_flag'):
            try:
                qs = qs.filter(del_flag='0')
            except Exception:
                pass
        return qs

    @audit_log
    def create(self, request, *args, **kwargs):
        data = normalize_input(request.data)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'code': 200, 'msg': '操作成功'})

    @audit_log
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = normalize_input(request.data)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'code': 200, 'msg': '操作成功'})

    @audit_log
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = getattr(self.request, 'user', None)
        kwargs = {}
        if hasattr(serializer.Meta.model, 'create_by') and user and getattr(user, 'username', None):
            kwargs['create_by'] = user.username
        if hasattr(serializer.Meta.model, 'update_by') and user and getattr(user, 'username', None):
            kwargs['update_by'] = user.username
        serializer.save(**kwargs)

    def perform_update(self, serializer):
        user = getattr(self.request, 'user', None)
        kwargs = {}
        if hasattr(serializer.Meta.model, 'update_by') and user and getattr(user, 'username', None):
            kwargs['update_by'] = user.username
        serializer.save(**kwargs)

    @audit_log
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if hasattr(instance, 'del_flag'):
            instance.del_flag = '1'
            instance.save(update_fields=['del_flag'])
            return Response({'code': 200, 'msg': '操作成功'})
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'],url_path='list')
    def model_list(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)