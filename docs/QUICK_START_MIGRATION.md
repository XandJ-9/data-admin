# Quick Start: Data Export & Import / 快速开始：数据导出与导入

## Export Menu Data / 导出菜单数据

```bash
cd backend
python manage.py export_menu --output menu_export.json
```

**Result**: Exports all menu records to `menu_export.json`

## Import Menu Data / 导入菜单数据

```bash
python manage.py import_menu menu_export.json --overwrite --skip-audit
```

**Options**:
- `--overwrite`: Update existing menus (如果不加此选项，将跳过已存在的菜单)
- `--skip-audit`: Reset audit fields to system defaults (重置审计字段为系统默认值)

## Export All System Data / 导出所有系统数据

```bash
python manage.py export_system_data --output system_data.json
```

**Includes**: 菜单、角色、部门、字典类型和字典数据

## Import All System Data / 导入所有系统数据

```bash
python manage.py import_system_data system_data.json --overwrite --skip-audit
```

## Export Specific Data Types / 导出特定数据类型

```bash
# Only menus and roles
python manage.py export_system_data --include menus,roles --output auth_data.json

# Only departments
python manage.py export_system_data --include depts --output org_data.json
```

## Common Use Cases / 常见用例

### 1. Backup Current Data / 备份当前数据
```bash
python manage.py export_system_data --output "backup_$(date +%Y%m%d_%H%M%S).json"
```

### 2. Sync from Production to Staging / 从生产同步到测试
```bash
# On production:
python manage.py export_system_data --output prod_data.json

# On staging:
python manage.py import_system_data prod_data.json --overwrite --skip-audit
```

### 3. Menu Migration Only / 仅迁移菜单
```bash
python manage.py export_menu --output menus.json
python manage.py import_menu menus.json --overwrite
```

## Check Exported Data / 检查导出的数据

```bash
# View first 20 lines
head -20 menu_export.json

# Count menu records
python manage.py shell -c "from apps.system.models import Menu; print(Menu.objects.filter(del_flag='0').count())"
```

## Files Created / 创建的文件

1. **export_menu.py** - Export menu data to JSON
2. **import_menu.py** - Import menu data from JSON
3. **export_system_data.py** - Export comprehensive system data
4. **import_system_data.py** - Import comprehensive system data
5. **MENU_MIGRATION.md** - Detailed menu migration guide
6. **DATA_MIGRATION_GUIDE.md** - Comprehensive data migration documentation

## Need More Help? / 需要更多帮助?

See [DATA_MIGRATION_GUIDE.md](./DATA_MIGRATION_GUIDE.md) for detailed documentation.
