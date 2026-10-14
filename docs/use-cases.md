# Use cases

The use cases in the README's [Use cases](../README.md#use-cases) section are cut to their short form there. The text below completes them, under the heading of the use case it belongs to.

## A browser agent acts for someone you cannot see

When the guess is wrong, the person whose account the agent used pays for it.

## You run many agents and need to know which one to trust less today

For any other agent those factors are excluded: their weight is redistributed, and the composite is capped at the value it would have with them scored neutral (AIP-SPEC Section 6.1, implementation status).

## Why you can check this yourself

Why you can check this yourself: [`AIP-SPEC.md`](../AIP-SPEC.md) and the Internet-Draft [draft-fane-opena2a-aip](https://datatracker.ietf.org/doc/draft-fane-opena2a-aip/); [aip-conformance](https://github.com/opena2a-standards/aip-conformance), 7 byte-pinned fixtures (4 challenge-response transcripts, 3 trust-score compositions) with Go and Python verifiers; the live discovery document at `https://aim.opena2a.org/.well-known/aip`; and the reference implementation, [OpenA2A AIM (Agent Identity Management)](https://github.com/opena2a-org/agent-identity-management).
