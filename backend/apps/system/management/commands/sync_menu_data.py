import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.system.models import Menu

MENU_DATA_FILE = Path(__file__).resolve().parent / 'menu_data.json'
MENU_JSON_FIELD_MAPPING = (
    ('menuId', 'menu_id'),
    ('menuName', 'menu_name'),
    ('orderNum', 'order_num'),
    ('path', 'path'),
    ('component', 'component'),
    ('routeName', 'route_name'),
    ('query', 'query'),
    ('isFrame', 'is_frame'),
    ('isCache', 'is_cache'),
    ('menuType', 'menu_type'),
    ('visible', 'visible'),
    ('status', 'status'),
    ('perms', 'perms'),
    ('icon', 'icon'),
    ('redirect', 'redirect'),
    ('activeMenu', 'active_menu'),
    ('isAffix', 'is_affix'),
    ('isBreadcrumb', 'is_breadcrumb'),
    ('alwaysShow', 'always_show'),
    ('remark', 'remark'),
)


def flatten_menu_tree(nodes: list[dict[str, Any]], parent_id: int = 0) -> list[dict[str, Any]]:
    flattened_menus: list[dict[str, Any]] = []
    for node in nodes:
        children = node.get('children', []) or []
        order_num = node.get('orderNum', 0)
        menu_id = node.get('menuId')
        if menu_id is None:
            menu_id = order_num if parent_id == 0 else parent_id * 100 + order_num

        menu_record = {
            'menu_id': menu_id,
            'parent_id': parent_id,
            'menu_name': node['menuName'],
            'order_num': order_num,
            'path': node.get('path', ''),
            'component': node.get('component', ''),
            'route_name': node.get('routeName', ''),
            'query': node.get('query', ''),
            'is_frame': node.get('isFrame', '1'),
            'is_cache': node.get('isCache', '0'),
            'menu_type': node.get('menuType', 'M'),
            'visible': node.get('visible', '0'),
            'status': node.get('status', '0'),
            'perms': node.get('perms', ''),
            'icon': node.get('icon', ''),
            'redirect': node.get('redirect', ''),
            'active_menu': node.get('activeMenu', ''),
            'is_affix': node.get('isAffix', False),
            'is_breadcrumb': node.get('isBreadcrumb', True),
            'always_show': node.get('alwaysShow', True),
            'remark': node.get('remark', ''),
        }
        flattened_menus.append(menu_record)
        if children:
            flattened_menus.extend(flatten_menu_tree(children, parent_id=menu_id))
    return flattened_menus


def export_menu_tree() -> list[dict[str, Any]]:
    menu_rows = list(
        Menu.objects.filter(del_flag='0')
        .order_by('parent_id', 'order_num', 'menu_id')
        .values(*(model_field for _, model_field in MENU_JSON_FIELD_MAPPING), 'parent_id')
    )
    _validate_menu_rows(menu_rows)

    children_by_parent: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in menu_rows:
        children_by_parent[row['parent_id']].append(row)
    visited_menu_ids: set[int] = set()

    def build_tree(parent_id: int = 0) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        for row in children_by_parent.get(parent_id, []):
            visited_menu_ids.add(row['menu_id'])
            node = {json_field: row[model_field] for json_field, model_field in MENU_JSON_FIELD_MAPPING}
            children = build_tree(row['menu_id'])
            if children:
                node['children'] = children
            nodes.append(node)
        return nodes

    menu_tree = build_tree()
    unvisited_menu_ids = sorted(
        row['menu_id']
        for row in menu_rows
        if row['menu_id'] not in visited_menu_ids
    )
    if unvisited_menu_ids:
        raise ValueError(f'存在未挂载到根节点的菜单记录，无法导出树结构：{unvisited_menu_ids}')
    return menu_tree


def write_menu_data_file(output_path: Path, menu_tree: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as output_file:
        json.dump(menu_tree, output_file, ensure_ascii=False, indent=2)
        output_file.write('\n')


def _validate_menu_rows(menu_rows: list[dict[str, Any]]) -> None:
    menu_ids = {row['menu_id'] for row in menu_rows}
    orphan_parent_ids = sorted(
        {
            row['parent_id']
            for row in menu_rows
            if row['parent_id'] != 0 and row['parent_id'] not in menu_ids
        }
    )
    if orphan_parent_ids:
        raise ValueError(f'存在父菜单缺失的菜单记录，无法导出树结构：{orphan_parent_ids}')

    duplicate_paths = [
        {'parent_id': parent_id, 'path': path, 'count': count}
        for (parent_id, path), count in Counter(
            (row['parent_id'], row['path']) for row in menu_rows if row['path']
        ).items()
        if count > 1
    ]
    if duplicate_paths:
        raise ValueError(f'存在重复菜单 path，无法导出稳定路由：{duplicate_paths}')

    duplicate_route_names = [
        {'route_name': route_name, 'count': count}
        for route_name, count in Counter(
            row['route_name'] for row in menu_rows if row['route_name']
        ).items()
        if count > 1
    ]
    if duplicate_route_names:
        raise ValueError(f'存在重复菜单 routeName，无法导出稳定路由：{duplicate_route_names}')


class Command(BaseCommand):
    help = '将当前数据库菜单导出并同步到 menu_data.json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            default=str(MENU_DATA_FILE),
            help='导出的 menu_data.json 路径，默认覆盖内置菜单数据文件',
        )

    def handle(self, *args, **options):
        output_path = Path(options['output']).expanduser().resolve()
        try:
            menu_tree = export_menu_tree()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        write_menu_data_file(output_path, menu_tree)
        self.stdout.write(
            self.style.SUCCESS(
                f'菜单数据已同步到 {output_path}，共导出 {self._count_menu_nodes(menu_tree)} 条记录'
            )
        )

    def _count_menu_nodes(self, nodes):
        return sum(1 + self._count_menu_nodes(node.get('children', [])) for node in nodes)
