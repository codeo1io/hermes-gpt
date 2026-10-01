# Prioritization — run 0aa75ea44f934b47acd316c4f5882eb5 (repository-maintenance c027a743 cycle 2)

- attempt: b11f493ea0ad4ce297b2625098b48813 (phase prioritize:prioritize)
- authored: 2026-10-01, worktree run-0aa75ea44f93-0aa75ea4 at HEAD caf60018d2 (+ uncommitted cycle-5 ROADMAP.md delta, ids rm-085..rm-094)
- inputs: assess spool 6d9fbb7b (F1-F5), research spool 0633763a (rm-085..rm-091), ROADMAP.md cycle-5 block, open candidates rm-066/067-remainder/069/075/077/081-084
- upstream probe this phase: `git log --all --not caf60018d2` shows upstream advanced 2 commits past the research gap — c83d27bb2b (site: v0.13 Autopilot candidate refresh) + 99ebf30998 (docs: README hero v0.13.0 candidate) → gap is now >=11 and upstream is mid-release-prep.

## Selected batch (this cycle): rm-092 + rm-093 + rm-094 — "close this run's assess findings"

One coherent, defect-first batch: all three items ARE this run's adversarial-assess findings (F1-F5) at the exact HEAD being modified; each is small-to-medium with red-pre-fix regression tests already specified in acceptance; no upstream/spec dependency; lands as one reviewable reliability+truthfulness seam. Shape precedent: cycle 4 (bb9c68fb) selected its own assess findings rm-076/078/079/080 end-to-end.

1. rm-092 (reliability, P115) — OAuth surface: remaining on-loop blocking lane (F1+F2, the rm-076 remainder). Every authenticated request (HTTP + WS handshake) does a fresh sqlite3.connect (synchronous=FULL, busy_timeout=15000) inline on the serving loop; issuance writes (token endpoint exchanges, register_client persist) also inline; docstring-claimed cache gate absent. Impact 5/5 — this is the top-priority open defect class in the tree and it invalidates landed rm-076's acceptance promise ("EVERY blocking call"). Effort S-M: offload pattern already proven by rm-076's landed implementation; acceptance specifies a lock-contention regression test that times out pre-fix.
2. rm-093 (reliability, P65) — ui_mount doctor false-PASS (F3+F5 folded). The once-written startup failure record is scanned only via audit_tail(limit=50); ordinary operator traffic evicts it and rotation archives it — doctor reports UI_MOUNT_HEALTHY while the UI is down. Impact 3.5/5: Operator's fail-closed posture goes untruthful exactly under load. Effort S-M (persistent signal or live probe); acceptance includes both churn-eviction and post-rotation regression tests.
3. rm-094 (docs, P50) — document the fleet/runner env knobs (F4): HERMES_GPT_FLEET_PEER_NAME/URL, HERMES_GPT_HOST/PORT, HERMES_GPT_PI_EXE, HERMES_GPT_OMX_EXE have zero doc hits (fleet trust attestation + runner-executable overrides discoverable only from source). Effort S, risk ~0; structural fix stays with rm-088.

Batch acceptance = the three items' acceptance blocks in ROADMAP.md:978/963/969; verified end-to-end by implement + review phases this cycle.

## Scored and deferred (rationale recorded)

- rm-085 + rm-081 (P115 upstream catch-up): highest stated priority but DEFERRED — dependency not stable: no v0.13 tag (tags stop at v0.12.0) and upstream advanced 2 more commits during this phase (site + README v0.13-candidate prep, verified above); largest effort in the pool (11+-commit integration + adopt-by-content reconciliation vs the fork's own Mission Control); high regression risk. A coherent batch must complete end-to-end THIS cycle; this one chases a moving target. Re-select next cycle once v0.13.0 tags.
- rm-083 (v0.13.0 release batch): blocked by version-policy rm-065 (open) and the rm-085 decision. DEFER.
- rm-086..rm-091 (research candidates): additive capabilities, none are defects; the batch principle prefers defects over features when both compete. HOLD as next-cycle material (rm-091 is a tiny ride-along if implement has slack; rm-088 remains the structural successor to rm-094).
- rm-077 (P70 dev-ex, browser-UI build path): real, independent seam, already passed over by cycle 4's selection. HOLD.
- rm-082 (Skills extension) / rm-084 (SEP-414 trace context): gated on SDK probes / cross-agent scope decisions. HOLD.
- rm-067 remainder (atomic-write durability, 12 fixed-.tmp sites): same FILE as rm-092 (token_store.py) but a different defect class (durability vs loop safety) — folding would grow the batch's risk. HOLD with seam note: pairs naturally after rm-092 lands.
- rm-066 (design-gated), rm-069 (Conductor's call on topology), rm-075 (P25 docstring truthfulness; fold candidate for any batch), rm-011/rm-012 (externally gated long-track). HOLD.

## Sibling interlocks (landing-gate awareness)

- Sibling run 6b026aed (family b428f728, assess c2630c42 COMPLETE) found the SAME defect set (oauth on-loop I/O, ui_mount doctor false-PASS, env-knob docs) — if its batch lands first, this run's implement phase reconciles at the landing gate (verify/re-derive instead of re-fixing); ids stay distinct per fleet invariant, landed-first keeps its numbering.
- Sibling run 1a6beeba minted rm-092..rm-098 in ITS unlanded roadmap delta (numbering collision with our rm-092..rm-094 is expected unlanded-vs-unlanded overlap; the landing gate renumbers per the landed-first convention — precedent: three parallel runs each minting rm-026+ were renumbered at integration).
- No unlanded sibling fix branches exist on any ref reachable here (`git log --all --not caf60018d2` = upstream v0.13 prep only).
