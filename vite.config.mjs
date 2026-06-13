import { defineConfig } from 'vite';
import { resolve } from 'node:path';

const frontendRoot = resolve('src/frontend');
const page = (name) => resolve(frontendRoot, name);

export default defineConfig({
  root: 'src/frontend',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8080',
        ws: true,
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
        systemEvolution: page('system-evolution.html'),
        skillExtract: page('skill-extract.html'),
        extractionPipeline: page('extraction-pipeline.html'),
        agentDigitalTwin: page('Agent-digital-twin.html'),
        digitalTwinCli: page('digital-twin-cli.html'),
        sandboxTwin: page('sandbox-twin.html'),
        datacenterRatchetEvolution: page('datacenter-ratchet-evolution.html'),
        costDashboard: page('cost-dashboard.html'),
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
