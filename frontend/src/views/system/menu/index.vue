<template>
   <div class="app-container">
      <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
         <el-form-item label="菜单名称" prop="menuName">
            <el-input
               v-model="queryParams.menuName"
               placeholder="请输入菜单名称"
               clearable
               style="width: 200px"
               @keyup.enter="handleQuery"
            />
         </el-form-item>
         <el-form-item label="状态" prop="status">
            <el-select v-model="queryParams.status" placeholder="菜单状态" clearable style="width: 200px">
               <el-option
                  v-for="dict in sys_normal_disable"
                  :key="dict.value"
                  :label="dict.label"
                  :value="dict.value"
               />
            </el-select>
         </el-form-item>
         <el-form-item>
            <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
            <el-button icon="Refresh" @click="resetQuery">重置</el-button>
         </el-form-item>
      </el-form>

      <el-row :gutter="10" class="mb8">
         <el-col :span="1.5">
            <el-button
               type="primary"
               plain
               icon="Plus"
               @click="handleAdd"
               v-hasPermi="['system:menu:add']"
            >新增</el-button>
         </el-col>
         <el-col :span="1.5">
            <el-button 
               type="info"
               plain
               icon="Sort"
               @click="toggleExpandAll"
            >展开/折叠</el-button>
         </el-col>
         <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
      </el-row>

      <el-table
         ref="menuTable"
         v-loading="loading"
         :data="menuList"
         row-key="menuId"
         :default-expand-all="isExpandAll"
         :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
      >
         <template #empty>
            <el-empty description="暂无菜单数据" />
         </template>
         <el-table-column prop="menuName" label="菜单名称" :show-overflow-tooltip="true" width="160"></el-table-column>
         <el-table-column prop="icon" label="图标" align="center" width="100">
            <template #default="scope">
               <svg-icon :icon-class="scope.row.icon" />
            </template>
         </el-table-column>
         <el-table-column prop="menuType" label="菜单类型" width="80">
            <template #default="scope">
                    <el-tag v-if="scope.row.menuType==='M'" type="primary">目录</el-tag>
                    <el-tag v-else-if="scope.row.menuType==='C'" type="success">菜单</el-tag>
                    <el-tag v-else-if="scope.row.menuType==='F'" type="warning">按钮</el-tag>
            </template>
         </el-table-column>
         <el-table-column prop="orderNum" label="排序" width="60"></el-table-column>
         <el-table-column prop="path" label="路径" :show-overflow-tooltip="true"></el-table-column>
         <el-table-column prop="component" label="组件路径" :show-overflow-tooltip="true"></el-table-column>
         <el-table-column prop="routeName" label="路由名称" :show-overflow-tooltip="true"></el-table-column>
         <el-table-column prop="perms" label="权限标识" :show-overflow-tooltip="true"></el-table-column>
         <el-table-column prop="status" label="状态" width="80">
            <template #default="scope">
               <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
            </template>
         </el-table-column>
         <el-table-column label="创建时间" align="center" width="160" prop="createTime">
            <template #default="scope">
               <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
         </el-table-column>
         <el-table-column label="操作" align="center" width="210" class-name="small-padding fixed-width">
            <template #default="scope">
               <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['system:menu:edit']">修改</el-button>
               <el-button link type="primary" icon="Plus" @click="handleAdd(scope.row)" v-hasPermi="['system:menu:add']">新增</el-button>
               <el-button link type="primary" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['system:menu:remove']">删除</el-button>
            </template>
         </el-table-column>
      </el-table>

      <!-- 添加或修改菜单对话框 -->
      <el-dialog :title="title" v-model="open" width="680px" append-to-body>
         <el-form ref="menuRef" :model="form" :rules="rules" label-width="100px">
            <el-row>
               <el-col :span="24">
                  <el-form-item label="上级菜单">
                     <el-tree-select
                        v-model="form.parentId"
                        :data="menuOptions"
                        :props="{ value: 'menuId', label: 'menuName', children: 'children' }"
                        value-key="menuId"
                        placeholder="选择上级菜单"
                        check-strictly
                     />
                  </el-form-item>
               </el-col>
               <el-col :span="24">
                  <el-form-item label="菜单类型" prop="menuType">
                     <el-radio-group v-model="form.menuType">
                        <el-radio value="M">目录</el-radio>
                        <el-radio value="C">菜单</el-radio>
                        <el-radio value="F">按钮</el-radio>
                     </el-radio-group>
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType != 'F'">
                  <el-form-item label="菜单图标" prop="icon">
                     <el-popover
                        placement="bottom-start"
                        :width="540"
                        trigger="click"
                     >
                        <template #reference>
                           <el-input v-model="form.icon" placeholder="点击选择图标" @blur="showSelectIcon" readonly>
                              <template #prefix>
                                 <svg-icon
                                    v-if="form.icon"
                                    :icon-class="form.icon"
                                    class="el-input__icon"
                                    style="height: 32px;width: 16px;"
                                 />
                                 <el-icon v-else style="height: 32px;width: 16px;"><search /></el-icon>
                              </template>
                           </el-input>
                        </template>
                        <icon-select ref="iconSelectRef" @selected="selected" :active-icon="form.icon" />
                     </el-popover>
                  </el-form-item>
               </el-col>
               <el-col :span="12">
                  <el-form-item label="显示排序" prop="orderNum">
                     <el-input-number v-model="form.orderNum" controls-position="right" :min="0" />
                  </el-form-item>
               </el-col>
               <el-col :span="12">
                  <el-form-item label="菜单名称" prop="menuName">
                     <el-input v-model="form.menuName" placeholder="请输入菜单名称" />
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType == 'C'">
                  <el-form-item prop="routeName">
                     <template #label>
                        <span>
                           <el-tooltip content="默认不填则和路由地址相同：如地址为：`user`，则名称为`User`（注意：因为router会删除名称相同路由，为避免名字的冲突，特殊情况下请自定义，保证唯一性）" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           路由名称
                        </span>
                     </template>
                     <el-input v-model="form.routeName" placeholder="请输入路由名称" />
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType != 'F'">
                  <el-form-item>
                     <template #label>
                        <span>
                           <el-tooltip content="选择是外链则路由地址需要以`http(s)://`开头" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>是否外链
                        </span>
                     </template>
                     <el-radio-group v-model="form.isFrame">
                        <el-radio value="0">是</el-radio>
                        <el-radio value="1">否</el-radio>
                     </el-radio-group>
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType != 'F'">
                  <el-form-item prop="path">
                     <template #label>
                        <span>
                           <el-tooltip content="访问的路由地址，如：`user`，如外网地址需内链访问则以`http(s)://`开头" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           路由地址
                        </span>
                     </template>
                     <el-input v-model="form.path" placeholder="请输入路由地址" />
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType == 'C'">
                  <el-form-item prop="component">
                     <template #label>
                        <span>
                           <el-tooltip content="访问的组件路径，如：`system/user/index`，默认在`views`目录下" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           组件路径
                        </span>
                     </template>
                     <el-input v-model="form.component" placeholder="请输入组件路径" />
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType != 'M'">
                  <el-form-item>
                     <el-input v-model="form.perms" placeholder="请输入权限标识" maxlength="100" />
                     <template #label>
                        <span>
                           <el-tooltip content="控制器中定义的权限字符，如：@PreAuthorize(`@ss.hasPermi('system:user:list')`)" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           权限字符
                        </span>
                     </template>
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType == 'C'">
                  <el-form-item>
                     <el-input v-model="form.query" placeholder="请输入路由参数" maxlength="255" />
                     <template #label>
                        <span>
                           <el-tooltip content='访问路由的默认传递参数，如：`{"id": 1, "name": "ry"}`' placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           路由参数
                        </span>
                     </template>
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType == 'C'">
                  <el-form-item>
                     <template #label>
                        <span>
                           <el-tooltip content="选择是则会被`keep-alive`缓存，需要匹配组件的`name`和地址保持一致" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           是否缓存
                        </span>
                     </template>
                     <el-radio-group v-model="form.isCache">
                        <el-radio value="0">缓存</el-radio>
                        <el-radio value="1">不缓存</el-radio>
                     </el-radio-group>
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType != 'F'">
                  <el-form-item>
                     <template #label>
                        <span>
                           <el-tooltip content="选择隐藏则路由将不会出现在侧边栏，但仍然可以访问" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           显示状态
                        </span>
                     </template>
                     <el-radio-group v-model="form.visible">
                        <el-radio
                           v-for="dict in sys_show_hide"
                           :key="dict.value"
                           :value="dict.value"
                        >{{ dict.label }}</el-radio>
                     </el-radio-group>
                  </el-form-item>
               </el-col>
               <el-col :span="12">
                  <el-form-item>
                     <template #label>
                        <span>
                           <el-tooltip content="选择停用则路由将不会出现在侧边栏，也不能被访问" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           菜单状态
                        </span>
                     </template>
                     <el-radio-group v-model="form.status">
                        <el-radio
                           v-for="dict in sys_normal_disable"
                           :key="dict.value"
                           :value="dict.value"
                        >{{ dict.label }}</el-radio>
                     </el-radio-group>
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType == 'M'">
                  <el-form-item>
                     <template #label>
                        <span>
                           <el-tooltip content="目录的默认重定向路径，如：`noRedirect`表示不可点击" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           重定向
                        </span>
                     </template>
                     <el-input v-model="form.redirect" placeholder="请输入重定向地址" />
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType == 'C'">
                  <el-form-item>
                     <template #label>
                        <span>
                           <el-tooltip content="指定侧边栏高亮的菜单路径，如编辑页面高亮列表页：`/system/user`" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           高亮菜单
                        </span>
                     </template>
                     <el-input v-model="form.activeMenu" placeholder="请输入高亮菜单路径" />
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType == 'C'">
                  <el-form-item>
                     <template #label>
                        <span>
                           <el-tooltip content="选择固定则该标签页不可关闭，始终显示在标签栏" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           固定标签
                        </span>
                     </template>
                     <el-radio-group v-model="form.isAffix">
                        <el-radio :value="true">固定</el-radio>
                        <el-radio :value="false">不固定</el-radio>
                     </el-radio-group>
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType != 'F'">
                  <el-form-item>
                     <template #label>
                        <span>
                           <el-tooltip content="选择隐藏则该路由不会出现在面包屑导航中" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           面包屑
                        </span>
                     </template>
                     <el-radio-group v-model="form.isBreadcrumb">
                        <el-radio :value="true">显示</el-radio>
                        <el-radio :value="false">隐藏</el-radio>
                     </el-radio-group>
                  </el-form-item>
               </el-col>
               <el-col :span="12" v-if="form.menuType == 'M'">
                  <el-form-item>
                     <template #label>
                        <span>
                           <el-tooltip content="当目录只有一个子菜单时，是否仍显示目录节点" placement="top">
                              <el-icon><question-filled /></el-icon>
                           </el-tooltip>
                           总是显示
                        </span>
                     </template>
                     <el-radio-group v-model="form.alwaysShow">
                        <el-radio :value="true">是</el-radio>
                        <el-radio :value="false">否</el-radio>
                     </el-radio-group>
                  </el-form-item>
               </el-col>
            </el-row>
         </el-form>
         <template #footer>
            <div class="dialog-footer">
               <el-button type="primary" @click="submitForm">确 定</el-button>
               <el-button @click="cancel">取 消</el-button>
            </div>
         </template>
      </el-dialog>
   </div>
</template>

<script setup name="Menu">
import { addMenu, delMenu, getMenu, listMenu, updateMenu } from "@/api/system/menu"
import SvgIcon from "@/components/SvgIcon"
import IconSelect from "@/components/IconSelect"

const { proxy } = getCurrentInstance()
const { sys_show_hide, sys_normal_disable } = proxy.useDict("sys_show_hide", "sys_normal_disable")

const menuList = ref([])
const open = ref(false)
const loading = ref(true)
const showSearch = ref(true)
const title = ref("")
const menuOptions = ref([])
const isExpandAll = ref(false)
const iconSelectRef = ref(null)

const data = reactive({
  form: {},
  queryParams: {
    menuName: undefined,
    status: undefined
  },
  rules: {
    menuName: [{ required: true, message: "菜单名称不能为空", trigger: "blur" }],
    orderNum: [{ required: true, message: "菜单顺序不能为空", trigger: "blur" }],
    path: [
      { 
        validator: (rule, value, callback) => {
          // 按钮类型不需要路径
          if (form.value.menuType === 'F') {
            callback()
            return
          }
          // 目录和菜单类型必须填写路径
          if (!value) {
            callback(new Error("路由地址不能为空"))
            return
          }
          // 外链地址必须以 http(s):// 开头
          if (form.value.isFrame === '0') {
            if (!/^https?:\/\/.+/.test(value)) {
              callback(new Error("外链地址必须以 http:// 或 https:// 开头"))
            } else {
              callback()
            }
            return
          }
          // 内部路由：允许字母、数字、斜杠、下划线、连字符、冒号（路由参数）及括号（参数正则约束）
          if (!/^[a-zA-Z0-9\/_\-:().\\\+*?]*$/.test(value)) {
            callback(new Error("路由地址格式不正确"))
            return
          }
          callback()
        }, 
        trigger: "blur" 
      }
    ]
  },
})

const { queryParams, form, rules } = toRefs(data)

/** 统一 API 错误处理 */
function handleApiError(error, message = '操作失败') {
  // 开发环境才输出详细错误
  if (import.meta.env.MODE === 'development') {
    console.error('[Menu API Error]:', error)
  } else {
    // 生产环境只记录错误类型
    console.error(`[Menu Error]: ${message}`)
  }
  proxy.$modal.msgError(message)
}

/** 安全的路由名称生成 */
function generateRouteName(name, path) {
  if (!name) return ''
  
  // 优先使用路径生成英文路由名
  if (path) {
    const pathName = path.split('/').filter(Boolean).join('-')
    const routeName = pathName
      .replace(/[^a-zA-Z0-9_-]/g, '')
      .replace(/(?:^|[-_])(\w)/g, (_, c) => c ? c.toUpperCase() : '')
    if (routeName) return routeName
  }
  
  // 退路：使用菜单名称
  const safeName = name.replace(/[^a-zA-Z0-9_\u4e00-\u9fa5]/g, '')
  const routeName = safeName.replace(/(?:^|[-_])(\w)/g, (_, c) => c ? c.toUpperCase() : '')
  
  // 开发环境警告：路由名称包含中文
  if (import.meta.env.MODE === 'development' && /[\u4e00-\u9fa5]/.test(routeName)) {
    console.warn(`路由名称 "${routeName}" 包含中文字符，建议使用英文路径`)
  }
  
  return routeName
}

/** 查询菜单列表 */
function getList() {
  loading.value = true
  listMenu(queryParams.value).then(response => {
    menuList.value = proxy.handleTree(response.data, "menuId")
    loading.value = false
  }).catch(error => {
    loading.value = false
    handleApiError(error, '获取菜单列表失败')
  })
}

/** 查询菜单下拉树结构 */
function getTreeselect() {
  menuOptions.value = []
   const menu = { menuId: 0, menuName: "主类目", children: [] }
   menuOptions.value.push(menu)
   return listMenu().then(response => {
    menu.children = proxy.handleTree(response.data, "menuId")
      return true
  }).catch(error => {
    handleApiError(error, '获取菜单树结构失败')
      error.__menuTreeHandled = true
      return false
  })
}

/** 取消按钮 */
function cancel() {
  open.value = false
  reset()
}

/** 表单重置 */
function createDefaultForm() {
   return {
    menuId: undefined,
    parentId: 0,
    menuName: undefined,
    icon: undefined,
    menuType: "M",
    orderNum: undefined,
    isFrame: "1",
    isCache: "0",
    visible: "0",
    status: "0",
    redirect: "",
      routeName: "",
      path: "",
      component: "",
      query: "",
      perms: "",
    activeMenu: "",
    isAffix: false,
    isBreadcrumb: true,
    alwaysShow: true
  }
}

function normalizeMenuForm(detail = {}) {
   const defaults = createDefaultForm()
   return {
      ...defaults,
      ...detail,
      parentId: detail.parentId ?? defaults.parentId,
      orderNum: detail.orderNum ?? defaults.orderNum,
      menuType: detail.menuType || defaults.menuType,
      isFrame: detail.isFrame ?? defaults.isFrame,
      isCache: detail.isCache ?? defaults.isCache,
      visible: detail.visible ?? defaults.visible,
      status: detail.status ?? defaults.status,
      redirect: detail.redirect ?? defaults.redirect,
      routeName: detail.routeName ?? defaults.routeName,
      path: detail.path ?? defaults.path,
      component: detail.component ?? defaults.component,
      query: detail.query ?? defaults.query,
      perms: detail.perms ?? defaults.perms,
      activeMenu: detail.activeMenu ?? defaults.activeMenu,
      isAffix: typeof detail.isAffix === 'boolean' ? detail.isAffix : defaults.isAffix,
      isBreadcrumb: typeof detail.isBreadcrumb === 'boolean' ? detail.isBreadcrumb : defaults.isBreadcrumb,
      alwaysShow: typeof detail.alwaysShow === 'boolean' ? detail.alwaysShow : defaults.alwaysShow,
   }
}

/** 表单重置 */
function reset() {
   form.value = createDefaultForm()
  proxy.resetForm("menuRef")
}

/** 展示下拉图标 */
function showSelectIcon() {
  iconSelectRef.value.reset()
}

/** 选择图标 */
function selected(name) {
  form.value.icon = name
}

/** 搜索按钮操作 */
function handleQuery() {
  getList()
}

/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm("queryRef")
  handleQuery()
}

/** 新增按钮操作 */
async function handleAdd(row) {
  reset()
  await getTreeselect()
  form.value.parentId = row?.menuId || 0
  open.value = true
  title.value = "添加菜单"
}

/** 展开/折叠操作 */
function toggleExpandAll() {
  isExpandAll.value = !isExpandAll.value
  const tableEl = proxy.$refs['menuTable']
  if (!tableEl) return
  
  // 使用 Element Plus 公开 API 递归展开/折叠所有行
  const toggleRowExpansion = (rows) => {
    rows.forEach(row => {
      tableEl.toggleRowExpansion(row, isExpandAll.value)
      if (row.children && row.children.length > 0) {
        toggleRowExpansion(row.children)
      }
    })
  }
  
  toggleRowExpansion(menuList.value)
}

/** 修改按钮操作 */
async function handleUpdate(row) {
  reset()
   try {
      await getTreeselect()
      const response = await getMenu(row.menuId)
      form.value = normalizeMenuForm(response.data)
    open.value = true
    title.value = "修改菜单"
   } catch (error) {
      if (error && !error.__menuTreeHandled) {
         handleApiError(error, '获取菜单详情失败')
      }
   }
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs["menuRef"].validate(valid => {
    if (valid) {
      // 只为菜单类型生成路由名称
      if (form.value.menuType === 'C' && !form.value.routeName) {
        form.value.routeName = generateRouteName(form.value.menuName, form.value.path)
      }
      
      // 只处理非按钮类型的路径
      if (form.value.menuType !== 'F' && form.value.path) {
        // 父级菜单的路径必须以 '/' 开头
        if (form.value.parentId == 0 && !form.value.path.startsWith('/')) {
          form.value.path = '/' + form.value.path
        }
      }
      
      if (form.value.menuId != undefined) {
        updateMenu(form.value).then(response => {
          proxy.$modal.msgSuccess("修改成功")
          open.value = false
          getList()
        }).catch(error => {
          handleApiError(error, '修改菜单失败')
        })
      } else {
        addMenu(form.value).then(response => {
          proxy.$modal.msgSuccess("新增成功")
          open.value = false
          getList()
        }).catch(error => {
          handleApiError(error, '新增菜单失败')
        })
      }
    }
  })
}

/** 删除按钮操作 */
function handleDelete(row) {
  proxy.$modal.confirm('是否确认删除名称为"' + row.menuName + '"的数据项?').then(function() {
    return delMenu(row.menuId)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess("删除成功")
  }).catch(error => {
    if (error && error !== 'cancel') {
      handleApiError(error, '删除菜单失败')
    }
  })
}

getList()
</script>
