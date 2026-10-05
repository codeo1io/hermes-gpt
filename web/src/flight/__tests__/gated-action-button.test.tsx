// GatedActionButton — staged-action truth tests (rm-159).
//
// Pins the post-apply contract: a completed real apply settles in a distinct
// `applied` state that shows the executed result and never dry-run labeling,
// and a second apply requires an explicit re-arm (Reset). Also pins the
// dead-`confirm`-stage removal: the confirm control lives in the dry-run
// panel only, and `data-gate-step` only ever reports idle/busy/dryrun/applied.
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { GatedActionButton } from '../GatedActionButton';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const dryRunBody = {
  ok: true,
  data: { tool: 'hermes_cron_create', dry_run: true, requires_confirm: true, result: { plan: { job: 'nightly' } } },
};
const appliedBody = {
  ok: true,
  data: { tool: 'hermes_cron_create', dry_run: false, requires_confirm: false, result: { created: 'job-42' } },
};

async function applyFully(): Promise<void> {
  fireEvent.click(screen.getByRole('button', { name: /restart nightly/i }));
  expect(await screen.findByText('DRY-RUN · NO-OP')).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: /confirm restart nightly/i }));
  expect(await screen.findByText('APPLIED')).toBeTruthy();
}

describe('GatedActionButton staged-action truth (rm-159)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('settles a real apply into an APPLIED state that never shows dry-run labeling', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValueOnce(jsonResponse(dryRunBody)).mockResolvedValueOnce(jsonResponse(appliedBody)),
    );
    render(<GatedActionButton tool="hermes_cron_create" args={{ name: 'nightly' }} label="Restart nightly" />);

    await applyFully();

    // The executed result is shown, the dry-run chip is gone, and the gate
    // step attribute reports the post-apply state.
    expect(document.querySelector('[data-gate-step]')?.getAttribute('data-gate-step')).toBe('applied');
    expect(screen.queryByText('DRY-RUN · NO-OP')).toBeNull();
    expect(screen.getByText(/"created": "job-42"/)).toBeTruthy();
    expect(document.querySelector('[data-gate-result]')).toBeTruthy();
  });

  it('requires an explicit re-arm: no Confirm control in the APPLIED state', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValueOnce(jsonResponse(dryRunBody)).mockResolvedValueOnce(jsonResponse(appliedBody)),
    );
    render(<GatedActionButton tool="hermes_cron_create" args={{ name: 'nightly' }} label="Restart nightly" />);

    await applyFully();
    expect(screen.queryByRole('button', { name: /confirm/i })).toBeNull();

    // Re-arm only via Reset, which returns to the idle label button.
    fireEvent.click(screen.getByRole('button', { name: 'Reset' }));
    expect(screen.getByRole('button', { name: /restart nightly/i })).toBeTruthy();
    expect(screen.queryByText('APPLIED')).toBeNull();
  });

  it('keeps a failed apply on the truthful dry-run plan — nothing executed, retry stays available', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(jsonResponse(dryRunBody))
        .mockResolvedValueOnce(
          jsonResponse({ ok: false, error: { code: 'CRON_CREATE_ERROR', message: 'boom' } }, 500),
        ),
    );
    render(<GatedActionButton tool="hermes_cron_create" args={{ name: 'nightly' }} label="Restart nightly" />);

    fireEvent.click(screen.getByRole('button', { name: /restart nightly/i }));
    expect(await screen.findByText('DRY-RUN · NO-OP')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /confirm restart nightly/i }));

    // The gate surfaces the error inline; the displayed plan is still the
    // dry-run plan and the Confirm retry control is intact.
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(/CRON_CREATE_ERROR: boom/)).toBeTruthy();
    expect(screen.getByText('DRY-RUN · NO-OP')).toBeTruthy();
    expect(screen.getByRole('button', { name: /confirm restart nightly/i })).toBeTruthy();
    expect(document.querySelector('[data-gate-step]')?.getAttribute('data-gate-step')).toBe('dryrun');
  });

  it('exposes only the live gate stages idle/busy/dryrun/applied (dead confirm stage removed)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(dryRunBody)));
    render(<GatedActionButton tool="hermes_cron_create" args={{ name: 'nightly' }} label="Restart nightly" />);

    expect(document.querySelector('[data-gate-step]')?.getAttribute('data-gate-step')).toBe('idle');
    fireEvent.click(screen.getByRole('button', { name: /restart nightly/i }));
    expect(await screen.findByText('DRY-RUN · NO-OP')).toBeTruthy();
    expect(document.querySelector('[data-gate-step]')?.getAttribute('data-gate-step')).toBe('dryrun');
  });
});
