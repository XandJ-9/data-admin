# Menu Data Migration Guide / 菜单数据迁移指南

This guide explains how to export and import menu data for project migration purposes.

## Export Menu Data / 导出菜单数据

### Basic Usage / 基本用法

```bash
# Export to default file (menu_data.json)
python manage.py export_menu

# Export to custom file
python manage.py export_menu --output my_menu_data.json

# Export with custom indentation
python manage.py export_menu --output menu_export.json --indent 4
```

### Options / 选项

- `--output`: Output file path (default: `menu_data.json`)
- `--indent`: JSON indentation level (default: `2`)

### Output Format / 输出格式

The exported JSON file contains:
```json
{
  "version": "1.0",
  "export_time": "2026-01-22T10:01:16.834974",
  "total_count": 34,
  "menus": [
    {
      "menu_id": 1,
      "parent_id": 0,
      "menu_name": "系统管理",
      "order_num": 9,
      "path": "/system",
      "component": "",
      "route_name": "系统管理",
      "query": "",
      "is_frame": "1",
      "is_cache": "0",
      "menu_type": "M",
      "visible": "0",
      "status": "0",
      "perms": "",
      "icon": "system",
      "remark": "系统管理目录",
      "create_by": "system",
      "update_by": "admin",
      "create_time": "2025-11-11T17:04:16.905101",
      "update_time": "2025-12-20T00:44:02.955335"
    }
    // ... more menus
  ]
}
```

## Import Menu Data / 导入菜单数据

### Basic Usage / 基本用法

```bash
# Import from file (skip existing menus)
python manage.py import_menu menu_data.json

# Import and overwrite existing menus
python manage.py import_menu menu_data.json --overwrite

# Import and reset audit fields to system/now
python manage.py import_menu menu_data.json --overwrite --skip-audit
```

### Options / 选项

- `input_file`: Path to JSON file to import (required)
- `--overwrite`: Update existing menus instead of skipping them
- `--skip-audit`: Reset audit fields (create_by, update_by, create_time, update_time) to system defaults

### Import Behavior / 导入行为

**Without `--overwrite`** (default):
- Creates new menus that don't exist
- Skips menus that already exist (based on `menu_id`)

**With `--overwrite`**:
- Creates new menus that don't exist
- Updates existing menus with data from JSON
- Preserves audit fields unless `--skip-audit` is used

**With `--skip-audit`**:
- Sets `create_by` and `update_by` to 'system'
- Sets `create_time` and `update_time` to current time

### Import Summary / 导入摘要

After import, you'll see a summary:
```
Import Summary:
  Created: 5
  Updated: 10
  Skipped: 19
Total: 34
```

## Migration Workflow / 迁移工作流

### From Source Environment / 从源环境

```bash
# 1. Export menu data
cd backend
python manage.py export_menu --output menu_backup_20260122.json

# 2. Copy the JSON file to target environment
```

### To Target Environment / 到目标环境

```bash
# 1. Verify the JSON file
cat menu_backup_20260122.json | head -20

# 2. Import menu data (dry run first - without --overwrite)
python manage.py import_menu menu_backup_20260122.json

# 3. If satisfied, import with overwrite
python manage.py import_menu menu_backup_20260122.json --overwrite

# 4. Verify in admin panel or via query
python manage.py shell
>>> from apps.system.models import Menu
>>> Menu.objects.filter(del_flag='0').count()
```

## Best Practices / 最佳实践

1. **Backup First / 先备份**: Always backup your database before importing
2. **Test First / 先测试**: Import without `--overwrite` first to see what would be created
3. **Verify / 验证**: Check the imported data in Django admin or via shell
4. **Version Control / 版本控制**: Commit JSON files to git for change tracking
5. **Document Changes / 记录变更**: Add comments or changelog when modifying menu structure

## Troubleshooting / 故障排除

### File Not Error / 文件未找到错误
```
File not found: menu_data.json
```
**Solution**: Check the file path and ensure you're in the correct directory

### Invalid JSON Error / 无效JSON错误
```
Invalid JSON file: Expecting property name enclosed in double quotes
```
**Solution**: Validate your JSON file using a JSON validator or linter

### Integrity Error / 完整性错误
```
IntegrityError: UNIQUE constraint failed: sys_menu.menu_id
```
**Solution**: Use `--overwrite` flag to update existing menus instead of creating duplicates

## Examples / 示例

### Export menus for production deployment / 导出菜单用于生产部署
```bash
python manage.py export_menu --output prod_menu_data.json --indent 2
```

### Import menus to staging environment / 导入菜单到测试环境
```bash
python manage.py import_menu prod_menu_data.json --overwrite --skip-audit
```

### Backup current menu structure / 备份当前菜单结构
```bash
python manage.py export_menu --output "menu_backup_$(date +%Y%m%d_%H%M%S).json"
```
