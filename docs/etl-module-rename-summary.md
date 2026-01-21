# 模块重命名总结

## ✅ 已完成的更改

### 后端重命名：dataintegration → dataetl

**文件和目录更改：**
- ✅ 目录重命名：`backend/apps/dataintegration/` → `backend/apps/dataetl/`
- ✅ 所有 Python 文件中的引用已更新
- ✅ Django 设置更新：`config/settings.py` 中的 `INSTALLED_APPS`
- ✅ URL 配置更新：`config/urls.py` 中的路由路径
- ✅ 新 API 路径：`/data-api/dataetl/`

**数据库：**
- ✅ 表名保持不变（已经是 `etl_task`, `etl_execution`, `etl_template`）
- ✅ 迁移记录已同步（使用 --fake 标记）

### 前端重组：独立到 data/etl 目录

**目录结构更改：**
```
旧结构：
frontend/src/views/data/integration/
frontend/src/api/etl.js

新结构：
frontend/src/views/data/etl/
frontend/src/api/dataetl.js
```

**具体更改：**
- ✅ 创建了新目录：`frontend/src/views/data/etl/`
- ✅ 复制了所有文件从 `integration/` 到 `etl/`
- ✅ API 文件重命名：`etl.js` → `dataetl.js`
- ✅ 更新了 API 路径：`/dataintegration/` → `/dataetl/`
- ✅ 路由配置已更新指向新位置

### 路由配置更新

**新的路由结构（frontend/src/router/index.js）：**
```javascript
{
  path: '/data/etl',
  component: Layout,
  redirect: '/data/etl/tasks',
  meta: { title: '数据ETL', icon: 'data-integration' },
  children: [
    {
      name: 'ETLTaskList',
      path: 'tasks',
      component: () => import('@/views/data/etl/taskList'),
      meta: { title: 'ETL任务', icon: 'list' }
    },
    {
      name: 'ETLTaskSimpleCreate',
      path: 'create',
      component: () => import('@/views/data/etl/SimpleTaskCreate'),
      meta: { title: '创建ETL任务', icon: 'plus' }
    },
    {
      name: 'ETLTaskDetail',
      path: 'detail/:id',
      component: () => import('@/views/data/etl/taskDetail'),
      meta: { title: '任务详情', activeMenu: '/data/etl/tasks' },
      hidden: true
    },
    {
      name: 'ETLExecutionDetail',
      path: 'execution/:id',
      component: () => import('@/views/data/etl/components/ExecutionMonitor'),
      meta: { title: '执行详情', activeMenu: '/data/etl/tasks' },
      hidden: true
    }
  ]
}
```

## 📁 新的目录结构

### 后端
```
backend/
└── apps/
    └── dataetl/              # 之前是 dataintegration
        ├── migrations/
        ├── models.py          # ETLTask, ETLExecution, ETLTemplate
        ├── serializers.py
        ├── views.py
        └── urls.py
```

### 前端
```
frontend/
└── src/
    ├── api/
    │   └── dataetl.js        # 之前是 etl.js
    └── views/
        └── data/
            └── etl/          # 新的独立目录
                ├── taskList.vue
                ├── SimpleTaskCreate.vue
                ├── taskDetail.vue
                └── components/
                    ├── ScenarioSelector.vue
                    ├── SimplifiedWizard.vue
                    ├── ExecutionMonitor.vue
                    ├── DatasourceSelect.vue
                    ├── TableSelect.vue
                    ├── HiveTableSelect.vue
                    ├── SqlEditor.vue
                    ├── ScheduleSelect.vue
                    ├── DataPreview.vue
                    ├── ConfigSummary.vue
                    └── scenarioConfig.js
```

## 🔄 API 路径变化

### 旧路径
```
前端: @/api/etl.js
后端: /data-api/dataintegration/
```

### 新路径
```
前端: @/api/dataetl.js
后端: /data-api/dataetl/
```

## ⚠️ 需要注意的事项

### 1. 旧代码清理（可选）
如果确认一切正常工作，可以删除旧的 `integration` 目录：
```bash
# 前端
rm -rf frontend/src/views/data/integration

# 但建议先保留一段时间作为备份
```

### 2. 数据库表名
表名已经是 `etl_task`, `etl_execution`, `etl_template`，不需要重命名。

### 3. API 兼容性
如果其他模块还在使用旧的 `/data-api/dataintegration/` 路径，需要更新它们。

### 4. 前端缓存
由于文件路径改变，可能需要清除浏览器缓存或强制刷新（Ctrl+F5）

## 🧪 测试步骤

1. **启动后端**
   ```bash
   cd backend
   python manage.py runserver
   ```
   验证：访问 `http://localhost:8000/data-api/dataetl/tasks/scenarios/`

2. **启动前端**
   ```bash
   cd frontend
   pnpm dev
   ```
   验证：访问 `http://localhost:5173/data/etl/tasks`

3. **功能验证**
   - [ ] 侧边栏显示"数据ETL"菜单
   - [ ] 任务列表页面正常加载
   - [ ] 可以创建新任务
   - [ ] API 调用成功（检查浏览器 Network 标签）

## 📝 迁移清单

- [x] 后端目录重命名
- [x] 后端代码引用更新
- [x] Django settings 更新
- [x] URL 配置更新
- [x] 前端目录重组
- [x] API 文件重命名
- [x] 路由配置更新
- [x] Django 系统检查通过
- [ ] 前端功能测试
- [ ] 后端 API 测试
- [ ] （可选）删除旧文件

## 🎯 优势

1. **命名一致性**
   - 后端：`dataetl` 模块
   - 前端：`data/etl` 目录
   - API：`dataetl.js`
   - 路由：`/data/etl`

2. **语义清晰**
   - `dataetl` 明确表示数据 ETL 功能
   - 独立目录避免与其他数据模块混淆

3. **易于维护**
   - 集中的模块结构
   - 清晰的命名约定
   - 独立的前端目录

## 📞 故障排查

如果遇到问题：

1. **Django 迁移错误**
   ```bash
   python manage.py showmigrations dataetl
   python manage.py migrate dataetl --fake
   ```

2. **前端导入错误**
   - 清除 node_modules 缓存：`rm -rf node_modules/.vite`
   - 重新启动：`pnpm dev`

3. **API 404 错误**
   - 检查浏览器 Network 标签，确认请求路径是 `/data-api/dataetl/...`
   - 确认后端运行正常

4. **路由不工作**
   - 清除浏览器缓存
   - 强制刷新：Ctrl+F5
   - 检查控制台错误信息
