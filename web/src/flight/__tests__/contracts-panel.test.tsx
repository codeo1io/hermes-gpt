// ContractsPanel + ContractDetail — regression net (rm-002). Pins the
// contract-evidence read-model: review-acceptance cards with verdict chips
// and detail links, workflow references, the empty envelope, and the
// NOT_FOUND detail state.
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ContractDetail, ContractsPanel } from '../ContractsPanel';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const sha = 'b'.repeat(64);
const contractsEnvelope = {
  ok: true,
  data: {
    success: true,
    count: 1,
    review_acceptances: [
      {
        record_id: 'rec-1',
        contract_sha256: sha,
        task_id: 'task-7',
        assignee: 'codex',
        reviewer: 'operator',
        verdict: 'SATISFIED',
        evidence_refs: ['/tmp/probe.py'],
      },
    ],
    workflows: [{ workflow_id: 'wf-1', title: 'nightly sweep', status: 'done' }],
  },
};

function renderContractsAt(path: string): ReturnType<typeof render> {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/ops/contracts" element={<ContractsPanel />} />
        <Route path="/ops/contracts/:contractSha256" element={<ContractDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ContractsPanel (rm-002)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('renders review acceptances with verdict chips and workflow references', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(contractsEnvelope)));
    renderContractsAt('/ops/contracts');

    expect(await screen.findByText('Review acceptances (1)')).toBeTruthy();
    expect(screen.getByText('SATISFIED')).toBeTruthy();
    expect(screen.getByText(new RegExp(`${sha.slice(0, 24)}…\\[truncated\\]`))).toBeTruthy();
    expect(screen.getByText('task-7 · reviewer operator')).toBeTruthy();
    expect(screen.getByText('Workflow references (1)')).toBeTruthy();
    expect(screen.getByText('nightly sweep')).toBeTruthy();
    expect(screen.getByText('done')).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Detail' })).toBeTruthy();

    const call = vi.mocked(fetch).mock.calls[0] as unknown as [RequestInfo];
    expect(String(call[0])).toContain('/api/ops/contracts');
  });

  it('renders both empty states for an empty evidence envelope', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({ ok: true, data: { success: true, count: 0, review_acceptances: [], workflows: [] } }),
      ),
    );
    renderContractsAt('/ops/contracts');

    expect(await screen.findByText('No review acceptances yet')).toBeTruthy();
    expect(screen.getByText('No workflow references')).toBeTruthy();
  });

  it('surfaces a failed contracts read with the gate code inline', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({ ok: false, error: { code: 'OPERATOR_DISABLED', message: 'operator mode off' } }, 403),
      ),
    );
    renderContractsAt('/ops/contracts');

    expect(await screen.findByText(/OPERATOR_DISABLED: operator mode off/)).toBeTruthy();
  });

  it('detail: renders acceptance records for a known contract sha', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({ ok: true, data: { success: true, contract_sha256: sha, records: contractsEnvelope.data.review_acceptances } }),
      ),
    );
    renderContractsAt(`/ops/contracts/${sha}`);

    expect(await screen.findByText('Review acceptance')).toBeTruthy();
    expect(screen.getByText('SATISFIED')).toBeTruthy();
    expect(screen.getByText('rec-1')).toBeTruthy();
    expect(screen.getByText(/task task-7 · assignee codex · reviewer operator/)).toBeTruthy();
    expect(screen.getByText('/tmp/probe.py')).toBeTruthy();
    expect(screen.getByRole('link', { name: '← All contracts' })).toBeTruthy();
  });

  it('detail: shows the no-evidence state for an unknown contract sha', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({ ok: false, error: { code: 'NOT_FOUND', message: 'no acceptance records' } }, 404),
      ),
    );
    renderContractsAt(`/ops/contracts/${'c'.repeat(64)}`);

    expect(await screen.findByText('No evidence found for this contract')).toBeTruthy();
  });
});
