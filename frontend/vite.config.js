import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@locales': path.resolve(__dirname, '../locales')
    }
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      }
    }
  },
  // 生产构建预览服务器（`vite preview` / `npm run start:frontend`）
  preview: {
    host: true,
    port: 3000,
    // 允许任意 Host 头，便于在容器/反向代理后访问；
    // 如需收紧可改为具体域名数组，或通过环境变量配置
    allowedHosts: true
  }
})
