import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/services': path.resolve(__dirname, './src/services'),
      '@/types': path.resolve(__dirname, './src/types'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/store': path.resolve(__dirname, './src/store'),
    },
  },
  server: {
    port: 3000,
    host: true, // Allow external connections for development
    hmr: {
      overlay: false, // Disable error overlay
    },
    // Proxy configuration - only for development
    proxy: process.env.NODE_ENV === 'development' ? {
      '/api': {
        target: 'https://api.genscenestudio.com',
        changeOrigin: true,
        secure: true,
        // Forward the API key header if present
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
        },
        // Handle preflight requests
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // Add API key header if not present
            if (!proxyReq.getHeader('X-API-Key')) {
              proxyReq.setHeader('X-API-Key', 'genscene_api_key_prod_2025_secure');
            }
            // Log proxy requests in debug mode
            if (process.env.NODE_ENV === 'development') {
              console.log(`Proxying ${req.method} ${req.url} to ${options.target}`);
            }
          });
        },
      },
    } : {},
    // CORS configuration for direct API calls
    cors: {
      origin: ['http://localhost:3000', 'http://127.0.0.1:3000'],
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key'],
      credentials: true,
    },
  },
  // Environment variables validation
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
  // Build optimizations
  build: {
    sourcemap: process.env.VITE_DEBUG === 'true',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          utils: ['axios', 'date-fns', 'clsx'],
          ui: ['framer-motion', 'lucide-react', 'sonner'],
        },
      },
    },
  },
})