from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from apps.system.views.core import BaseViewSet, BaseViewMixin
from apps.system.permission import HasRolePermission

import os
import sys
import time
import platform
import socket
import shutil
from datetime import datetime, timedelta


PROCESS_START_TIME = time.time()


def _format_bytes_gb(b):
    try:
        return round(float(b) / (1024 ** 3), 2)
    except Exception:
        return 0.0


def _get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return '127.0.0.1'


def _get_mem_info():
    total = used = free = usage = 0.0
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ('dwLength', ctypes.c_ulong),
                ('dwMemoryLoad', ctypes.c_ulong),
                ('ullTotalPhys', ctypes.c_ulonglong),
                ('ullAvailPhys', ctypes.c_ulonglong),
                ('ullTotalPageFile', ctypes.c_ulonglong),
                ('ullAvailPageFile', ctypes.c_ulonglong),
                ('ullTotalVirtual', ctypes.c_ulonglong),
                ('ullAvailVirtual', ctypes.c_ulonglong),
                ('sullAvailExtendedVirtual', ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_b = int(stat.ullTotalPhys)
        avail_b = int(stat.ullAvailPhys)
        used_b = total_b - avail_b
        total = _format_bytes_gb(total_b)
        used = _format_bytes_gb(used_b)
        free = _format_bytes_gb(avail_b)
        usage = round((used / total) * 100, 2) if total else 0.0
    except Exception:
        try:
            import psutil  # type: ignore
            vm = psutil.virtual_memory()
            total = _format_bytes_gb(vm.total)
            used = _format_bytes_gb(vm.used)
            free = _format_bytes_gb(vm.available)
            usage = round((vm.used / vm.total) * 100, 2) if vm.total else 0.0
        except Exception:
            pass
    return {
        'total': total,
        'used': used,
        'free': free,
        'usage': usage,
    }


def _get_cpu_info():
    cpu_num = os.cpu_count() or 0
    used = sys_p = 0.0
    free = 100.0
    try:
        import psutil  # type: ignore
        used = float(psutil.cpu_percent(interval=0.2))
        sys_p = 0.0
        free = max(0.0, 100.0 - used - sys_p)
    except Exception:
        used = 0.0
        sys_p = 0.0
        free = 100.0
    return {
        'cpuNum': cpu_num,
        'used': round(used, 2),
        'sys': round(sys_p, 2),
        'free': round(free, 2),
    }


def _get_jvm_info():
    name = platform.python_implementation()
    version = platform.python_version()
    start_dt = datetime.fromtimestamp(PROCESS_START_TIME)
    run_delta = datetime.now() - start_dt
    hours, remainder = divmod(run_delta.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    run_time = f"{int(hours)}小时{int(minutes)}分钟"
    home = sys.executable
    input_args = ' '.join(sys.argv)
    return {
        'name': name,
        'version': version,
        'startTime': start_dt.strftime('%Y-%m-%d %H:%M:%S'),
        'runTime': run_time,
        'home': home,
        'inputArgs': input_args,
        'total': 0,
        'used': 0,
        'free': 0,
        'usage': 0,
    }


def _get_sys_files():
    items = []
    try:
        base = os.getcwd()
        total, used, free = shutil.disk_usage(base)
        usage = round((used / total) * 100, 2) if total else 0.0
        items.append({
            'dirName': base,
            'sysTypeName': platform.system(),
            'typeName': 'Fixed',
            'total': f"{_format_bytes_gb(total)}G",
            'free': f"{_format_bytes_gb(free)}G",
            'used': f"{_format_bytes_gb(used)}G",
            'usage': usage,
        })
    except Exception:
        pass
    return items


class ServerView(BaseViewMixin, ViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]

    def get(self, request):
        data = {
            'cpu': _get_cpu_info(),
            'mem': _get_mem_info(),
            'sys': {
                'computerName': platform.node(),
                'osName': f"{platform.system()} {platform.release()}",
                'computerIp': _get_local_ip(),
                'osArch': platform.machine(),
                'userDir': os.getcwd(),
            },
            'jvm': _get_jvm_info(),
            'sysFiles': _get_sys_files(),
        }
        return self.data(data)


class OnlineViewSet(BaseViewMixin, ViewSet):
    permission_classes = [IsAuthenticated, HasRolePermission]

    @action(detail=False, methods=['get'], url_path='list')
    def list_action(self, request):
        ipaddr = request.query_params.get('ipaddr', '')
        user_name = request.query_params.get('userName', '')
        ua = request.META.get('HTTP_USER_AGENT', '')
        token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        user = getattr(request, 'user', None)
        dept_name = ''
        try:
            from apps.system.models import Dept
            if user and getattr(user, 'dept_id', None):
                d = Dept.objects.filter(dept_id=user.dept_id).first()
                dept_name = d.dept_name if d else ''
        except Exception:
            pass
        rows = []
        if user and getattr(user, 'username', None):
            if (not user_name) or (user.username.find(user_name) >= 0):
                row = {
                    'tokenId': token or '',
                    'userName': user.username,
                    'deptName': dept_name,
                    'ipaddr': request.META.get('REMOTE_ADDR', ''),
                    'loginLocation': '',
                    'os': platform.system(),
                    'browser': ua,
                    'loginTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
                if (not ipaddr) or (row['ipaddr'].find(ipaddr) >= 0):
                    rows.append(row)
        # return Response({'code': 200, 'msg': '操作成功', 'rows': rows, 'total': len(rows)})
        return self.raw_response({'code': 200, 'msg': '操作成功', 'rows': rows, 'total': len(rows)})

    @action(methods=['DELETE'], detail=False, url_path='force-logout')
    def destroy_by_token(self, request, *args, **kwargs):
        return self.ok('操作成功')
