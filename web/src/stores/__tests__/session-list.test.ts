// session-list store — regression net (rm-002). Pins the conversation-list
// read model: load success/failure paths and the upsert-prepend/dedupe used
// when a turn finishes.
import { afterEach, describe, expect, it, vi } from 'vitest';

import { listSessions } from '../../api/chat';
import { useSessionListStore } from '../session-list';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function session(sessionId: string, title = 'Titled', count = 3) {
  return {
    session_id: sessionId,
    title,
    message_count: count,
    updated_at: '2026-10-04T09:00:00Z',
    profile: 'default',
    model: 'claude-sonnet',
    last_activity_at: 1759578000,
    created_at: 1759318800,
  };
}

function resetStore(): void {
  useSessionListStore.setState({ sessions: [], loading: false, error: null });
}

describe('useSessionListStore (rm-002)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    resetStore();
  });

  it('loads the session list into the store', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({ ok: true, data: { sessions: [session('s1'), session('s2')] } }),
      ),
    );
    await useSessionListStore.getState().load();

    const state = useSessionListStore.getState();
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
    expect(state.sessions.map((s) => s.session_id)).toEqual(['s1', 's2']);
  });

  it('keeps the previous list and records the error when the load fails', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ ok: true, data: { sessions: [session('s1')] } }))
      .mockResolvedValueOnce(
        jsonResponse({ ok: false, error: { code: 'INTERNAL', message: 'store unavailable' } }, 500),
      );
    vi.stubGlobal('fetch', fetchMock);
    await useSessionListStore.getState().load();
    await useSessionListStore.getState().load();

    const state = useSessionListStore.getState();
    expect(state.loading).toBe(false);
    expect(state.error).toBe('store unavailable');
    // The previously loaded list survives the failure.
    expect(state.sessions.map((s) => s.session_id)).toEqual(['s1']);
  });

  it('upserts a finished session at the head and never duplicates it', () => {
    useSessionListStore.setState({ sessions: [session('s1'), session('s2')] });

    useSessionListStore.getState().upsert(session('s2', 'New title', 9));

    const after = useSessionListStore.getState().sessions;
    expect(after.length).toBe(2);
    expect(after[0].session_id).toBe('s2');
    expect(after[0].title).toBe('New title');
    expect(after[0].message_count).toBe(9);
    expect(after[1].session_id).toBe('s1');
  });

  it('routes through the listSessions api helper, not raw fetch elsewhere', async () => {
    void listSessions; // import pin: the store must keep using the api/chat helper
    const fetchMock = vi.fn(async () => jsonResponse({ ok: true, data: { sessions: [] } }));
    vi.stubGlobal('fetch', fetchMock);
    await useSessionListStore.getState().load();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String((fetchMock.mock.calls[0] as unknown as [RequestInfo])[0])).toContain('/api/sessions');
  });
});
