// DeckOverview — regression net (rm-002). Pins the /ops landing: one card
// per mission surface with its canonical title and idle state, the static
// deck links, and per-surface readiness from the operator store.
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { DeckOverview } from '../DeckOverview';
import { SURFACE_SCHEMAS } from '../schemas';
import { MISSION_SURFACES } from '../types';
import { useOperatorStore } from '../../stores/operator';

const TITLES = [
  'Mission Control Overview',
  'Health',
  'Profiles',
  'Fleet',
  'Codex',
  'Cron',
  'Delegations',
  'Failures',
  'Approvals',
  'Vault',
  'Usage',
  'Audit',
];

function renderDeck(): ReturnType<typeof render> {
  return render(
    <MemoryRouter>
      <DeckOverview />
    </MemoryRouter>,
  );
}

describe('DeckOverview (rm-002)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    useOperatorStore.setState({ surfaces: {} });
  });

  it('renders exactly one idle card per mission surface, with canonical titles', () => {
    renderDeck();

    expect(screen.getByText('Flight Deck')).toBeTruthy();
    for (const title of TITLES) {
      expect(screen.getByText(title)).toBeTruthy();
    }
    const cards = document.querySelectorAll('.fd-deck-card');
    expect(cards.length).toBe(MISSION_SURFACES.length);
    expect(document.querySelectorAll('.fd-deck-card[data-state="idle"]').length).toBe(
      MISSION_SURFACES.length,
    );
    // Every card links to its per-surface route.
    const hrefs = Array.from(cards).map((c) => (c as HTMLAnchorElement).getAttribute('href'));
    for (const surface of MISSION_SURFACES) {
      expect(hrefs).toContain(`/ops/${surface}`);
    }
  });

  it('renders the static deck links (missions, events, contracts, swarm)', () => {
    renderDeck();

    expect(screen.getByRole('link', { name: 'Missions' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Event History' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Contracts' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Swarm Monitor' })).toBeTruthy();
  });

  it('reflects per-surface readiness and unavailability from the operator store', () => {
    useOperatorStore.setState({
      surfaces: {
        overview: { status: 'ready', data: { surface: 'overview', available: true } },
        vault: { status: 'ready', data: { surface: 'vault', available: false } },
      } as never,
    });
    renderDeck();

    const readyCard = document.querySelector('.fd-deck-card[data-state="ready"]');
    expect(readyCard?.textContent).toContain('Mission Control Overview');
    expect(readyCard?.textContent).toContain('ready');
    const unavailableCard = Array.from(document.querySelectorAll('.fd-deck-card')).find((c) =>
      c.textContent?.includes('Vault'),
    );
    expect(unavailableCard?.textContent).toContain('unavailable');
  });

  it('stays consistent with the schema-backed per-surface routes', () => {
    // App.tsx renders SurfacePanel for every SURFACE_SCHEMAS key; the deck's
    // card set is exactly MISSION_SURFACES, and every schema surface is
    // represented on the deck.
    renderDeck();
    expect(document.querySelectorAll('.fd-deck-card').length).toBe(MISSION_SURFACES.length);
    for (const surface of Object.keys(SURFACE_SCHEMAS)) {
      expect(MISSION_SURFACES).toContain(surface);
    }
  });
});
