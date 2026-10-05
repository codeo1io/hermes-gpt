// ApprovalsPanel — regression net (rm-002). Pins the pending-approval
// read-model rendering (raw prompts never shown) and the server-gated
// confirm-dialog flow: a 409 CONFIRM_REQUIRED opens the dialog, and the
// dialog's Confirm re-POSTs with the tool's own confirm argument — the
// adapter/operator gate is never weakened client-side.
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ApprovalsPanel } from '../ApprovalsPanel';
import { useApprovalStore } from '../../stores/approval';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

// api.get unwraps body.data once; the store reads body.data.data.data
// (surface envelope -> mission envelope -> payload).
const approvalsEnvelope = {
  ok: true,
  data: {
    surface: 'approvals',
    data: {
      success: true,
      data: {
        approvals: [
          { kind: 'hermes_cron_create', source: 'mission', id: 'appr-1', status: 'review', prompt_sha256: 'a'.repeat(64) },
          { kind: 'hermes_profile_switch', source: 'mission', id: 'appr-2', status: 'review' },
        ],
      },
    },
  },
};

const emptyApprovals = {
  ok: true,
  data: { surface: 'approvals', data: { success: true, data: { approvals: [] } } },
};

function resetStore(): void {
  useApprovalStore.setState({
    items: [],
    source: 'mission',
    status: 'idle',
    error: null,
    fetchedAt: null,
    dialog: null,
  });
}

describe('ApprovalsPanel (rm-002)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    resetStore();
  });

  it('renders pending approvals as read-only cards (ids and shas, never raw prompts)', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(approvalsEnvelope)));
    render(<ApprovalsPanel />);

    expect(await screen.findByText('hermes_cron_create')).toBeTruthy();
    expect(screen.getByText(/id appr-1/)).toBeTruthy();
    expect(screen.getByText(new RegExp(`sha ${'a'.repeat(16)}…\\[truncated\\]`))).toBeTruthy();
    expect(screen.getByText('hermes_profile_switch')).toBeTruthy();
    expect(screen.getByText(/Raw prompts are never shown/)).toBeTruthy();
  });

  it('shows the empty state when nothing is pending, then refreshes on demand', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(emptyApprovals))
      .mockResolvedValueOnce(jsonResponse(approvalsEnvelope));
    vi.stubGlobal('fetch', fetchMock);
    render(<ApprovalsPanel />);

    expect(await screen.findByText('No pending approvals')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    expect(await screen.findByText(/id appr-1/)).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('surfaces a failed approvals query with an inline retry', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ ok: false, error: { code: 'OPERATOR_DISABLED', message: 'operator mode off' } }, 403))
      .mockResolvedValueOnce(jsonResponse(emptyApprovals));
    vi.stubGlobal('fetch', fetchMock);
    render(<ApprovalsPanel />);

    expect(await screen.findByText('operator mode off')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(await screen.findByText('No pending approvals')).toBeTruthy();
  });

  it('opens the confirm dialog on the server 409 gate and re-arms Confirm with the gate argument', async () => {
    const plan = { changes: { job: 'nightly' }, confirm_required: true };
    const actionCalls: Array<Record<string, unknown>> = [];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null;
      if (String(input).includes('/api/ops/action') && body) {
        actionCalls.push(body);
        const args = body.args as Record<string, unknown>;
        if (args.confirm === true) {
          return jsonResponse({
            ok: true,
            data: { tool: 'hermes_cron_create', dry_run: false, requires_confirm: false, result: { created: 'job-42' } },
          });
        }
        return jsonResponse(
          { ok: false, error: { code: 'CONFIRM_REQUIRED', message: 'confirmation required', details: plan } },
          409,
        );
      }
      return jsonResponse(emptyApprovals);
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<ApprovalsPanel />);

    // Trigger the gate through the store the same way an action surface does.
    await useApprovalStore.getState().runGated('hermes_cron_create', { name: 'nightly' }, false);

    const dialog = await screen.findByRole('dialog');
    expect(dialog.getAttribute('aria-label')).toBe('Confirm hermes_cron_create');
    expect(screen.getByText(/server gate is never bypassed/)).toBeTruthy();
    expect(screen.getByText(/"confirm_required": true/)).toBeTruthy();

    // The dialog Confirm re-POSTs with the tool's own confirm argument.
    fireEvent.click(screen.getByRole('button', { name: /^Confirm$/ }));
    await waitFor(() => expect(actionCalls.length).toBe(2));
    expect(actionCalls[0]).toEqual(
      expect.objectContaining({ tool: 'hermes_cron_create', args: { name: 'nightly' }, dry_run: false }),
    );
    expect(actionCalls[1]).toEqual(
      expect.objectContaining({
        tool: 'hermes_cron_create',
        args: expect.objectContaining({ name: 'nightly', confirm: true }),
        dry_run: false,
      }),
    );
  });
});
