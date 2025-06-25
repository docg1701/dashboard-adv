/// <reference types="vitest" />
import { defineConfig } from 'vite' // Keep this for Vite's own config
import react from '@vitejs/plugin-react'
// import { visualizer } from 'rollup-plugin-visualizer'; // Import

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // visualizer({ // Add visualizer plugin
    //   filename: 'dist/stats.html', // Output file
    //   open: false, // Set to false, as it cannot open browser here
    //   gzipSize: true,
    //   brotliSize: true,
    // }),
  ],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts',
    css: false, // Disable CSS processing for tests
    testTimeout: 30000, // Increase timeout to 30 seconds
    include: ['src/modules/**/*.{test,spec}.?(c|m)[jt]s?(x)', 'src/components/**/*.{test,spec}.?(c|m)[jt]s?(x)'],
    tsconfig: './tsconfig.spec.json',
  },
  server: {
    proxy: {
      // Redireciona qualquer requisição que comece com /api
      '/api': {
        // O alvo é o seu backend rodando no Docker na porta 8000
        target: 'http://localhost:8000',
        // Necessário para o proxy funcionar corretamente
        changeOrigin: true,
      },
    },
  },
})