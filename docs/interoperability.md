# Interoperability

AIP is designed to complement the six protocols below. Each line ends with a status, as of 2026-10-11, for what that line describes. **Specified** means AIP-SPEC describes it and no code for it was found in the reference implementation. **Implemented** means the reference implementation has code for it. **Tested in conformance** means a fixture in [aip-conformance](https://github.com/opena2a-standards/aip-conformance) exercises it; none of the six is, because that suite's fixtures cover the Section 5.1 challenge-response and the Section 6.1 trust-score composition.

- [Google A2A Protocol](https://github.com/a2aproject/A2A) — AIP identity in agent cards. **Implemented** in part, for the agent card: the card the reference implementation serves carries the agent's ID and registered public key in an `aim` extension, and that ID is the UUID the provider assigns (AIP-SPEC Section 3.1). Its A2A verification service (AIP-SPEC Appendix A) is not assessed here.
- [Anthropic MCP](https://modelcontextprotocol.io) — capability-based tool access control. **Implemented** in part: the reference implementation checks an agent's capabilities server-side. Verifying a connecting agent by the Section 5.1 challenge-response is specified, and the reference implementation does not serve that exchange.
- [OpenID Connect](https://openid.net/connect/) — JWT tokens for machine-to-machine auth. **Implemented** in part: the reference implementation serves an OAuth 2.0 token endpoint (RFC 6749) that accepts the JWT-bearer grant type of RFC 7523, where a registered agent exchanges an assertion signed with its Ed25519 key for a bearer access token. The request carries that assertion in `client_assertion`, with `client_id` and `client_assertion_type`; the endpoint reads no `assertion` parameter, in which RFC 7523 Section 2.1 carries the JWT. That endpoint returns no OpenID Connect ID token, and Section 5.4 defines AIP's own JWT bearer tokens and no OAuth 2.0 or OpenID Connect flow.
- [WebAuthn/FIDO2](https://www.w3.org/TR/webauthn-3/) — hardware key storage for browsers. **Specified** (Sections 11.1 and 12.1).
- [W3C Verifiable Credentials](https://www.w3.org/TR/vc-data-model-2.0/) — trust scores as VCs. **Specified** (Section 6.4).
- [ATP (Agent Trust Protocol)](https://github.com/opena2a-standards/agent-trust-protocol) — ecosystem trust. **Implemented** in part: the reference implementation has a one-way push through its registry bridge, and its credential issuance route sends the agent's 9-factor behavioral score to the OpenA2A Registry, which signs it into a credential and records the issuance in its transparency log (AIP-SPEC Appendix A.1). The reference implementation does not compute the combined score of AIP-SPEC Section 6.5.

The rows behind these statuses are in [GAP-ANALYSIS.md](../GAP-ANALYSIS.md) (A2A agent card identity, MCP capability-based tool access, OAuth 2.0 / OIDC, WebAuthn/FIDO2, Verifiable Credential expression, ATP integration) and in AIP-SPEC Appendix A.1 (§4 Capabilities, §5 Verification, §6.5 ATP integration).

## How AIP and ATP Work Together

```
AIP (identity + behavior)     ATP (code + provenance)
  "Who is this agent?"           "Is this agent's code safe?"
         ↓                              ↓
              Combined Trust Decision
              "Is this agent safe to use?"
```
