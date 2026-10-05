// AccountStatusBanner — behavior contract (§13) + local-mode-only deployment
// scope pin (rm-050). The banner is recovery UX for same-origin no-auth
// /api/me deployments (loopback default boundary); on auth-configured
// deployments the SPA attaches no credentials, /api/me cannot resolve a real
// accountStatus, and remote auth failures surface through the server's 401
// envelope — never through this banner.
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ACCOUNT_BANNER_SCOPE, AccountStatusBanner } from '../AccountStatusBanner';

describe('AccountStatusBanner (rm-050)', () => {
  it('pins the local-mode-only deployment scope marker', () => {
    expect(ACCOUNT_BANNER_SCOPE).toBe('local-mode-only');
  });

  it('renders nothing for the ok state', () => {
    const { container } = render(<AccountStatusBanner status="ok" />);
    expect(container.firstChild).toBeNull();
  });

  it.each([
    ['expired', 'Session expired', 'read-only chat history remains available'],
    ['revoked', 'Access tokens revoked', 'read-only chat history remains available'],
    ['unauthorized', 'Authentication required', 'Sign in to continue'],
  ] as const)('renders the %s recovery banner with its §13 copy', (status, title, body) => {
    render(<AccountStatusBanner status={status} />);
    const banner = screen.getByTestId('account-status-banner');
    expect(banner.getAttribute('role')).toBe('alert');
    expect(banner.getAttribute('data-status')).toBe(status);
    expect(screen.getByText(title)).toBeTruthy();
    expect(screen.getByText(new RegExp(body))).toBeTruthy();
  });

  it('notes disabled mutating controls by default and omits the note when mutations remain enabled', () => {
    const { rerender } = render(<AccountStatusBanner status="expired" />);
    expect(
      screen.getByText(/Mutating controls are disabled until you re-authenticate\./),
    ).toBeTruthy();

    rerender(<AccountStatusBanner status="expired" mutationsEnabled />);
    expect(
      screen.queryByText(/Mutating controls are disabled until you re-authenticate\./),
    ).toBeNull();
  });

  it('renders the re-auth affordance: href when provided, callback fallback otherwise', () => {
    const { unmount } = render(
      <AccountStatusBanner status="unauthorized" onReauth={() => {}} reauthHref="/oauth/authorize" />,
    );
    const link = screen.getByText('Re-authenticate');
    expect(link.getAttribute('href')).toBe('/oauth/authorize');
    unmount();

    const onReauth = vi.fn();
    render(<AccountStatusBanner status="unauthorized" onReauth={onReauth} />);
    fireEvent.click(screen.getByText('Re-authenticate'));
    expect(onReauth).toHaveBeenCalledTimes(1);
  });
});
