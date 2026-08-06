# Contributing to OpenA2A AIP

The OpenA2A Agent Identity Protocol is authored in the open and published with a working reference implementation (AIM). It is early, and we are looking for co-authors and contributors to help shape it before it goes to an external standards body. Your review, critique, and independent implementation work all carry weight on the spec.

## What we are looking for

- Review and critique. Read [AIP-SPEC.md](AIP-SPEC.md) and tell us where it is ambiguous, where it leaves interoperability gaps, or where the conformance levels do not hold up.
- An independent second implementation. A non-AIM implementation of AIP identity creation and verification is the strongest signal that the spec is sound. It does not need to be complete to be useful.
- Security audit and threat modeling of the spec itself, not just an implementation.
- Identity and protocol interop expertise. We want input from people who have shipped DID methods, verifiable credentials, agent cards, or capability models, and who can stress-test how AIP interoperates with adjacent standards.
- We need independent implementations and interoperability testing against OpenID Connect, WebAuthn, and W3C Verifiable Credentials.

## Who we are looking for

We especially welcome:

- Security and cryptography researchers, including academic and PhD-level work.
- Standards-process experts (W3C, IETF, OpenTelemetry) who can help take these specifications to external bodies.
- Engineers building agent platforms and runtimes, for independent implementations and adoption.
- Red teamers and security auditors.

## How to contribute

- Open an issue or pull request on this repository.
- Or email info@opena2a.org with "co-author" in the subject line.

Small fixes (typos, broken links, clarifications) can go straight to a pull request. For anything that changes the protocol surface, conformance levels, or wire format, open an issue first so the change can be discussed before implementation work begins.

## Ground rules

- Contributions are licensed under Apache-2.0, consistent with the project license.
- Be specific and evidence-based. Point to the section, the field, or the failing case.
- No purely theoretical claims without a path to validation. If you propose a change, describe how it could be tested or implemented.
