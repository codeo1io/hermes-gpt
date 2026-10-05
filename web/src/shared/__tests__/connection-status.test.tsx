// ConnectionStatus — regression net (rm-002). Pins the transport-health
// indicator: silent when connected, visible when disconnected/reconnecting,
// attempt counts during backoff, and the server-restart recovery note.
import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { ConnectionStatus } from '../ConnectionStatus';
import { useConnectionStore } from '../../stores/connection';

function resetStore(): void {
  useConnectionStore.setState({
    sseStatus: 'connected',
    reconnect: { phase: 'idle' },
    serverRestart: false,
    staleLeaseSeconds: 600,
  });
}

describe('ConnectionStatus (rm-002)', () => {
  afterEach(resetStore);

  it('renders nothing while connected and no restart is pending', () => {
    resetStore();
    const { container } = render(<ConnectionStatus />);
    expect(container.firstChild).toBeNull();
  });

  it('shows the disconnected pill', () => {
    useConnectionStore.setState({ sseStatus: 'disconnected' });
    render(<ConnectionStatus />);
    const pill = screen.getByTestId('connection-status');
    expect(pill.getAttribute('role')).toBe('status');
    expect(screen.getByText('Disconnected')).toBeTruthy();
  });

  it('shows the reconnecting state with the backoff attempt count', () => {
    useConnectionStore.setState({
      sseStatus: 'reconnecting',
      reconnect: { phase: 'backoff', attempt: 3, nextAttemptAt: Date.now() + 5_000 },
    });
    render(<ConnectionStatus />);
    expect(screen.getByText(/Reconnecting… \(attempt 3\)/)).toBeTruthy();
  });

  it('shows the server-restart interruption note with the stale-lease bound', () => {
    useConnectionStore.setState({
      sseStatus: 'reconnecting',
      reconnect: { phase: 'server-restart' },
      serverRestart: true,
      staleLeaseSeconds: 600,
    });
    render(<ConnectionStatus />);
    const pill = screen.getByTestId('connection-status');
    expect(pill.textContent).toContain('Reconnecting…');
    // The JSX note splits across text nodes; assert on the whole pill.
    expect(pill.textContent).toContain('interrupted; it can be resumed after reconnect');
    expect(pill.textContent).toContain('Stale turns older than 600s are shown as interrupted, never as running.');
  });
});
