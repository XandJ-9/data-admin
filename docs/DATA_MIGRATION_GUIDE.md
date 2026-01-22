# Data Migration Commands / 数据迁移命令

This guide provides comprehensive documentation for exporting and importing system data for project migration purposes.

## Available Commands / 可用命令

### 1. Menu Export/Import / 菜单导出/导入

#### Export Menu Data
```bash
# Export to default file (menu_data.json)
python manage.py export_menu

# Export to custom file
python manage.py export_menu --output my_menu.json

# Export with custom indentation
python manage.py export_menu --output menu.json --indent 4
```

#### Import Menu Data
```bash
# Import (skip existing)
python manage.py import_menu menu.json

# Import and overwrite existing
python manage.py import_menu menu.json --overwrite

# Import with reset audit fields
python manage.py import_menu menu.json --overwrite --skip-audit
```

### 2. System Data Export/Import / 系统数据导出/导入

#### Export All System Data
```bash
# Export all data types (menus, roles, depts, dicts)
python manage.py export_system_data --output system_data.json

# Export specific data types only
python manage.py export_system_data --include menus,roles --output auth_data.json

# Export with custom formatting
python manage.py export_system_data --output data.json --indent 4
```

#### Import System Data
```bash
# Import all data (skip existing)
python manage.py import_system_data system_data.json

# Import and overwrite existing
python manage.py import_system_data system_data.json --overwrite

# Import with reset audit fields
python manage.py import_system_data system_data.json --overwrite --skip-audit
```

## Data Types / 数据类型

The `export_system_data` command supports the following data types:

| Type | Description | Tables |
|------|-------------|--------|
| `menus` | Menu tree structure | `sys_menu` |
| `roles` | User roles | `sys_role` |
| `depts` | Department hierarchy | `sys_dept` |
| `dicts` | Dictionary types and data | `sys_dict_type`, `sys_dict_data` |

Note: When exporting `roles`, role-menu associations (`sys_role_menu`) are automatically included.

## Command Options / 命令选项

### export_menu Options
- `--output`: Output file path (default: `menu_data.json`)
- `--indent`: JSON indentation (default: `2`)

### import_menu Options
- `input_file`: Path to JSON file (required)
- `--overwrite`: Update existing records instead of skipping
- `--skip-audit`: Reset audit fields to system defaults

### export_system_data Options
- `--output`: Output file path (default: `system_data.json`)
- `--indent`: JSON indentation (default: `2`)
- `--include`: Comma-separated data types (default: `menus,roles,depts,dicts`)

### import_system_data Options
- `input_file`: Path to JSON file (required)
- `--overwrite`: Update existing records instead of skipping
- `--skip-audit`: Reset audit fields to system defaults

## JSON Structure / JSON结构

### Menu Export Format
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
      "remark": "系统管理目录"
    }
  ]
}
```

### System Data Export Format
```json
{
  "version": "1.0",
  "export_time": "2026-01-22T10:47:04.202035",
  "data_types": ["menus", "roles", "depts", "dicts"],
  "menus": [...],
  "roles": [...],
  "role_menus": [...],
  "departments": [...],
  "dict_types": [...],
  "dict_data": [...],
  "menu_count": 34,
  "role_count": 3,
  "role_menu_count": 14,
  "department_count": 3,
  "dict_type_count": 6,
  "dict_data_count": 19
}
```

## Import Behavior / 导入行为

### Without --overwrite (Default)
- Creates new records that don't exist (based on primary key)
- Skips existing records
- Preserves all existing data

### With --overwrite
- Creates new records that don't exist
- Updates existing records with data from JSON
- Preserves audit fields unless `--skip-audit` is used

### With --skip-audit
- Sets `create_by` and `update_by` to 'system'
- Sets `create_time` and `update_time` to current time
- Useful for clean migrations without carrying over historical timestamps

## Migration Workflows / 迁移工作流

### Quick Start / 快速开始

```bash
# 1. Export from source environment
cd backend
python manage.py export_system_data --output production_data.json

# 2. Transfer file to target environment

# 3. Import to target environment
python manage.py import_system_data production_data.json --overwrite --skip-audit
```

### Menu-Only Migration / 仅菜单迁移

```bash
# Export menus only
python manage.py export_menu --output menus_20260122.json

# Import to target
python manage.py import_menu menus_20260122.json --overwrite
```

### Selective Data Export / 选择性数据导出

```bash
# Export only menus and roles (no depts or dicts)
python manage.py export_system_data --include menus,roles --output auth_data.json

# Export only departments
python manage.py export_system_data --include depts --output org_data.json
```

### Backup Before Changes / 更改前备份

```bash
# Create timestamped backup
python manage.py export_system_data --output "backup_$(date +%Y%m%d_%H%M%S).json"
```

### Verify Import / 验证导入

```bash
# 1. Dry run (without --overwrite) to see what would be created
python manage.py import_system_data data.json

# 2. Check the summary output
# 3. If satisfied, run with --overwrite
python manage.py import_system_data data.json --overwrite

# 4. Verify in Django shell
python manage.py shell
>>> from apps.system.models import Menu, Role
>>> Menu.objects.filter(del_flag='0').count()
34
>>> Role.objects.filter(del_flag='0').count()
3
```

## Best Practices / 最佳实践

### 1. Environment-Specific Backups / 环境特定备份
```bash
# Development
python manage.py export_system_data --output dev_data.json

# Staging
python manage.py export_system_data --output staging_data.json

# Production
python manage.py export_system_data --output prod_data.json
```

### 2. Version Control / 版本控制
```bash
# Commit to git for change tracking
git add backend/data_exports/*.json
git commit -m "Add menu configuration snapshot"
```

### 3. Incremental Updates / 增量更新
```bash
# Export after making changes
python manage.py export_menu --output menu_update_20260122.json

# Document changes in a changelog
echo "2026-01-22: Added new 'Reports' menu" >> MENU_CHANGELOG.md
```

### 4. Testing Before Production / 生产前测试
```bash
# 1. Export from staging
python manage.py export_system_data --output staging_test.json

# 2. Import to development
python manage.py import_system_data staging_test.json --overwrite --skip-audit

# 3. Test thoroughly in development
# 4. If successful, import to production
```

### 5. Data Integrity / 数据完整性
```bash
# Always export complete related data together
python manage.py export_system_data --include menus,roles --output auth_config.json
# This ensures role-menu associations are included
```

## Troubleshooting / 故障排除

### Common Errors / 常见错误

#### File Not Found
```bash
File not found: menu_data.json
```
**Solution**: Check file path and ensure you're in the correct directory

#### Invalid JSON
```bash
Invalid JSON file: Expecting property name enclosed in double quotes
```
**Solution**: Validate JSON file using a validator or linter

#### Integrity Error
```bash
IntegrityError: UNIQUE constraint failed: sys_menu.menu_id
```
**Solution**: Use `--overwrite` flag to update existing records

#### Foreign Key Constraint
```bash
IntegrityError: FOREIGN KEY constraint failed
```
**Solution**: Import parent records before child records (e.g., roles before role_menus)

### Debug Mode / 调试模式

```bash
# Run with verbosity to see detailed output
python manage.py import_system_data data.json --overwrite -v 2

# Check Django logs for detailed errors
# Add to settings.py:
# LOG_LEVEL = 'DEBUG'
```

## Examples / 示例

### Example 1: Initial Setup / 初始设置
```bash
# Export from development
python manage.py export_system_data --output initial_setup.json

# Import to new staging environment
python manage.py import_system_data initial_setup.json --overwrite --skip-audit
```

### Example 2: Menu Structure Update / 菜单结构更新
```bash
# 1. Backup current menus
python manage.py export_menu --output menu_before_changes.json

# 2. Make changes in admin panel

# 3. Export updated menus
python manage.py export_menu --output menu_after_changes.json

# 4. Import to staging for testing
python manage.py import_menu menu_after_changes.json --overwrite
```

### Example 3: Cross-Environment Sync / 跨环境同步
```bash
# From production to staging
python manage.py export_system_data --output prod_to_staging.json
scp prod_to_staging.json user@staging-server:/backend/
# On staging server:
python manage.py import_system_data prod_to_staging.json --overwrite --skip-audit
```

### Example 4: Selective Menu Export / 选择性菜单导出
```bash
# Export only specific module menus by filtering after export
python manage.py export_menu --output all_menus.json

# Then manually edit the JSON to keep only specific menus
# or use jq for filtering:
jq '.menus[] | select(.menu_type == "C")' all_menus.json
```

## File Organization / 文件组织

Recommended directory structure for exported data:

```
backend/
├── data_exports/
│   ├── menus/
│   │   ├── menu_20260122.json
│   │   └── menu_20260123.json
│   ├── system/
│   │   ├── dev_20260122.json
│   │   ├── staging_20260122.json
│   │   └── prod_20260122.json
│   └── backups/
│       └── emergency_backup.json
└── management/
    └── commands/
```

## Security Considerations / 安全考虑

1. **Sensitive Data**: Exported data may contain sensitive information. Store securely.
2. **Access Control**: Limit access to export files using file permissions.
3. **Version Control**: Be careful not to commit sensitive data to public repositories.
4. **Backup Encryption**: Consider encrypting backups before storage/transmission.
5. **Audit Trail**: Keep track of who exported/imported data and when.

## Related Commands / 相关命令

```bash
# Initialize system with default data
python manage.py init_system

# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## Additional Resources / 其他资源

- [Django Management Commands](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)
- [Project Documentation](./CLAUDE.md)
- [Database Models](../apps/system/models.py)
