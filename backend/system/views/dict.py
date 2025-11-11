from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


from ..models import DictType, DictData
from ..serializers import DictTypeSerializer, DictDataSerializer
from django.db.models import Q
from django.core.cache import cache

class DictAPIView(APIView):
    permission_classes = [IsAuthenticated]


class DictTypeListView(DictAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        dict_name = request.query_params.get('dictName', '')
        dict_type = request.query_params.get('dictType', '')
        status_value = request.query_params.get('status', '')

        qs = DictType.objects.filter(del_flag='0')
        if dict_name:
            qs = qs.filter(dict_name__icontains=dict_name)
        if dict_type:
            qs = qs.filter(dict_type__icontains=dict_type)
        if status_value:
            qs = qs.filter(status=status_value)

        qs = qs.order_by('-create_time')

        page_size = int(request.query_params.get('pageSize', 10))
        page_num = int(request.query_params.get('pageNum', 1))
        total = qs.count()
        start = (page_num - 1) * page_size
        end = start + page_size

        serializer = DictTypeSerializer(qs[start:end], many=True)
        return Response({
            'code': 200,
            'msg': '操作成功',
            'total': total,
            'rows': serializer.data
        })


class DictTypeDetailView(DictAPIView):
    def get(self, request, dict_id):
        try:
            obj = DictType.objects.get(dict_id=dict_id, del_flag='0')
        except DictType.DoesNotExist:
            return Response({'code': 404, 'msg': '字典类型不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'code': 200, 'msg': '操作成功', 'data': DictTypeSerializer(obj).data})

    def delete(self, request, dict_id):
        try:
            obj = DictType.objects.get(dict_id=dict_id, del_flag='0')
        except DictType.DoesNotExist:
            return Response({'code': 404, 'msg': '字典类型不存在'}, status=status.HTTP_404_NOT_FOUND)
        obj.del_flag = '1'
        obj.save(update_fields=['del_flag'])
        return Response({'code': 200, 'msg': '操作成功'})


class DictTypeCreateUpdateView(DictAPIView):
    def post(self, request):
        serializer = DictTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'code': 200, 'msg': '操作成功'})
        return Response({'code': 400, 'msg': '参数错误', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        dict_id = request.data.get('dictId')
        if not dict_id:
            return Response({'code': 400, 'msg': '缺少字典ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            obj = DictType.objects.get(dict_id=dict_id, del_flag='0')
        except DictType.DoesNotExist:
            return Response({'code': 404, 'msg': '字典类型不存在'}, status=status.HTTP_404_NOT_FOUND)
        serializer = DictTypeSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'code': 200, 'msg': '操作成功'})
        return Response({'code': 400, 'msg': '参数错误', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class DictTypeRefreshCacheView(DictAPIView):
    def delete(self, request):
        cache.delete('dict_optionselect')
        return Response({'code': 200, 'msg': '操作成功'})


class DictTypeOptionSelectView(DictAPIView):
    def get(self, request):
        cached = cache.get('dict_optionselect')
        if cached is not None:
            return Response({'code': 200, 'msg': '操作成功', 'data': cached})
        qs = DictType.objects.filter(status='0', del_flag='0').order_by('dict_name')
        data = [{'dictId': d.dict_id, 'dictName': d.dict_name, 'dictType': d.dict_type} for d in qs]
        cache.set('dict_optionselect', data, timeout=300)
        return Response({'code': 200, 'msg': '操作成功', 'data': data})


class DictDataListView(DictAPIView):
    def get(self, request):
        dict_type = request.query_params.get('dictType', '')
        dict_label = request.query_params.get('dictLabel', '')
        status_value = request.query_params.get('status', '')

        qs = DictData.objects.filter(del_flag='0')
        if dict_type:
            qs = qs.filter(dict_type=dict_type)
        if dict_label:
            qs = qs.filter(dict_label__icontains=dict_label)
        if status_value:
            qs = qs.filter(status=status_value)

        qs = qs.order_by('-create_time')

        page_size = int(request.query_params.get('pageSize', 10))
        page_num = int(request.query_params.get('pageNum', 1))
        total = qs.count()
        start = (page_num - 1) * page_size
        end = start + page_size

        serializer = DictDataSerializer(qs[start:end], many=True)
        return Response({'code': 200, 'msg': '操作成功', 'total': total, 'rows': serializer.data})


class DictDataDetailView(DictAPIView):
    def get(self, request, dict_code):
        try:
            obj = DictData.objects.get(dict_code=dict_code, del_flag='0')
        except DictData.DoesNotExist:
            return Response({'code': 404, 'msg': '字典数据不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'code': 200, 'msg': '操作成功', 'data': DictDataSerializer(obj).data})

    def delete(self, request, dict_code):
        try:
            obj = DictData.objects.get(dict_code=dict_code, del_flag='0')
        except DictData.DoesNotExist:
            return Response({'code': 404, 'msg': '字典数据不存在'}, status=status.HTTP_404_NOT_FOUND)
        obj.del_flag = '1'
        obj.save(update_fields=['del_flag'])
        return Response({'code': 200, 'msg': '操作成功'})


class DictDataByTypeView(DictAPIView):
    def get(self, request, dict_type):
        qs = DictData.objects.filter(dict_type=dict_type, status='0', del_flag='0').order_by('dict_sort', 'dict_label')
        serializer = DictDataSerializer(qs, many=True)
        return Response({'code': 200, 'msg': '操作成功', 'data': serializer.data})


class DictDataCreateUpdateView(DictAPIView):
    def post(self, request):
        serializer = DictDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'code': 200, 'msg': '操作成功'})
        return Response({'code': 400, 'msg': '参数错误', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        dict_code = request.data.get('dictCode')
        if not dict_code:
            return Response({'code': 400, 'msg': '缺少字典编码'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            obj = DictData.objects.get(dict_code=dict_code, del_flag='0')
        except DictData.DoesNotExist:
            return Response({'code': 404, 'msg': '字典数据不存在'}, status=status.HTTP_404_NOT_FOUND)
        serializer = DictDataSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'code': 200, 'msg': '操作成功'})
        return Response({'code': 400, 'msg': '参数错误', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)