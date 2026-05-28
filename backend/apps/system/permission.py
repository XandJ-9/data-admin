from rest_framework.permissions import BasePermission
from .models import Menu, RoleMenu, UserRole


def _as_list(value):
    if value in (None, '', False):
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def get_user_role_context(user):
    try:
        user_roles = list(
            UserRole.objects.filter(
                user=user,
                del_flag='0',
                role__status='0',
                role__del_flag='0',
            ).select_related('role')
        )
        roles = [ur.role.role_key for ur in user_roles]
    except Exception:
        user_roles = []
        roles = []
    return user_roles, roles


def user_has_menu_permission(user, required_permissions) -> bool:
    user_roles, roles = get_user_role_context(user)
    if 'admin' in roles:
        return True

    required_permissions = _as_list(required_permissions)
    if not required_permissions:
        return False

    role_ids = [ur.role_id for ur in user_roles]
    granted_permissions = set(
        Menu.objects.filter(
            menu_id__in=RoleMenu.objects.filter(
                role_id__in=role_ids,
                del_flag='0',
            ).values_list('menu_id', flat=True),
            del_flag='0',
            status='0',
            perms__gt='',
        ).values_list('perms', flat=True)
    )
    if '*:*:*' in granted_permissions:
        return True
    return bool(set(required_permissions) & granted_permissions)


class HasRolePermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        user_roles, roles = get_user_role_context(user)
        if 'admin' in roles:
            return True

        required_permissions = self._get_required_permissions(request, view)
        if required_permissions:
            return user_has_menu_permission(user, required_permissions)

        required = getattr(view, 'required_roles', 'common')
        required_roles = _as_list(required)
        if not required_roles:
            return False
        return any(role in roles for role in required_roles)

    def _get_required_permissions(self, request, view):
        action = getattr(view, 'action', None) or request.method.lower()
        permission_map = getattr(view, 'permission_map', {}) or {}
        if action in permission_map:
            return _as_list(permission_map[action])
        required_permissions = getattr(view, 'required_permissions', None)
        return _as_list(required_permissions)
