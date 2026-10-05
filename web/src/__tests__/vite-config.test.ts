// vite.config.ts — smoke net (rm-002). Pins the build/serve contract the SPA
// depends on: the /ui base path (the Starlette mount), the dev-server /api
// proxy, and the vitest jsdom environment + setup file.
import { describe, expect, it } from 'vitest';

// eslint-disable-next-line import/no-relative-packages
import config from '../../vite.config';

describe('vite.config (rm-002)', () => {
  it('serves the SPA under the /ui base path', () => {
    expect(config.base).toBe('/ui/');
  });

  it('proxies /api to the local hermes-gpt server in dev', () => {
    const proxy = (config.server as { proxy?: Record<string, { target?: string }> }).proxy;
    expect(proxy?.['/api']).toBeTruthy();
    expect(proxy?.['/api'].target).toBe('http://127.0.0.1:7677');
  });

  it('builds into web/dist for the Starlette /ui mount', () => {
    expect((config.build as { outDir?: string }).outDir).toBe('dist');
  });

  it('configures vitest with jsdom and the shared setup file', () => {
    const test = config.test as { environment?: string; setupFiles?: string[]; globals?: boolean };
    expect(test.environment).toBe('jsdom');
    expect(test.globals).toBe(true);
    expect(test.setupFiles).toContain('./src/test/setup.ts');
  });
});
