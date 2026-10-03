# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Session turn concurrency

### Session turn lease

A time-limited exclusive claim that guarantees at most one live turn per chat session.

A turn acquires the lease under its holder token for one TTL window; while the turn runs it must keep renewing the lease well before the window closes (on an interval far shorter than the TTL, so several missed renewals still leave headroom). The lease is released when the turn completes. If the lease expires or is taken over while the turn still runs, renewal reports the loss and the turn must abort cooperatively rather than continue — the invariant is never allowed to lapse silently.

### Lease holder

The token that identifies which turn owns a session turn lease; renewal and release match on it, so only the owning turn can extend or free the lease.

### Lease renewal

The act of extending a still-owned session turn lease by one further TTL window.

Rules: renewal runs on a fixed interval well under the TTL; a transient store error during renewal is retried on the next interval and does not stop the turn; a renewal that reports the lease gone (expired or taken over) is terminal.

### Lease loss

The state in which a running turn can no longer renew its session turn lease because the lease expired or another turn took it over; the required response is a cooperative turn abort on the normal cancellation path, never continued execution.
