// Composer — regression net (rm-002). Pins send/stop affordances: Enter
// submits the trimmed text and clears the box, Shift+Enter inserts a newline
// instead, the Send button tracks disabled/empty state, and streaming swaps
// Send for Stop.
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { Composer } from '../Composer';

function type(text: string): void {
  fireEvent.change(screen.getByLabelText('Message Hermes'), { target: { value: text } });
}

describe('Composer (rm-002)', () => {
  it('sends the trimmed text on submit and clears the input', () => {
    const onSend = vi.fn();
    render(<Composer streaming={false} profile="default" model="" onSend={onSend} onStop={() => {}} />);

    type('  hello hermes  ');
    const form = screen.getByLabelText('Message Hermes').closest('form') as HTMLFormElement;
    fireEvent.submit(form);

    expect(onSend).toHaveBeenCalledWith('hello hermes');
    expect((screen.getByLabelText('Message Hermes') as HTMLTextAreaElement).value).toBe('');
  });

  it('Enter submits, Shift+Enter does not', () => {
    const onSend = vi.fn();
    render(<Composer streaming={false} profile="default" model="" onSend={onSend} onStop={() => {}} />);

    type('one');
    fireEvent.keyDown(screen.getByLabelText('Message Hermes'), {
      key: 'Enter',
      shiftKey: true,
    });
    expect(onSend).not.toHaveBeenCalled();

    fireEvent.keyDown(screen.getByLabelText('Message Hermes'), { key: 'Enter' });
    expect(onSend).toHaveBeenCalledTimes(1);
    expect(onSend).toHaveBeenCalledWith('one');
  });

  it('keeps Send disabled while empty or externally disabled, and never sends blank text', () => {
    const onSend = vi.fn();
    const { rerender } = render(
      <Composer streaming={false} profile="default" model="" onSend={onSend} onStop={() => {}} />,
    );
    expect(screen.getByLabelText('Send message')).toHaveProperty('disabled', true);

    type('   ');
    expect(screen.getByLabelText('Send message')).toHaveProperty('disabled', true);

    type('real message');
    expect(screen.getByLabelText('Send message')).toHaveProperty('disabled', false);

    rerender(
      <Composer streaming={false} disabled profile="default" model="" onSend={onSend} onStop={() => {}} />,
    );
    expect(screen.getByLabelText('Send message')).toHaveProperty('disabled', true);
    expect(onSend).not.toHaveBeenCalled();
  });

  it('offers Stop instead of Send while streaming, and Stop calls onStop', () => {
    const onStop = vi.fn();
    render(
      <Composer streaming profile="default" model="sonnet" onSend={() => {}} onStop={onStop} />,
    );
    expect(screen.queryByLabelText('Send message')).toBeNull();
    fireEvent.click(screen.getByLabelText('Stop generating'));
    expect(onStop).toHaveBeenCalledTimes(1);
    // Profile/model hint stays visible for context.
    expect(screen.getByText('profile · default · sonnet')).toBeTruthy();
  });
});
