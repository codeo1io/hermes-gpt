// FleetPanel — regression net (rm-002). Pins the read-only fleet surface:
// authority/peers/served-profiles rendering, the unconfigured envelope, and
// the failure/retry path.
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { FleetPanel } from '../FleetPanel';
import { useFleetStore } from '../../stores/fleet';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

// api.get unwraps body.data once; the store keeps body.data.data as the
// mission envelope (available + inner data payload).
const fleetEnvelope = {
  ok: true,
  data: {
    surface: 'fleet',
    fetched_at: '2026-10-04T09:00:00Z',
    data: {
      available: true,
      data: {
        authority: 'configured',
        peers: [{ id: 'peer-1' }, { id: 'peer-2' }],
        served_profiles: ['default', 'ops'],
      },
    },
  },
};

function resetStore(): void {
  useFleetStore.setState({
    fleet: null,
    workflows: null,
    status: 'idle',
    error: null,
    fetchedAt: null,
  });
}

describe('FleetPanel (rm-002)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    resetStore();
  });

  it('renders authority, peers, and served profiles from the fleet envelope', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        if (String(input).includes('/api/ops/fleet')) return jsonResponse(fleetEnvelope);
        return jsonResponse({ ok: true, data: { workflows: [] } });
      }),
    );
    render(<FleetPanel />);

    expect(await screen.findByText('Authority')).toBeTruthy();
    expect(screen.getByText('configured')).toBeTruthy();
    expect(screen.getByText('Peers (2)')).toBeTruthy();
    expect(screen.getByText('Served profiles (2)')).toBeTruthy();
    expect(screen.getByText('ops')).toBeTruthy();
    // A2A secrets stay behind the read-only presentation note.
    expect(screen.getByText(/A2A URLs, tokens, and task payloads are never surfaced/)).toBeTruthy();

    const urls = vi
      .mocked(fetch)
      .mock.calls.map((c) => String((c as unknown as [RequestInfo])[0]));
    expect(urls.some((u) => u.includes('/api/ops/fleet'))).toBe(true);
    expect(urls.some((u) => u.includes('/api/ops/swarm'))).toBe(true);
  });

  it('renders the unconfigured authority state without peer sections erroring', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({
          ok: true,
          data: {
            surface: 'fleet',
            data: {
              available: false,
              unavailable_reason: 'no A2A authority configured',
              data: {},
            },
          },
        }),
      ),
    );
    render(<FleetPanel />);

    expect(await screen.findByText('no A2A authority configured')).toBeTruthy();
    expect(document.querySelector('.fd-unavailable')?.getAttribute('role')).toBe('status');
  });

  it('surfaces a failed fleet fetch with an inline retry', async () => {
    // Isolate the fleet query: the swarm fetch shares the store's single
    // status/error slot, so let it stay pending for this test (see the
    // shared-status finding recorded with this batch).
    let releaseSwarm!: () => void;
    const swarmGate = new Promise<void>((resolve) => {
      releaseSwarm = resolve;
    });
    let fleetCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).includes('/api/ops/fleet')) {
        fleetCalls += 1;
        if (fleetCalls === 1) {
          return jsonResponse(
            { ok: false, error: { code: 'OPERATOR_DISABLED', message: 'operator mode off' } },
            403,
          );
        }
        return jsonResponse(fleetEnvelope);
      }
      await swarmGate;
      return jsonResponse({ ok: true, data: { workflows: [] } });
    });
    try {
      vi.stubGlobal('fetch', fetchMock);
      render(<FleetPanel />);

      expect(await screen.findByText('operator mode off')).toBeTruthy();
      fireEvent.click(screen.getByRole('button', { name: /retry/i }));
      expect(await screen.findByText('Peers (2)')).toBeTruthy();
    } finally {
      releaseSwarm();
    }
  });
});
