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
        plazaDark: page('plaza-dark.html'),
        plazaOld: page('plaza-old.html'),
        plazaWabisabi: page('plaza-wabisabi.html'),
        plazaWabisabiV2: page('plaza-wabisabi-v2.html'),
        systemEvolution: page('system-evolution.html'),
        skillExtract: page('skill-extract.html'),
        extractionPipeline: page('extraction-pipeline.html'),
        digitalTwinCli: page('digital-twin-cli.html'),
        sandboxTwin: page('sandbox-twin.html'),
        datacenterRatchetEvolution: page('datacenter-ratchet-evolution.html'),
        demoFieldioParticles: page('demo-fieldio-particles.html'),
        demoLupiDataHumanism: page('demo-lupi-data-humanism.html'),
        demoTakramBiosynthetic: page('demo-takram-biosynthetic.html'),
      },
    },
  },
});
