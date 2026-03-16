import Layout from '@/layout'


const menuData = [
    // ==================== 系统管理 ====================
    {
        path: '/system',
        component: Layout,
        redirect: 'noRedirect',
        name: 'System',
        alwaysShow: true,
        meta: {
            title: '系统管理',
            icon: 'system'
        },
        children: [
            {
                path: 'user',
                component: () => import('@/views/system/user/index'),
                name: 'User',
                meta: {
                    title: '用户管理',
                    icon: 'user',
                    noCache: false
                },
                permissions: ['system:user:list']
            },
            {
                path: 'role',
                component: () => import('@/views/system/role/index'),
                name: 'Role',
                meta: {
                    title: '角色管理',
                    icon: 'peoples',
                    noCache: false
                },
                permissions: ['system:role:list']
            },
            {
                path: 'dept',
                component: () => import('@/views/system/dept/index'),
                name: 'Dept',
                meta: {
                    title: '部门管理',
                    icon: 'tree-table',
                    noCache: false
                },
                permissions: ['system:dept:list']
            },
            {
                path: 'menu',
                component: () => import('@/views/system/menu/index'),
                name: 'Menu',
                meta: {
                    title: '菜单管理',
                    icon: 'tree',
                    noCache: false
                },
                permissions: ['system:menu:list']
            },
            {
                path: 'dict',
                component: () => import('@/views/system/dict/index'),
                name: 'Dict',
                meta: {
                    title: '字典管理',
                    icon: 'dict',
                    noCache: false
                },
                permissions: ['system:dict:list']
            },
            {
                path: 'config',
                component: () => import('@/views/system/config/index'),
                name: 'Config',
                meta: {
                    title: '系统配置',
                    icon: 'edit',
                    noCache: false
                },
                permissions: ['system:config:list']
            }
        ]
    },

    // 系统管理 - 隐藏路由
    {
        path: '/system',
        component: Layout,
        hidden: true,
        children: [
            {
                path: 'user-auth/role/:userId(\\d+)',
                component: () => import('@/views/system/user/authRole'),
                name: 'AuthRole',
                meta: { title: '分配角色', activeMenu: '/system/user' },
                permissions: ['system:user:edit']
            },
            {
                path: 'role-auth/user/:roleId(\\d+)',
                component: () => import('@/views/system/role/authUser'),
                name: 'AuthUser',
                meta: { title: '分配用户', activeMenu: '/system/role' },
                permissions: ['system:role:edit']
            },
            {
                path: 'dict-data/index/:dictId(\\d+)',
                component: () => import('@/views/system/dict/data'),
                name: 'Data',
                meta: { title: '字典数据', activeMenu: '/system/dict' },
                permissions: ['system:dict:list']
            }
        ]
    },

    // ==================== 数据资产 ====================
    {
        path: '/data-asset',
        component: Layout,
        redirect: 'noRedirect',
        name: 'DataAsset',
        alwaysShow: true,
        meta: {
            title: '数据资产',
            icon: 'data-asset'
        },
        children: [
            {
                path: 'asset',
                component: () => import('@/views/data/asset/index'),
                name: 'AssetOverview',
                meta: {
                    title: '资产概览',
                    icon: 'dashboard',
                    noCache: false
                },
                permissions: ['system:user:list']
            },
            {
                path: 'datasource',
                component: () => import('@/views/data/asset/datasource/index'),
                name: 'DataSource',
                meta: {
                    title: '数据源管理',
                    icon: 'datasource',
                    noCache: false
                },
                permissions: ['system:datasource:query']
            },
            {
                path: 'metadata',
                component: () => import('@/views/data/asset/metadata/index'),
                name: 'Metadata',
                meta: {
                    title: '元数据管理',
                    icon: 'list',
                    noCache: false
                },
                permissions: ['system:datasource:list']
            },
            {
                path: 'lineage',
                component: () => import('@/views/data/asset/lineage/index'),
                name: 'DataLineage',
                meta: {
                    title: '数据血缘',
                    icon: 'tree-table',
                    noCache: false
                },
                permissions: ['system:datasource:list']
            }
        ]
    },

    // 数据资产 - 隐藏路由
    {
        path: '/data-asset',
        component: Layout,
        hidden: true,
        children: [
            {
                path: 'datasource/detail/:id(\\d+)',
                component: () => import('@/views/data/asset/datasource/detail'),
                name: 'DataSourceDetail',
                meta: { title: '数据源详情', activeMenu: '/data-asset/datasource', noCache: false },
                permissions: ['system:datasource:query']
            },
            {
                path: 'datasource/view/:id(\\d+)',
                component: () => import('@/views/data/asset/datasource/view'),
                name: 'DataSourceView',
                meta: { title: '源数据查看', activeMenu: '/data-asset/datasource', noCache: false },
                permissions: ['system:datasource:view']
            }
        ]
    },

    // ==================== 数据ETL ====================
    {
        path: '/data-etl',
        component: Layout,
        redirect: '/data-etl/home',
        name: 'DataETL',
        alwaysShow: true,
        meta: {
            title: '数据ETL',
            icon: 'data-integration'
        },
        children: [
            {
                path: 'home',
                component: () => import('@/views/data/etl/index'),
                name: 'ETLHome',
                meta: {
                    title: 'ETL首页',
                    icon: 'dashboard',
                    noCache: false
                },
                permissions: ['dataetl:task:query']
            },
            {
                path: 'tasks',
                component: () => import('@/views/data/etl/taskList'),
                name: 'ETLTaskList',
                meta: {
                    title: 'ETL任务',
                    icon: 'list',
                    noCache: false
                },
                permissions: ['dataetl:task:query']
            },
            {
                path: 'execution-logs',
                component: () => import('@/views/data/etl/executionLogs'),
                name: 'ETLExecutionLogs',
                meta: {
                    title: '执行日志',
                    icon: 'log',
                    noCache: false
                },
                permissions: ['dataetl:executionlog:query']
            }
        ]
    },

    // 数据ETL - 隐藏路由
    {
        path: '/data-etl',
        component: Layout,
        hidden: true,
        children: [
            {
                path: 'task/:id',
                component: () => import('@/views/data/etl/taskDetail'),
                name: 'ETLTaskDetail',
                meta: { title: 'ETL任务详情', activeMenu: '/data-etl/tasks', noCache: false },
                permissions: ['dataetl:task:query']
            }
        ]
    },

    // ==================== 数据服务 ====================
    {
        path: '/data-service',
        component: Layout,
        redirect: 'noRedirect',
        name: 'DataService',
        alwaysShow: true,
        meta: {
            title: '数据服务',
            icon: 'server'
        },
        children: [
            {
                path: 'query',
                component: () => import('@/views/data/service/query/index'),
                name: 'DataServiceQuery',
                meta: {
                    title: 'SQL查询',
                    icon: 'code',
                    noCache: false
                },
                permissions: ['dataservice:sql:query']
            },
            {
                path: 'interface',
                component: () => import('@/views/data/service/interface/index'),
                name: 'DataServiceInterface',
                meta: {
                    title: '接口管理',
                    icon: 'guide',
                    noCache: false
                },
                permissions: ['dataservice:interface:query']
            },
            {
                path: 'query-log',
                component: () => import('@/views/data/service/query/queryLog'),
                name: 'DataServiceQueryLog',
                meta: {
                    title: '查询日志',
                    icon: 'log',
                    noCache: false
                },
                permissions: ['dataservice:querylog:query']
            }
        ]
    },

    // 数据服务 - 隐藏路由
    {
        path: '/data-service',
        component: Layout,
        hidden: true,
        children: [
            {
                path: 'interface/detail/:interfaceId(\\d+)',
                component: () => import('@/views/data/service/interface/detail'),
                name: 'InterfaceDetail',
                meta: { title: '接口详情', activeMenu: '/data-service/interface', noCache: false },
                permissions: ['dataservice:interface:view']
            }
        ]
    }
]

export default menuData