# Use cases

The use cases below moved here from the README, which links this page. Each says what AIP gives the case, what you can run today and where the reference implementation stops. The page opens with who reads the specification and where each reader's question is answered.

## Who reads this

Each row names a reader, the question that brings them here and the text that answers it. An `AIP-SPEC.md:N` reference is the line in `AIP-SPEC.md` at the commit that added this table; the section link stays stable when lines move.

| Reader | The question they bring | Where it is answered |
|---|---|---|
| Security leader or CISO | What must an agent's identity provider guarantee before our agents are trusted, and what evidence does it keep? | [You have to decide what an agent's identity provider must guarantee](#you-have-to-decide-what-an-agents-identity-provider-must-guarantee); Level 2 of [Section 2](../AIP-SPEC.md#level-2-managed-identity) (`AIP-SPEC.md:70`); the security considerations of [Section 12](../AIP-SPEC.md#12-security-considerations) (`AIP-SPEC.md:980`); suspension and revocation, [Section 8.3](../AIP-SPEC.md#83-suspension-and-revocation) (`AIP-SPEC.md:806`) |
| IAM professional or identity architect | How does AIP sit beside the OAuth 2.0, OpenID Connect and DID infrastructure I run, and what does it not replace? | [`docs/interoperability.md`](interoperability.md), which gives each protocol AIP complements a status; provider-scoped `did:web` identifiers, [Section 3.2](../AIP-SPEC.md#32-decentralized-identifier-did) (`AIP-SPEC.md:132`); machine-to-machine authentication, [Section 5.4](../AIP-SPEC.md#54-machine-to-machine-authentication) (`AIP-SPEC.md:563`) |
| Platform or security engineer | How do I verify an agent and follow its trust over time, and what does a failure look like? | [A browser agent acts for someone you cannot see](#a-browser-agent-acts-for-someone-you-cannot-see); [You run many agents](#you-run-many-agents-and-need-to-know-which-one-to-trust-less-today); the verification rules of [Section 5.1.4](../AIP-SPEC.md#514-verification-rules) (`AIP-SPEC.md:449`); drift detection, [Section 8.4](../AIP-SPEC.md#84-drift-detection) (`AIP-SPEC.md:815`) |
| Agent developer or implementer | What do I implement first, and how do I show it conforms? | Level 1 of [Section 2](../AIP-SPEC.md#level-1-local-identity) (`AIP-SPEC.md:60`); the pinned-verdict rule of [Section 5.1.5](../AIP-SPEC.md#515-conformance-fixtures) (`AIP-SPEC.md:513`); the commands under [A browser agent acts for someone you cannot see](#a-browser-agent-acts-for-someone-you-cannot-see) |
| GRC, audit or compliance reader | Who suspended, revoked or changed an agent, when and why, and which record shows it? | [An auditor asks who suspended an agent, when and why](#an-auditor-asks-who-suspended-an-agent-when-and-why); [Section 8.3](../AIP-SPEC.md#83-suspension-and-revocation) (`AIP-SPEC.md:813`); the audit logs of [Section 9](../AIP-SPEC.md#9-audit) (`AIP-SPEC.md:831`). The specification maps to no control framework; OASB appears only as a link in the [README](../README.md) |
| Standards reviewer (IETF or AIW participant) | What problem does AIP solve, how does it relate to existing work and to other specifications named AIP, and how mature is it? | [`docs/interoperability.md`](interoperability.md); [`docs/naming-and-prior-art.md`](naming-and-prior-art.md); the Internet-Draft revision and where it differs from the specification, [`docs/specification-notes.md`](specification-notes.md); what the reference implementation has, [`GAP-ANALYSIS.md`](../GAP-ANALYSIS.md); [Section 13](../AIP-SPEC.md#13-iana-considerations) (`AIP-SPEC.md:1005`) |

### The readers

- **Security leader or CISO**
  - Who: accountable for the organization's security risk, and for which agents and vendors may act on its systems.
  - Why they open it: a team or a vendor wants to connect agents to internal systems, and the identity provider behind them is not one the organization runs.
  - What they decide: which conformance level to require of that provider, and which rules to check before its agents are trusted.
  - How they verify: the level the provider declares in its discovery document, checked against what it serves, and the pinned verdicts of the Section 5.1 fixtures.
- **IAM professional or identity architect**
  - Who: runs the identity systems the organization already has, such as OAuth 2.0 and OpenID Connect, X.509 certificates, workload identity such as SPIFFE, DIDs and privileged access management.
  - Why they open it: to see how agent identities, keys and tokens fit beside that infrastructure.
  - What they decide: which identifier form to accept, how agents authenticate machine to machine, and where keys are stored.
  - How they verify: [`docs/interoperability.md`](interoperability.md), whose statuses separate what is specified from what the reference implementation has.
- **Platform or security engineer**
  - Who: deploys, operates and monitors the components that check agents at runtime, and is paged when they fail.
  - Why they open it: they verify agents at runtime and act on trust-score changes and drift alerts.
  - What they decide: challenge freshness and nonce handling (single use, five minutes at most), and what happens when drift is detected.
  - How they verify: the Section 5.1 transcripts of aip-conformance, and the discovery document of the provider they use.
- **Agent developer or implementer**
  - Who: writes the identity provider, the relying party or the agent that proves its identity.
  - Why they open it: they have to produce or check identities that other implementations accept.
  - What they decide: which conformance level to implement, starting from Level 1, local identity.
  - How they verify: the pinned verdict on every Section 5.1 fixture, and the trust-score compositions of Section 6.1.
- **GRC, audit or compliance reader**
  - Who: maps controls to evidence and reads the records an auditor asks for.
  - Why they open it: an auditor asks who suspended, revoked or changed an agent, when and why.
  - What they decide: whether the provider's audit log is evidence they accept, and how its integrity is protected.
  - How they verify: the event types of Section 9.2, and how the provider protects its log, which for the reference implementation [Appendix A.1](../AIP-SPEC.md#a1-spec-sections-currently-implemented-by-aim) records.
- **Standards reviewer (IETF or AIW participant)**
  - Who: a participant in an IETF or AIW discussion who judges whether a problem needs new work.
  - Why they open it: to judge whether agent identity needs a protocol beside OAuth 2.0, OpenID Connect, WebAuthn and W3C DIDs, and how AIP relates to other specifications of the same name.
  - What they decide: whether to review, implement or co-author it, and what to ask the editors to change.
  - How they verify: the Internet-Draft on the datatracker, [`docs/specification-notes.md`](specification-notes.md) and [`GAP-ANALYSIS.md`](../GAP-ANALYSIS.md).

## A browser agent acts for someone you cannot see

A shopping agent drives a real browser to your checkout for a person who has left the room. The web identifies people with passwords and cookies and identifies servers with TLS certificates; the agent is neither, so your site guesses from a User-Agent string, and anyone can send any string. When the guess is wrong, the person whose account the agent used pays for it.

AIP gives the agent a cryptographic identity and a way to prove it. The verifier issues a random challenge, the agent signs it with the key bound to its identity, and the verifier checks the signature, the key binding, the challenge's freshness and that the nonce was used once (AIP-SPEC Section 5.1).

What you can do today: run the Section 5.1 transcripts in the conformance suite. One is accepted; three are rejected for a wrong key, a stale challenge and a replayed nonce.

```bash
git clone https://github.com/opena2a-standards/aip-conformance
cd aip-conformance/verifiers/go
go run . ../../fixtures
```

Where it stops today: the reference identity provider advertises the challenge endpoint in its discovery document but does not serve that route yet, so the transcripts above are the way to exercise Section 5.1.

Who acts: the relying party, meaning the engineer whose site or service checks the agent, and the developer whose agent answers the challenge.

Spec text: the challenge-response protocol of [Section 5.1](../AIP-SPEC.md#51-challenge-response-protocol) (`AIP-SPEC.md:342`) and its verification rules, [Section 5.1.4](../AIP-SPEC.md#514-verification-rules) (`AIP-SPEC.md:449`); and single-use nonces valid for five minutes at most, [Section 12.2](../AIP-SPEC.md#122-replay-attacks) (`AIP-SPEC.md:993`).

## You run many agents and need to know which one to trust less today

A platform team runs agents built by several teams. One begins failing actions and tripping security alerts, and nobody has a number that moves, so its access stays where it was until a person notices.

AIP defines a trust score from 0.0 to 1.0 composed of nine weighted factors (Section 6). Penalties are applied and recorded against the agent, and the identity provider publishes a discovery document that any relying party can fetch.

What you can do today: run the first two commands in the README [Quick Start](../README.md#quick-start), which create an agent identity and fetch the identity provider's discovery document.

Where it stops today: the reference implementation scores all nine factors, but compliance counts only for an agent whose organization has a compliance snapshot, and user feedback only for an agent that has feedback ratings. For any other agent those factors are excluded: their weight is redistributed, and the composite is capped at the value it would have with them scored neutral (AIP-SPEC Section 6.1, implementation status).

Who acts: the platform team that runs the agents, and the identity provider that scores them.

Spec text: the multi-factor algorithm of [Section 6.1](../AIP-SPEC.md#61-multi-factor-algorithm) (`AIP-SPEC.md:589`); drift detection and its penalties, [Section 8.4](../AIP-SPEC.md#84-drift-detection) (`AIP-SPEC.md:815`); and the rule that trust scores MUST be computed server-side, [Section 12.4](../AIP-SPEC.md#124-trust-score-manipulation) (`AIP-SPEC.md:1001`).

## You have to decide what an agent's identity provider must guarantee

A business unit wants to connect agents built by another team to internal systems. Each agent will prove who it is through an identity provider you do not run. Before any of them is trusted, you have to say what that provider must guarantee.

Who acts: the security leader, with the platform team that will connect the agents.

Without the specification: an agent's identity is whatever key or token someone placed in its environment, and nobody can say who may change its capabilities, whether a recorded response can be replayed, or how the agent is stopped.

What the specification does: Level 2, managed identity, is the level for organizations, and it requires challenge-response verification, trust scoring, a server-side audit log, API key or JWT authentication and drift detection ([Section 2](../AIP-SPEC.md#level-2-managed-identity), `AIP-SPEC.md:70`). The security considerations of [Section 12](../AIP-SPEC.md#12-security-considerations) set four rules: private keys MUST be encrypted at rest and MUST NOT be transmitted in plaintext, and the provider stores only public keys (`AIP-SPEC.md:984`); challenge-response MUST use single-use nonces valid for five minutes at most (`AIP-SPEC.md:993`); an agent MUST NOT be able to grant itself capabilities (`AIP-SPEC.md:997`); and trust scores MUST be computed server-side, never reported by the agent (`AIP-SPEC.md:1001`). A provider MUST support suspension and revocation, each logged with reason, actor and timestamp ([Section 8.3](../AIP-SPEC.md#83-suspension-and-revocation), `AIP-SPEC.md:813`). An implementation claiming Section 5.1 conformance MUST produce the pinned verdict on every fixture ([Section 5.1.5](../AIP-SPEC.md#515-conformance-fixtures), `AIP-SPEC.md:513`).

What to require, in the specification's terms: the conformance level the provider declares, with the Level 2 requirements behind it; the four rules of Section 12; and the pinned verdicts of the Section 5.1 fixtures.

How to see it work: a declared level is a claim to check against what the provider serves. The reference provider, OpenA2A AIM (Agent Identity Management), targets Level 2, and on 2026-10-30 its discovery document declared that level:

```sh
curl -s https://aim.opena2a.org/.well-known/aip | jq .conformanceLevel
# 2
```

[Appendix A.1](../AIP-SPEC.md#a1-spec-sections-currently-implemented-by-aim) (`AIP-SPEC.md:1063`) records that the same provider does not serve the Section 5.1 challenge-response exchange, which Level 2 requires. The fixtures show what a conforming verifier refuses: a response signed with another agent's key, and a challenge from an issuer the verifier does not trust. From `aip-conformance/verifiers/go` in the clone made under [A browser agent acts for someone you cannot see](#a-browser-agent-acts-for-someone-you-cannot-see):

```sh
go run . ../../fixtures/challenge-response-other-agent-key.json ../../fixtures/challenge-response-untrusted-issuer.json
```

Output at aip-conformance commit `52ba849`, run on 2026-10-30:

```
PASS  ../../fixtures/challenge-response-other-agent-key.json
       expected: REJECT [UNTRUSTED_KEY]
       observed: REJECT[UNTRUSTED_KEY: response.publicKey does not match bound key for agentDid "did:opena2a:agent:agent_conformance_test_001" (got 278117fc144c7234..., bound is 3d4017c3e843895a...)]
PASS  ../../fixtures/challenge-response-untrusted-issuer.json
       expected: REJECT [UNTRUSTED_ISSUER]
       observed: REJECT[UNTRUSTED_ISSUER: challenge.issuerDid "did:opena2a:authority:opena2a.org" is not in verifierState.trustedIssuers]

summary: 2 pass, 0 fail (2 fixtures)
```

Out of scope: the fixtures cover Section 5.1 and the Section 6.1 trust score, not the Section 12 rules or the rest of Level 2. Those are checked against what a provider states about itself, as Appendix A.1 does for the reference implementation. AIP answers who an agent is; whether its code and provenance can be trusted is ATP's question ([How AIP and ATP work together](interoperability.md#how-aip-and-atp-work-together)).

## An auditor asks who suspended an agent, when and why

After an incident, an auditor asks for the record of what happened to one agent's identity: when it was suspended, who did it and why, and which capabilities it held at the time.

Who acts: the GRC or audit reader, and the identity provider that keeps the record.

Without the specification: the answer is pieced together from application logs and tickets, if they still exist, and nothing says which events had to be recorded.

What the specification does: a provider MUST support suspension, which is temporary and reversible, and revocation, which is permanent, and both MUST be logged in the audit trail with reason, actor and timestamp ([Section 8.3](../AIP-SPEC.md#83-suspension-and-revocation), `AIP-SPEC.md:813`). A Level 2 or Level 3 implementation MUST keep a server-side audit log in an append-only data store ([Section 9.2](../AIP-SPEC.md#92-server-audit-log), `AIP-SPEC.md:853`), whose event types include `identity_suspended`, `identity_revoked`, `capability_granted`, `capability_revoked`, `capability_violation`, `trust_score_changed`, `drift_detected` and `key_rotated`. A Level 1 implementation MUST keep a local append-only audit log ([Section 9.1](../AIP-SPEC.md#91-local-audit-log), `AIP-SPEC.md:835`).

How to see it work: not runnable here. aip-conformance has no fixture for Section 8.3 or Section 9, and the reference provider's audit endpoint answers only an authenticated caller: on 2026-10-30, `GET https://aim.opena2a.org/api/v1/agents/<id>/audit` without credentials returned HTTP 401.

Out of scope: the specification requires an append-only store and does not require a signed or hash-chained log. [Appendix A.1](../AIP-SPEC.md#a1-spec-sections-currently-implemented-by-aim) (`AIP-SPEC.md:1066`) records that the reference implementation's audit log is append-only at the repository layer and not cryptographically signed, so its integrity relies on database access control. The specification maps its events to no control framework.

## Why you can check this yourself

Why you can check this yourself: [`AIP-SPEC.md`](../AIP-SPEC.md) and the Internet-Draft [draft-fane-opena2a-aip](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/); [aip-conformance](https://github.com/opena2a-standards/aip-conformance), 7 byte-pinned fixtures (4 challenge-response transcripts, 3 trust-score compositions) with Go and Python verifiers; the live discovery document at `https://aim.opena2a.org/.well-known/aip`; and the reference implementation, [OpenA2A AIM (Agent Identity Management)](https://github.com/opena2a-org/agent-identity-management).
