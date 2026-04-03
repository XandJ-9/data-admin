import { defineConfig, loadEnv } from 'vite'
import path from 'path'
import createVitePlugins from './vite/plugins'

// https://vitejs.dev/config/
export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd())
    const { VITE_APP_BASE_URL, VITE_APP_BASE_API, VITE_APP_BASE_BACKEND_URL } = env
    const baseUrl = VITE_APP_BASE_BACKEND_URL || 'http://localhost:8000'

  return {
    // 部署生产环境和开发环境下的URL。
    // 默认情况下，vite 会假设你的应用是被部署在一个域名的根路径上
    // 例如 https://www.ruoyi.vip/。如果应用被部署在一个子路径上，你就需要用这个选项指定这个子路径。例如，如果你的应用被部署在 https://www.ruoyi.vip/admin/，则设置 baseUrl 为 /admin/。
    // base: VITE_APP_ENV === 'production' ? '/' : VITE_APP_BASE_URL,
    base: VITE_APP_BASE_URL,
    plugins: createVitePlugins(env, command === 'build'),
    resolve: {
      // https://cn.vitejs.dev/config/#resolve-alias
      alias: {
        // 设置路径
        '~': path.resolve(__dirname, './'),
        // 设置别名
        '@': path.resolve(__dirname, './src')
      },
      // https://cn.vitejs.dev/config/#resolve-extensions
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },
    // 打包配置
    build: {
      // https://vite.dev/config/build-options.html
      minify: 'terser',
      sourcemap: command === 'build' ? false : 'inline',
      outDir: 'dist',
      assetsDir: 'assets',
      chunkSizeWarningLimit: 2000,
      rollupOptions: {
        output: {
          chunkFileNames: 'static/js/[name]-[hash].js',
          entryFileNames: 'static/js/[name]-[hash].js',
          assetFileNames: 'static/[ext]/[name]-[hash].[ext]',
          manualChunks: {
            'xterm': [
              '@xterm/xterm',
              '@xterm/addon-fit',
              '@xterm/addon-search',
              '@xterm/addon-unicode11',
              '@xterm/addon-web-links',
              '@xterm/addon-webgl'
            ]
          }
        }
      }
    },
    // vite 相关配置
    server: {
      port: 80,
      // host: true，
      host: '0.0.0.0',
      open: true,
      proxy: {
          // WebSocket proxy for terminal
          '/ws': {
            target: baseUrl,
            changeOrigin: true,
            ws: true
          },
          // https://cn.vitejs.dev/config/#server-proxy
          [`${VITE_APP_BASE_API}/docs`]: {
            target: baseUrl,
            changeOrigin: true,
            rewrite: (p) => p.replace(`${VITE_APP_BASE_API}`, '/api')
          },
          [`${VITE_APP_BASE_API}/schema`]: {
            target: baseUrl,
            changeOrigin: true,
            rewrite: (p) => p.replace(`${VITE_APP_BASE_API}`, '/api')
          },
          '/api': {
            target: baseUrl,
            changeOrigin: true
          },
          [`${VITE_APP_BASE_API}`]: {
          target: baseUrl,
          changeOrigin: true,
              rewrite: (p) => p.replace(`${VITE_APP_BASE_API}`, '/data-api')
          },
         // springdoc proxy
        //  '^/v3/api-docs/(.*)': {
        //   target: baseUrl,
        //   changeOrigin: true,
        // }
      }
    },
    css: {
      postcss: {
        plugins: [
          {
            postcssPlugin: 'internal:charset-removal',
            AtRule: {
              charset: (atRule) => {
                if (atRule.name === 'charset') {
                  atRule.remove()
                }
              }
            }
          }
        ]
      }
    }
  }
})
