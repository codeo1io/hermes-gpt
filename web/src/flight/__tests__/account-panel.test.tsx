// AccountPanel — regression net (rm-002). Pins the read-only operator policy
// + OAuth token-store cards against the /api/ops/account envelope, the
// failure/retry path, and that token material is never rendered.
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AccountPanel } from '../AccountPanel';
import { useAccountStore } from '../../stores/account';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const accountEnvelope = {
  ok: true,
  data: {
    policy: {
      level: 'workspace',
      enabled: true,
      apply_mode: 'dry-run',
      owner_mode_ready: false,
      mutation_allowed: false,
      available_capability_groups: ['core', 'operator'],
    },
    oauth: { presence: 'present', expires_at: '2026-11-01T00:00:00Z', client_count: 2 },
    server_version: '0.13.0',
  },
};

function resetStore(): void {
  useAccountStore.setState({
    account: null,
    loading: false,
    error: null,
    fetchedAt: null,
  });
}

describe('AccountPanel (rm-002)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    resetStore();
  });

  it('renders operator policy and token-store status from the account envelope', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(accountEnvelope)));
    render(<AccountPanel />);

    expect(await screen.findByText('Operator policy')).toBeTruthy();
    expect(screen.getByText('workspace')).toBeTruthy();
    expect(screen.getByText('apply mode')).toBeTruthy();
    expect(screen.getByText('dry-run')).toBeTruthy();
    expect(screen.getByText('OAuth token store')).toBeTruthy();
    expect(screen.getByText('present')).toBeTruthy();
    expect(screen.getByText('2026-11-01T00:00:00Z')).toBeTruthy();
    expect(screen.getByText('Server version 0.13.0')).toBeTruthy();

    const call = vi.mocked(fetch).mock.calls[0] as unknown as [RequestInfo];
    expect(String(call[0])).toContain('/api/ops/account');
  });

  it('refreshes on demand via the header Refresh control', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(accountEnvelope));
    vi.stubGlobal('fetch', fetchMock);
    render(<AccountPanel />);
    await screen.findByText('Operator policy');

    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });

  it('surfaces a failed account fetch with an inline retry', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ ok: false, error: { code: 'OPERATOR_DISABLED', message: 'operator mode off' } }, 403))
      .mockResolvedValueOnce(jsonResponse(accountEnvelope));
    vi.stubGlobal('fetch', fetchMock);
    render(<AccountPanel />);

    expect(await screen.findByText('operator mode off')).toBeTruthy();
    expect(screen.queryByText('Operator policy')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(await screen.findByText('Operator policy')).toBeTruthy();
  });

  it('renders the no-token-store empty state and never token material', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({
          ok: true,
          data: {
            policy: { level: 'read_only', enabled: true, apply_mode: 'off', owner_mode_ready: false, mutation_allowed: false, available_capability_groups: null },
            oauth: null,
            server_version: '0.13.0',
          },
        }),
      ),
    );
    render(<AccountPanel />);

    expect(await screen.findByText('No token store')).toBeTruthy();
    // The card copy itself promises token material is never shown.
    expect(screen.getByText(/Token material is never shown/)).toBeTruthy();
  });
});
