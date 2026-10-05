// EventHistoryPanel — regression net (rm-002). Pins the normalized timeline
// rendering (source tag, kind, summary, actor/subject) and the filterbar
// round-trip: changing a filter re-queries with the corresponding query
// parameter.
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { EventHistoryPanel } from '../EventHistoryPanel';
import { useEventHistoryStore } from '../../stores/eventHistory';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const eventsEnvelope = {
  ok: true,
  data: {
    events: [
      {
        event_id: 'e-1',
        source: 'audit',
        kind: 'cron.create',
        ts: '2026-10-04T09:00:00Z',
        summary: 'cron job created',
        actor: 'operator',
        subject_id: 'job-42',
        status_after: 'pending',
      },
      {
        event_id: 'e-2',
        source: 'swarm',
        kind: 'workflow.finish',
        ts: '2026-10-04T09:05:00Z',
        summary: 'workflow finished',
      },
    ],
    retention_max_age_days: 30,
    warnings: ['1 event outside retention window'],
  },
};

function resetStore(): void {
  useEventHistoryStore.setState({
    events: [],
    envelope: null,
    status: 'idle',
    error: null,
    filters: { source: '', subject_id: '', kind: '', limit: 50 },
  });
}

describe('EventHistoryPanel (rm-002)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    resetStore();
  });

  it('renders timeline events with source, kind, summary, and meta', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(eventsEnvelope)));
    render(<EventHistoryPanel />);

    expect(await screen.findByText('cron.create')).toBeTruthy();
    expect(screen.getByText('workflow.finish')).toBeTruthy();
    expect(screen.getByText('cron job created')).toBeTruthy();
    expect(screen.getByText('workflow finished')).toBeTruthy();
    expect(document.querySelector('.fd-event[data-source="audit"]')).toBeTruthy();
    expect(document.querySelector('.fd-event[data-source="swarm"]')).toBeTruthy();
    expect(screen.getByText('job-42')).toBeTruthy();
    // Retention banner + warnings.
    expect(screen.getByText(/retention 30d/)).toBeTruthy();
    expect(screen.getByText(/1 event outside retention window/)).toBeTruthy();
  });

  it('re-queries with the source filter when the operator changes it', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(eventsEnvelope));
    vi.stubGlobal('fetch', fetchMock);
    render(<EventHistoryPanel />);
    await screen.findByText('cron.create');

    fireEvent.change(screen.getByLabelText('Source filter'), { target: { value: 'audit' } });
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));

    const secondUrl = String((fetchMock.mock.calls[1] as unknown as [RequestInfo])[0]);
    expect(secondUrl).toContain('/api/events?');
    expect(secondUrl).toContain('source=audit');
    expect(secondUrl).toContain('limit=50');
  });

  it('shows the empty state for an empty timeline and the error state with retry', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({ ok: true, data: { events: [], retention_max_age_days: 30 } }),
      )
      .mockResolvedValueOnce(
        jsonResponse({ ok: false, error: { code: 'EVENTS_DISABLED', message: 'events off' } }, 403),
      )
      .mockResolvedValueOnce(
        jsonResponse({ ok: true, data: { events: [], retention_max_age_days: 30 } }),
      );
    vi.stubGlobal('fetch', fetchMock);
    render(<EventHistoryPanel />);

    expect(await screen.findByText('No events match')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    expect(await screen.findByText('events off')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(await screen.findByText('No events match')).toBeTruthy();
  });

  it('refreshes on demand via the header control', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(eventsEnvelope));
    vi.stubGlobal('fetch', fetchMock);
    render(<EventHistoryPanel />);
    await screen.findByText('cron.create');

    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });
});
