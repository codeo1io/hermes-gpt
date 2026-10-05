// ActivityCard — regression net (rm-002). Pins the collapsed/expanded tool
// activity card: running vs terminal elapsed text, aria wiring between the
// summary button and its detail region, and the executing placeholder.
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ActivityCard } from '../ActivityCard';
import type { ToolActivity } from '../../stores/conversation';

function activity(overrides: Partial<ToolActivity>): ToolActivity {
  return {
    callId: 'call-1',
    name: 'hermes_search_files',
    brief: 'pattern="nightly"',
    status: 'running',
    expanded: false,
    durationMs: null,
    summary: undefined,
    ...overrides,
  };
}

describe('ActivityCard (rm-002)', () => {
  it('renders the tool label, brief, and running elapsed text while collapsed', () => {
    render(<ActivityCard activity={activity({})} onToggle={() => {}} />);
    const summary = screen.getByRole('button');
    expect(summary.getAttribute('aria-expanded')).toBe('false');
    expect(summary.getAttribute('aria-controls')).toBe('activity-call-1');
    expect(screen.getByText('tool · hermes_search_files')).toBeTruthy();
    expect(screen.getByText('pattern="nightly"')).toBeTruthy();
    expect(screen.getByText('running')).toBeTruthy();
    // No detail region while collapsed.
    expect(screen.queryByText('3 matches')).toBeNull();
  });

  it('exposes the result summary and final duration when expanded and finished', () => {
    render(
      <ActivityCard
        activity={activity({ status: 'ok', expanded: true, durationMs: 42, summary: '3 matches' })}
        onToggle={() => {}}
      />,
    );
    expect(screen.getByRole('button').getAttribute('aria-expanded')).toBe('true');
    expect(screen.getByText('3 matches')).toBeTruthy();
    expect(screen.getByText('42ms')).toBeTruthy();
  });

  it('shows the executing placeholder while expanded but unfinished', () => {
    render(<ActivityCard activity={activity({ expanded: true })} onToggle={() => {}} />);
    expect(screen.getByText('Executing…')).toBeTruthy();
  });

  it('toggles expansion through onToggle and mirrors the data-status attribute', () => {
    const onToggle = vi.fn();
    const { container, rerender } = render(
      <ActivityCard activity={activity({ status: 'error' })} onToggle={onToggle} />,
    );
    const section = container.querySelector('.activity');
    expect(section?.getAttribute('data-status')).toBe('error');
    fireEvent.click(screen.getByRole('button'));
    expect(onToggle).toHaveBeenCalledTimes(1);

    rerender(<ActivityCard activity={activity({ status: 'error', expanded: true })} onToggle={onToggle} />);
    expect(container.querySelector('.activity')?.getAttribute('data-status')).toBe('error');
    expect(screen.getByText('Executing…')).toBeTruthy();
  });
});
