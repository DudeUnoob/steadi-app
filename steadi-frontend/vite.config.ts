import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react({
      // Optimize JSX runtime
      jsxRuntime: 'automatic',
    }), 
    tailwindcss()
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@tabler/icons-react': '@tabler/icons-react/dist/esm/icons/index.mjs'
    },
  },

  // Development server optimizations
  server: {
    port: 5173,
    host: true,
    // Enable HMR
    hmr: {
      overlay: true,
    },
    // Optimize dependency pre-bundling
    fs: {
      strict: false,
    },
  },

  // Build optimizations
  build: {
    // Enable source maps for debugging
    sourcemap: true,
    // Optimize chunk splitting
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks for better caching
          vendor: ['react', 'react-dom'],
          ui: ['@radix-ui/react-tabs', '@radix-ui/react-select', '@radix-ui/react-label'],
          charts: ['recharts'],
          utils: ['clsx', 'tailwind-merge', 'date-fns'],
          icons: ['lucide-react', '@tabler/icons-react'],
          state: ['zustand'],
          auth: ['@supabase/supabase-js'],
        },
      },
    },
    // Increase chunk size warning limit
    chunkSizeWarningLimit: 1000,
    // Enable minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true,
      },
    },
  },

  // Dependency optimization
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'zustand',
      '@supabase/supabase-js',
      'lucide-react',
      'recharts',
      'date-fns',
      'clsx',
      'tailwind-merge',
    ],
    // Force pre-bundling of these dependencies
    force: true,
  },

  // Enable esbuild for faster builds
  esbuild: {
    target: 'es2020',
    // Remove console.log in production
    drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : [],
  },

  // Preview server configuration
  preview: {
    port: 4173,
    host: true,
  },
})
