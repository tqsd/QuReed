import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [svelte()],
  build: {
    outDir: '../src/qureed/gui/static',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        assetFileNames: 'assets/qureed-gui.[ext]',
        chunkFileNames: 'assets/qureed-gui.js',
        entryFileNames: 'assets/qureed-gui.js'
      }
    }
  },
  server: {
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/specs': 'http://127.0.0.1:8000'
    }
  }
});
