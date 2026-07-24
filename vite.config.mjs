import { defineConfig } from 'vite';
import { resolve } from 'node:path';

const frontendRoot = resolve('src/frontend');
const page = (name) => resolve(frontendRoot, name);

// Prefer 127.0.0.1 over localhost to avoid Node dual-stack AggregateError
// (IPv6 ::1 + IPv4) when the backend is briefly down during --reload.
const BACKEND = 'http://127.0.0.1:8080';
const BACKEND_WS = 'ws://127.0.0.1:8080';

function proxyErrorHandler(proxy) {
  proxy.on('error', (err, _req, res) => {
    const code = err && (err.code || err.errno) || 'ECONNREFUSED';
    // Keep one short line — full AggregateError stacks are noise during reload
    console.warn(`[vite] backend ${BACKEND} unreachable (${code}). Start: python src/backend/main.py --port 8080`);
    if (res && !res.headersSent && typeof res.writeHead === 'function') {
      res.writeHead(503, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({
        error: true,
        detail: '后端未启动或正在热重载 (127.0.0.1:8080)。请确认 python src/backend/main.py --port 8080 已运行。',
        status_code: 503,
        code,
      }));
    }
  });
}

export default defineConfig({
  root: 'src/frontend',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: BACKEND,
        changeOrigin: true,
        configure: proxyErrorHandler,
      },
      '/ws': {
        target: BACKEND_WS,
        ws: true,
        configure: proxyErrorHandler,
      },
    },
  },
  build: {
    outDir: '../../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        index: page('index.html'),
        login: page('login.html'),
        agentTeamConfig: page('agent-team-config.html'),
        tasks: page('tasks.html'),
        plaza: page('plaza.html'),
        skillExtract: page('skill-extract.html'),
        extractionPipeline: page('extraction-pipeline.html'),
        agentDigitalTwin: page('Agent-digital-twin.html'),
        digitalTwinCli: page('digital-twin-cli.html'),
        sandboxTwin: page('sandbox-twin.html'),
        datacenterRatchetEvolution: page('datacenter-ratchet-evolution.html'),
        costDashboard: page('cost-dashboard.html'),
        petConfig: page('pet-config.html'),
        agentMemory: page('agent-memory.html'),
      },
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/three')) return 'three-core';
        },
      },
    },
    chunkSizeWarningLimit: 600,
  },
});
