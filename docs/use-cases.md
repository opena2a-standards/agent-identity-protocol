# Use cases

The use cases below moved here from the README, which links this page. Each says what AIP gives the case, what you can run today and where the reference implementation stops.

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

## You run many agents and need to know which one to trust less today

A platform team runs agents built by several teams. One begins failing actions and tripping security alerts, and nobody has a number that moves, so its access stays where it was until a person notices.

AIP defines a trust score from 0.0 to 1.0 composed of nine weighted factors (Section 6). Penalties are applied and recorded against the agent, and the identity provider publishes a discovery document that any relying party can fetch.

What you can do today: run the first two commands in the README [Quick Start](../README.md#quick-start), which create an agent identity and fetch the identity provider's discovery document.

Where it stops today: the reference implementation scores all nine factors, but compliance counts only for an agent whose organization has a compliance snapshot, and user feedback only for an agent that has feedback ratings. For any other agent those factors are excluded: their weight is redistributed, and the composite is capped at the value it would have with them scored neutral (AIP-SPEC Section 6.1, implementation status).

## Why you can check this yourself

Why you can check this yourself: [`AIP-SPEC.md`](../AIP-SPEC.md) and the Internet-Draft [draft-fane-opena2a-aip](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/); [aip-conformance](https://github.com/opena2a-standards/aip-conformance), 7 byte-pinned fixtures (4 challenge-response transcripts, 3 trust-score compositions) with Go and Python verifiers; the live discovery document at `https://aim.opena2a.org/.well-known/aip`; and the reference implementation, [OpenA2A AIM (Agent Identity Management)](https://github.com/opena2a-org/agent-identity-management).
