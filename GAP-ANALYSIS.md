# AIM → AIP: Gap Analysis

## What Exists vs What the Spec Requires

Based on source code review of `agent-identity-management` (March 2026; rows marked *updated 2026-07* re-verified against the current tree).

### Identity (Section 3)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| Ed25519 keypair generation | Complete | `apps/backend/internal/crypto/keygen.go` |
| ML-DSA-65 hybrid signing | Complete | `apps/backend/internal/crypto/pqc/hybrid.go` |
| Agent ID format (aim_XXXXXXXX) | Complete | `apps/backend/internal/domain/agent.go` |
| DID resolution (did:aip:) | Complete (*updated 2026-07*) — `did:aip:aim_<uuid>` resolver; other methods rejected | `handlers/aip_handler.go` (ResolveDID), `domain/agent_did.go` |
| DID Document generation | Complete (*updated 2026-07*) — W3C DID Document served by the resolver | `handlers/aip_handler.go` |
| Local identity file format | Partial — SDK creates files but format not standardized | `sdk/typescript/` |
| Key rotation with grace period | Complete | `agent.go` (KeyRotationGraceUntil, PreviousPublicKey) |

### Capabilities (Section 4)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| namespace:action format | Complete | `apps/backend/internal/domain/capability.go` |
| Reserved namespaces | Complete (8 namespaces) | `capability.go` |
| Capability violation tracking | Complete | `capability.go` (CapabilityViolation) |
| Capability negotiation protocol | NOT IMPLEMENTED — capabilities checked server-side only | - |
| Custom org namespaces | NOT IMPLEMENTED | - |

### Verification (Section 5)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| Challenge-response (Ed25519) | Complete | `apps/backend/internal/application/verification_event_service.go` |
| MCP verification flow | Complete | `mcp_service.go` |
| A2A verification flow | Complete | `a2a_service.go` |
| OAuth 2.0 / OIDC | REMOVED from codebase | `auth_service.go` line 54 comment |
| WebAuthn/FIDO2 | NOT IMPLEMENTED | - |
| JWT tokens | Complete (custom, not standard OAuth) | `infrastructure/auth/jwt.go` |
| API keys | Complete | `api_key_service.go` |

### Trust Scoring (Section 6)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| 9-factor algorithm (spec §6.1) | 6 of 9 factors implemented (*updated 2026-07*; execution isolation measured; §6.1 exclusion + anti-gaming cap implemented) | `trust_calculator.go` |
| Verification factor (25%) | Complete | `trust_calculator.go` |
| Uptime factor (15%) | Complete | `trust_calculator.go` |
| Success rate factor (15%) | Complete | `trust_calculator.go` |
| Security alerts factor (15%) | Complete | `trust_calculator.go` |
| Compliance factor (10%) | STUB (TODO comment) | `trust_calculator.go` |
| Execution isolation factor (10%) | Complete (*updated 2026-07*) — measured in the composite; persistence of the stored breakdown column is a filed follow-up | `trust_calculator.go` |
| Age factor (5%) | Complete | `trust_calculator.go` |
| Drift factor (3%) | STUB (TODO comment) | `trust_calculator.go` |
| Feedback factor (2%) | STUB (TODO comment) | `trust_calculator.go` |
| Verifiable Credential expression | NOT IMPLEMENTED | - |
| ATP integration | Partial (one-way push via registry bridge) | `registry_bridge_service.go` |

### Governance (Section 7)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| Policy format (YAML) | NOT IMPLEMENTED (policies in DB, not YAML) | `security_policy_service.go` |
| Policy actions (allow/deny/approve/rate_limit) | Partial | `security_policy_service.go` |
| SOUL integration | NOT IMPLEMENTED in AIM (SOUL is CLI-side) | - |

### Lifecycle (Section 8)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| State machine | Complete (pending→verified→suspended→revoked) | `agent.go` |
| Key rotation | Complete | `agent.go` |
| Drift detection | Complete | `drift_detection_service.go` |
| Suspension | Complete | `agent_service.go` |
| Revocation | Complete | `agent_service.go` |

### Audit (Section 9)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| Server audit log | Complete | `audit_service.go` |
| Local audit log (SDK) | Complete | SDK writes to `audit.jsonl` |
| Verification events | Complete (comprehensive) | `verification_event_service.go` |

### Discovery (Section 10)

| Spec Requirement | Implementation Status | File |
|-----------------|----------------------|------|
| /.well-known/aip | NOT IMPLEMENTED | - |

---

## Priority Implementation Order

1. **/.well-known/aip discovery endpoint** — minimum for standard compliance
2. **DID resolution** — required for Level 3 and cross-platform identity
3. **Complete trust scoring** — implement compliance, drift, feedback factors
4. **Verifiable Credentials** — trust scores as W3C VCs for portability
5. **OAuth 2.0 / OIDC** — re-add for standard machine-to-machine auth
6. **WebAuthn/FIDO2** — browser-based key storage for Chrome integration
7. **Capability negotiation** — runtime negotiation protocol between agents
8. **YAML policy format** — declarative governance policies

---

## Prior Art and Naming in the IETF Landscape (June 2026)

The abbreviations "AIP" and the sibling "AAP" are each used by more than one
Internet-Draft. This section records that prior art and how OpenA2A AIP relates to
it, so implementers and reviewers can disambiguate. When referenced outside this
repository, use the fully qualified name **OpenA2A AIP**.

### Drafts using the "AIP" / "AAP" names

| Draft | Author(s) | datatracker (initial) | Scope |
|---|---|---|---|
| draft-aip-agent-identity-protocol | Cao, Arango (NVIDIA) | -00, 2026-03-16 | Agent identity registry + enforcement proxy |
| draft-singla-agent-identity-protocol | Singla | -00, 2026-04-17 | Agent identity + delegation |
| draft-aap-oauth-profile, "Agent Authorization Profile" | Cruz (independent) | -01, 2026-02-07 | OAuth 2.0 profile for agent-to-API authorization |
| OpenA2A AIP (this spec) | OpenA2A | not yet filed | Identity, capabilities, verification, trust scoring, governance, lifecycle, audit |
| OpenA2A AAP (companion) | OpenA2A | not yet filed | Authorization token model + broker/resolution layer |

### OpenA2A AIP vs draft-aip-agent-identity-protocol (NVIDIA)

The two specifications share a common spine — a Layer 1 agent-identity registry
and a Layer 2 policy/enforcement proxy — and differ on what is built above it.

| Dimension | draft-aip-agent-identity-protocol-00 | OpenA2A AIP |
|---|---|---|
| Agent identifier | host-prefixed UUIDv4 (`host/uuid`) | DID (`did:opena2a`; W3C did-extensions PR #717) |
| Signing keys | Ed25519 | Ed25519, with ML-DSA-65 hybrid in the ATX credential |
| Identity registry | HTTP registry, agent record | Managed / federated identity (Conformance Levels 2–3) |
| Per-call attestation | per-call signed AIP token (argumentsHash + nonce) | challenge-response verification (Section 5) |
| Enforcement | Layer 2 forward proxy; ALLOW / DENY / HOLD; YAML policy, DLP, HITL | governance (Section 7) + proxy enforcement |
| Capability model | tool allowlists only | structured capability vocabulary + reserved namespaces (Section 4) |
| Trust score | not defined | multi-factor trust score + levels + history (Section 6) |
| Portable credential | per-call JSON token | ATX signed portable credential via ATP |
| Transparency log | not defined | RFC 6962 Merkle log (Registry) |
| Verifiable Credentials | not defined | W3C VC expression of trust (Section 6.4) |
| Revocation | status + SSE invalidation | suspension / revocation + drift detection (Section 8) |

The identity-and-enforcement spine is common to both. The elements specific to
OpenA2A AIP — DID-based identity, a structured capability vocabulary, a
multi-factor trust score, a portable signed credential (ATX) carried via ATP, a
transparency log, and W3C Verifiable Credential expression — are not present in
draft-aip-agent-identity-protocol-00. OpenA2A AIP leads with those elements rather
than with the shared identity spine.
