// ChatPage — hydration race tests (rm-160) + module regression net (rm-002).
//
// Pins the latest-hydration-wins guard: a superseded (stale) getMessages
// response never clobbers the newer route's state — including across
// unmount/remount — and history hydration never wipes an in-flight stream
// for the same session (the first-meta navigate case). Normal hydration is
// pinned too so the guard cannot silently block it.
import { act, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { getMessages } from '../../api/chat';
import { useConversationStore } from '../../stores/conversation';
import { ChatPage } from '../ChatPage';

vi.mock('../../api/chat', () => ({
  listSessions: vi.fn(async () => ({ sessions: [] })),
  createSession: vi.fn(),
  getMessages: vi.fn(),
  startChat: vi.fn(),
  stopChat: vi.fn(),
  reconnectStream: vi.fn(),
}));

interface ChatMessage {
  message_id: number | null;
  role: 'user' | 'assistant';
  content: string;
}

function messages(...items: string[]): { messages: ChatMessage[] } {
  return {
    messages: items.map((content, index) => ({
      message_id: index + 1,
      role: index % 2 === 0 ? ('user' as const) : ('assistant' as const),
      content,
    })),
  };
}

function deferred<T>(): {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (reason?: unknown) => void;
} {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function renderAt(path: string): ReturnType<typeof render> {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:sessionId" element={<ChatPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ChatPage hydration races (rm-160)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useConversationStore.getState().reset();
  });
  afterEach(() => {
    useConversationStore.getState().reset();
  });

  it('hydrates history for the routed session when no stream is in flight', async () => {
    vi.mocked(getMessages).mockResolvedValue(messages('B question', 'B answer') as never);
    renderAt('/chat/s1');

    await waitFor(() => expect(useConversationStore.getState().sessionId).toBe('s1'));
    const state = useConversationStore.getState();
    expect(state.messages).toHaveLength(2);
    expect(state.streaming).toBe(false);
    // The chat shell renders the persisted user turn.
    expect(screen.getByText('B question')).toBeTruthy();
  });

  it('does not clobber an in-flight stream for the same session (first-meta navigate)', async () => {
    const store = useConversationStore.getState();
    store.startStreaming('s1', 'turn-1');
    store.appendToken('partial answer');
    vi.mocked(getMessages).mockResolvedValue(messages('old question', 'old full answer') as never);
    renderAt('/chat/s1');

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    const after = useConversationStore.getState();
    expect(after.streaming).toBe(true);
    expect(after.sessionId).toBe('s1');
    // The optimistic streamed bubble survives; the persisted full history
    // was NOT applied over it.
    expect(after.messages.at(-1)?.content).toBe('partial answer');
    expect(after.messages.some((m) => m.content === 'old full answer')).toBe(false);
  });

  it('a stale hydration response never clobbers the newer route (across remount)', async () => {
    const first = deferred<{ messages: ChatMessage[] }>();
    vi.mocked(getMessages).mockReturnValueOnce(first.promise as never);
    const { unmount } = renderAt('/chat/a');

    vi.mocked(getMessages).mockResolvedValue(messages('B message') as never);
    unmount();
    renderAt('/chat/b');
    await waitFor(() => expect(useConversationStore.getState().sessionId).toBe('b'));

    // The superseded response for /chat/a resolves last; it must be dropped.
    await act(async () => {
      first.resolve(messages('A message'));
      await Promise.resolve();
      await Promise.resolve();
    });

    const state = useConversationStore.getState();
    expect(state.sessionId).toBe('b');
    expect(state.messages.some((m) => m.content === 'A message')).toBe(false);
    expect(state.messages.some((m) => m.content === 'B message')).toBe(true);
  });

  it('a stale failure response never raises an error over the newer route', async () => {
    const first = deferred<{ messages: ChatMessage[] }>();
    vi.mocked(getMessages).mockReturnValueOnce(first.promise as never);
    const { unmount } = renderAt('/chat/a');

    vi.mocked(getMessages).mockResolvedValue(messages('B message') as never);
    unmount();
    renderAt('/chat/b');
    await waitFor(() => expect(useConversationStore.getState().sessionId).toBe('b'));

    await act(async () => {
      first.reject(new Error('late failure'));
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(useConversationStore.getState().error).toBeNull();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('records a load error for the current route when hydration fails', async () => {
    vi.mocked(getMessages).mockRejectedValue(new Error('backend down') as never);
    renderAt('/chat/s1');

    await waitFor(() => expect(useConversationStore.getState().error).toBe('backend down'));
    // The topbar transport indicator reflects the degraded state.
    expect(screen.getByText('Connection needs attention')).toBeTruthy();
  });
});
