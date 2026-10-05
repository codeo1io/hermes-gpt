// schemas.ts — regression net (rm-002). Pins the surface-schema registry the
// deck and per-surface routes are built from: every mission surface has a
// schema, keys are unique, and the composite overview exposes the canonical
// cross-surface stats/sections.
import { describe, expect, it } from 'vitest';

import { SURFACE_SCHEMAS } from '../schemas';
import { MISSION_SURFACES } from '../types';

describe('SURFACE_SCHEMAS (rm-002)', () => {
  it('covers every mission surface exactly once', () => {
    const schemaKeys = Object.keys(SURFACE_SCHEMAS);
    expect(new Set(schemaKeys).size).toBe(schemaKeys.length);
    for (const surface of MISSION_SURFACES) {
      expect(schemaKeys).toContain(surface);
    }
    expect(schemaKeys.length).toBe(MISSION_SURFACES.length);
  });

  it('gives each schema a title and unique stat/section keys within it', () => {
    for (const [surface, schema] of Object.entries(SURFACE_SCHEMAS)) {
      expect(schema.title, `title for ${surface}`).toBeTruthy();
      expect(schema.surface).toBe(surface);
      const stats = schema.stats ?? [];
      const sections = schema.sections ?? [];
      expect(new Set(stats.map((s) => s.key)).size).toBe(stats.length);
      expect(new Set(sections.map((s) => s.key)).size).toBe(sections.length);
      expect(sections.length).toBeGreaterThan(0);
    }
  });

  it('pins the composite overview schema: cross-surface stats and sections', () => {
    const overview = SURFACE_SCHEMAS.overview;
    expect(overview.title).toBe('Mission Control Overview');
    const statKeys = (overview.stats ?? []).map((s) => s.key);
    for (const key of ['fleet_health', 'profiles', 'pending_approvals', 'failures']) {
      expect(statKeys).toContain(key);
    }
    const sectionKeys = (overview.sections ?? []).map((s) => s.key);
    for (const key of ['surfaces_unavailable', 'cron', 'delegations', 'audit']) {
      expect(sectionKeys).toContain(key);
    }
  });

  it('pins the approvals surface schema used for deck metadata', () => {
    // App.tsx renders ApprovalsPanel directly for the approvals surface;
    // the schema still backs the deck card (title + pending section).
    expect((SURFACE_SCHEMAS.approvals.sections ?? []).map((s) => s.key)).toContain('approvals');
  });
});
