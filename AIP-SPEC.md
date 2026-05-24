# Agent Identity Protocol (AIP)

## An Open Standard for AI Agent Identity, Capabilities, and Trust

**Version:** 1.0.0-draft
**Authors:** OpenA2A
**Date:** March 2026

---

## Abstract

The Agent Identity Protocol (AIP) defines an open standard for creating, managing, and verifying cryptographic identities for AI agents. As AI agents proliferate across browsers, cloud platforms, and enterprise environments, the question "which agent is this, what can it do, and should I trust it?" needs a standardized answer.

AIP provides:

1. **Identity** — cryptographic keypairs bound to agent metadata, resolvable via DID (Section 3)
2. **Capabilities** — a structured vocabulary for what agents can do, with enforcement (Section 4)
3. **Verification** — challenge-response protocol for proving agent identity (Section 5)
4. **Trust Scoring** — multi-factor algorithm for computing and communicating trust (Section 6)
5. **Governance** — behavioral policies that constrain agent actions (Section 7)
6. **Lifecycle** — creation, rotation, suspension, and revocation of agent identities (Section 8)
7. **Audit** — append-only event log for accountability (Section 9)

AIP is designed to complement existing protocols and standards:

- **Google A2A** — AIP identity in the agent card. Agents verify each other via AIP before task delegation.
- **Anthropic MCP** — AIP capabilities map to MCP tool permissions. MCP servers verify connecting agents via AIP challenge-response.
- **OpenID Connect** — AIP agent tokens extend OAuth 2.0 for machine-to-machine authentication.
- **WebAuthn/FIDO2** — AIP key storage can use hardware authenticators for high-assurance agent identity.
- **W3C Verifiable Credentials** — AIP trust scores expressed as VCs for cross-platform portability.
- **ATP (Agent Trust Protocol)** — AIP provides identity; ATP provides ecosystem-wide trust verification. They're complementary layers.

This specification defines the protocol. The OpenA2A AIM platform (`github.com/opena2a-org/agent-identity-management`) is the reference implementation.

---

## 1. Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

| Term | Definition |
|------|-----------|
| **Agent** | An AI system that performs actions on behalf of a user or another agent |
| **Identity Provider** | A server that creates and manages agent identities |
| **Relying Party** | A system that verifies an agent's identity before granting access |
| **Capability** | A permission declared in `namespace:action` format |
| **Trust Score** | A 0.0-1.0 value computed from multiple behavioral and provenance signals |
| **Governance Policy** | Constraints on agent behavior (what it MUST and MUST NOT do) |
| **Audit Log** | Append-only record of agent actions and verification events |

---

## 2. Conformance Levels

### Level 1: Local Identity

Agent identity created and managed locally (SDK, CLI). No server required. Suitable for individual developers.

Requirements:
- Ed25519 keypair generation (Section 3.1)
- Local identity file (Section 3.3)
- Local audit log (Section 9.1)
- Capability declaration (Section 4.1)

### Level 2: Managed Identity

Agent identity managed by an identity provider. Adds verification, trust scoring, and centralized audit. Suitable for organizations.

Requirements:
- All Level 1 requirements
- Challenge-response verification (Section 5)
- Trust scoring (Section 6)
- Server-side audit log (Section 9.2)
- API key or JWT authentication (Section 5.4)
- Drift detection (Section 8.4)

### Level 3: Federated Identity

Agent identity verifiable across organizations. Adds DID resolution, verifiable credentials, and cross-platform trust. Suitable for ecosystem-wide deployment.

Requirements:
- All Level 2 requirements
- DID-based agent identifiers (Section 3.2)
- Verifiable Credential trust assertions (Section 6.4)
- Cross-platform capability negotiation (Section 4.3)
- ATP integration for ecosystem trust (Section 6.5)

### 2.1 Relationship to A2A-IDF identity levels

AIP's `Local`, `Managed`, and `Federated` conformance levels describe *deployment topology* (what infrastructure operates the agent identity). The A2A Identity Trust Framework (A2A-IDF, `a2aproject/A2A#1496`) defines a separate three-level taxonomy of `SELF_ASSERTED`, `DOMAIN_VERIFIED`, and `ORGANIZATION_VERIFIED` that describes *provenance of identity binding* (how the identity claim was verified at discovery time). Both taxonomies apply independently to the same agent. A `Local` AIP agent may be `SELF_ASSERTED` or `DOMAIN_VERIFIED` under A2A-IDF; a `Managed` AIP agent may be `DOMAIN_VERIFIED` or `ORGANIZATION_VERIFIED`; a `Federated` AIP agent may be `DOMAIN_VERIFIED` or `ORGANIZATION_VERIFIED`. AIP conformance does not constrain A2A-IDF level assignment and vice versa.

---

## 3. Agent Identity

### 3.1 Cryptographic Identity

Every agent MUST have an Ed25519 keypair (RFC 8032).

```
Private key: 64 bytes (generated via crypto/rand)
Public key:  32 bytes (derived from private key)
Agent ID:    "aim_" + first 8 hex chars of SHA-256(public_key)
```

Example:
```
Agent ID:    aim_7f3a9c2e
Public Key:  ed25519:x8Kp2mN...4RqW (base64)
```

Implementations SHOULD also support hybrid Ed25519 + ML-DSA-65 (FIPS 204) for post-quantum readiness:

```
Classical key:     Ed25519 (32-byte pub, 64-byte priv)
Post-quantum key:  ML-DSA-65 (1,952-byte pub, 4,032-byte priv)
Hybrid signature:  Ed25519 sig (64 bytes) + ML-DSA-65 sig (3,309 bytes)
```

Both keys are generated simultaneously. Classical-only verifiers check the Ed25519 signature. Quantum-aware verifiers check both.

### 3.2 Decentralized Identifier (DID)

At Level 3, agents are identified by DIDs conforming to W3C DID Core. AIP uses the unified `did:opena2a` method shared with ATP (Agent Trust Protocol) and ATX (Agent Trust eXtension):

```
did:opena2a:<type>:<id>
```

Where `<type>` is one of the registered type prefixes: `agent`, `authority`, `publisher`, `mcp_server`, `a2a_agent`, `skill`, `ai_tool`, `llm`. For agent identities at AIP Level 3, the type is `agent`.

Example:
```
did:opena2a:agent:aim_7f3a9c2e
```

The DID Document includes the agent's public keys, capabilities, and service endpoints:

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1"
  ],
  "id": "did:opena2a:agent:aim_7f3a9c2e",
  "controller": "did:opena2a:authority:org_acme",
  "verificationMethod": [{
    "id": "did:opena2a:agent:aim_7f3a9c2e#key-1",
    "type": "Ed25519VerificationKey2020",
    "controller": "did:opena2a:agent:aim_7f3a9c2e",
    "publicKeyMultibase": "z6Mkf5rGMoatrSj1f..."
  }],
  "capabilityInvocation": ["#key-1"],
  "service": [{
    "id": "#identity-provider",
    "type": "AgentIdentityProvider",
    "serviceEndpoint": "https://aim.example.com"
  }]
}
```

### 3.3 Identity File Format

Local identities are stored in a standard directory structure:

```
~/.opena2a/aim-core/
  identities/
    my-agent.json        # Agent identity
  audit.jsonl            # Append-only audit log
```

Identity file format:

```json
{
  "id": "aim_7f3a9c2e",
  "name": "my-agent",
  "type": "claude",
  "publicKey": "ed25519:x8Kp2mN...4RqW",
  "encryptedPrivateKey": "aes-256-gcm:...",
  "capabilities": ["file:read", "api:call"],
  "createdAt": "2026-03-22T10:00:00Z",
  "status": "verified"
}
```

Private keys MUST be encrypted at rest. The default encryption is AES-256-GCM with a key derived from the user's system keychain or a passphrase.

### 3.4 Agent Types

AIP defines a standard vocabulary for agent types:

| Type | Description |
|------|-----------|
| `claude` | Anthropic Claude-based agents |
| `gpt` | OpenAI GPT-based agents |
| `gemini` | Google Gemini-based agents |
| `langchain` | LangChain framework agents |
| `crewai` | CrewAI framework agents |
| `autogen` | Microsoft AutoGen agents |
| `semantic-kernel` | Microsoft Semantic Kernel agents |
| `mcp-server` | Model Context Protocol servers |
| `a2a-agent` | Agent-to-Agent protocol agents |
| `custom` | Custom implementation |

The type is informational. It MUST NOT be used for security decisions — an agent claiming to be `claude` is not verified as such by the type field alone.

---

## 4. Capabilities

### 4.1 Capability Format

Capabilities are expressed as `namespace:action` strings:

```
file:read          Read files from the filesystem
file:write         Write files to the filesystem
db:read            Read from databases
db:write           Write to databases
api:call           Make outbound API calls
network:listen     Listen on network ports
system:exec        Execute system commands
mcp:tool_use       Invoke MCP tools
data:pii_access    Access personally identifiable information
payment:process    Process financial transactions
```

### 4.2 Reserved Namespaces

The following namespaces are reserved and have standardized meanings:

| Namespace | Description | Risk Level |
|-----------|-----------|------------|
| `file` | Filesystem operations | Medium-High |
| `db` | Database operations | Medium-High |
| `api` | External API calls | Medium |
| `network` | Network operations | High |
| `system` | System-level operations | Critical |
| `mcp` | MCP protocol operations | Medium |
| `data` | Data access and handling | High |
| `payment` | Financial operations | Critical |
| `user` | User data operations | High |
| `agent` | Agent-to-agent operations | Medium |

Organizations MAY define custom namespaces prefixed with their domain:

```
acme.com/billing:charge
acme.com/internal:deploy
```

### 4.3 Capability Negotiation

When an agent connects to a service (MCP server, A2A agent, API), the service SHOULD:

1. Request the agent's declared capabilities
2. Compare against required capabilities for the requested operation
3. Reject the request if the agent lacks the required capability
4. Log the capability check result in the audit trail

```
Agent → Service: "I want to call tool X"
Service → Agent: "Tool X requires [file:read, api:call]. Your capabilities?"
Agent → Service: "My capabilities: [file:read, api:call, db:read]"
Service: Verify agent identity, check capability list, grant or deny
```

### 4.4 Capability Violations

When an agent attempts an action outside its declared capabilities, the identity provider MUST:

1. Record a `CapabilityViolation` event in the audit log
2. Apply a trust score penalty proportional to the violation severity
3. Optionally block the action (configurable per policy)

Violation severity levels:
- `low` — action attempted but not critical (trust penalty: -2%)
- `medium` — sensitive action attempted (trust penalty: -5%)
- `high` — dangerous action attempted (trust penalty: -10%)
- `critical` — system-level or financial action attempted (trust penalty: -20%)

---

## 5. Verification

### 5.1 Challenge-Response Protocol

Agent identity verification uses Ed25519 challenge-response:

```
1. Relying Party → Identity Provider:
   POST /api/v1/agents/{agentId}/challenge

2. Identity Provider → Relying Party:
   { "challenge": "random-32-bytes-base64", "expiresAt": "..." }

3. Relying Party → Agent:
   "Sign this challenge with your private key"

4. Agent → Relying Party:
   { "signature": "ed25519-signature-base64", "publicKey": "..." }

5. Relying Party verifies:
   - Signature valid for challenge + public key
   - Public key matches registered agent
   - Challenge not expired (5-minute window)
   - Nonce not reused
```

### 5.2 Protocol-Specific Verification

AIP defines verification flows for common protocols:

**MCP Verification:**
```
MCP Client connects to MCP Server
  → Server requests AIP challenge
  → Client signs with agent key
  → Server verifies against identity provider
  → Server checks client capabilities against required MCP tools
  → Connection accepted or rejected
```

**A2A Verification:**
```
Agent A wants to delegate task to Agent B
  → A includes signed AIP assertion in A2A message
  → B verifies A's identity and trust score
  → B checks A's capabilities include agent:delegate
  → B accepts or rejects delegation
```

### 5.3 Verification Events

Every verification attempt MUST be logged as a verification event:

```json
{
  "id": "evt_abc123",
  "agentId": "aim_7f3a9c2e",
  "protocol": "mcp",
  "verificationType": "identity",
  "status": "success",
  "signature": "base64...",
  "messageHash": "SHA256:...",
  "nonce": "base64...",
  "durationMs": 42,
  "driftDetected": false,
  "initiator": {
    "type": "agent",
    "name": "orchestrator-agent"
  },
  "timestamp": "2026-03-22T14:00:00Z"
}
```

### 5.4 Machine-to-Machine Authentication

For programmatic access, AIP supports:

- **API Keys** — SHA-256 hashed, stored server-side, base64-encoded for transport
- **JWT Bearer Tokens** — HMAC-SHA256 signed, 1-hour TTL, containing agent ID and organization ID
- **SDK Tokens** — scoped tokens for SDK operations (agent registration, verification)

JWT claims:

```json
{
  "sub": "user_123",
  "org": "org_456",
  "iss": "aim.example.com",
  "aud": "aim-api",
  "exp": 1711137600,
  "iat": 1711134000,
  "scope": "agent:read agent:write"
}
```

---

## 6. Trust Scoring

### 6.1 Multi-Factor Algorithm

AIP defines a 9-factor trust scoring algorithm. Each factor contributes a weighted score. The composite score is 0.0 (no trust) to 1.0 (full trust). Weights sum to 100.

| Factor | Weight | Input | Score Range |
|--------|--------|-------|-------------|
| **Verification status** | 25% | Signature verification success rate | 0.0-1.0 |
| **Uptime and availability** | 15% | Health check responsiveness | 0.0-1.0 |
| **Action success rate** | 15% | Action completion rate | 0.0-1.0 |
| **Security alerts** | 15% | Active security alerts (weighted by severity) | 0.0-1.0 |
| **Compliance** | 10% | Framework adherence (SOC 2, HIPAA, GDPR, etc.) | 0.0-1.0 |
| **Execution isolation** | 10% | Sandbox / process isolation posture | 0.0-1.0 |
| **Age and history** | 5% | Operational history | <7d: 0.3, 7-30d: 0.5, 30-90d: 0.75, 90d+: 1.0 |
| **Drift detection** | 3% | Behavioral consistency vs baseline | 0.0-1.0 |
| **User feedback** | 2% | Explicit trust ratings from humans | 0.0-1.0 |

```
trust_score = Σ (factor_weight * factor_score * confidence)
```

Where `confidence` is the data availability for each factor (0.0 = no data, 1.0 = sufficient data). Factors with no data are excluded and their weights redistributed proportionally.

**Reference implementation.** The 9-factor algorithm above is implemented in the AIM (Agent Identity Management) reference implementation as the `TrustCalculator` service. AIP §6.1 specifies the factor set, weights, and composition rule; AIP-conformant implementations MAY substitute their own per-factor scoring functions provided the factor set, weights, and 0.0-1.0 composite range remain unchanged. The AIM `TrustCalculator` is the named reference implementation for AIP §6.1 in OpenA2A's ecosystem.

### 6.2 Trust Levels

Trust scores map to discrete levels for policy decisions:

| Score Range | Level | Meaning |
|-------------|-------|---------|
| 0.0 - 0.2 | Blocked | Agent is compromised or malicious |
| 0.2 - 0.4 | Warning | Significant trust concerns |
| 0.4 - 0.6 | Limited | Restricted access, monitoring required |
| 0.6 - 0.8 | Standard | Normal operations |
| 0.8 - 1.0 | Elevated | High-trust operations (financial, PII) |

### 6.3 Trust Score History

Identity providers MUST maintain a trust score history with:
- Previous score, new score, delta
- Reason for change (verification, alert, drift, manual)
- Timestamp
- Actor who triggered the change

### 6.4 Verifiable Credential Expression

At Level 3, trust scores SHOULD be expressible as W3C Verifiable Credentials:

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://opena2a.org/credentials/v1"
  ],
  "type": ["VerifiableCredential", "AgentTrustCredential"],
  "issuer": "did:opena2a:authority:provider_opena2a",
  "issuanceDate": "2026-03-22T14:00:00Z",
  "expirationDate": "2026-03-23T14:00:00Z",
  "credentialSubject": {
    "id": "did:opena2a:agent:aim_7f3a9c2e",
    "trustScore": 0.82,
    "trustLevel": "standard",
    "capabilities": ["file:read", "api:call"],
    "verificationCount": 1847,
    "lastVerified": "2026-03-22T13:55:00Z"
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-03-22T14:00:00Z",
    "verificationMethod": "did:opena2a:authority:provider_opena2a#key-1",
    "proofPurpose": "assertionMethod",
    "proofValue": "z58DAdFfa9SkqZMVPxAQp..."
  }
}
```

### 6.5 ATP Integration

AIP trust scores feed into ATP (Agent Trust Protocol) for ecosystem-wide trust:

- AIP provides **behavioral trust** — how the agent acts in deployment
- ATP provides **provenance trust** — how the agent's code was built and scanned

Combined score:
```
ecosystem_trust = α * aip_behavioral_trust + β * atp_provenance_trust
```

Where α and β are configurable weights (default: α=0.5, β=0.5).

---

## 7. Governance

### 7.1 Policy Format

Agent governance policies are expressed in YAML:

```yaml
agent: aim_7f3a9c2e
policies:
  - name: "Require approval for file writes"
    capability: "file:write"
    action: "require_approval"
    approvers: ["user:admin@acme.com"]

  - name: "Block system commands"
    capability: "system:exec"
    action: "deny"

  - name: "Rate limit API calls"
    capability: "api:call"
    action: "rate_limit"
    limit: 100
    period: "1m"
```

### 7.2 Policy Actions

| Action | Behavior |
|--------|----------|
| `allow` | Permit without restriction |
| `deny` | Block unconditionally |
| `require_approval` | Queue for human approval before execution |
| `rate_limit` | Allow up to N invocations per period |
| `audit` | Allow but log for review |
| `notify` | Allow but send notification to specified parties |

### 7.3 SOUL Integration

AIP governance policies complement SOUL.md behavioral governance:

- **AIP policies** — technical enforcement (capabilities, rate limits, approvals)
- **SOUL policies** — behavioral governance (injection hardening, data handling, honesty)

An agent SHOULD have both: AIP policies enforced by the identity provider, SOUL policies enforced by the LLM runtime.

---

## 8. Lifecycle

### 8.1 States

```
Created → Pending → Verified → Active
                                  ↓
                              Suspended → Revoked
                                  ↓
                              Reactivated → Active
```

| State | Meaning |
|-------|---------|
| `created` | Identity generated, not yet verified |
| `pending` | Verification in progress |
| `verified` | Identity cryptographically verified |
| `active` | Operating normally |
| `suspended` | Temporarily disabled (policy violation, drift detected) |
| `revoked` | Permanently disabled (compromised, decommissioned) |

### 8.2 Key Rotation

Agents SHOULD rotate keys periodically. The rotation protocol:

1. Generate new keypair
2. Register new public key with identity provider
3. Grace period begins (configurable, default 7 days)
4. During grace period, both old and new keys are valid
5. After grace period, old key is retired

```json
{
  "agentId": "aim_7f3a9c2e",
  "currentKey": "ed25519:newKey...",
  "previousKey": "ed25519:oldKey...",
  "keyRotationGraceUntil": "2026-03-29T14:00:00Z"
}
```

### 8.3 Suspension and Revocation

An identity provider MUST support:

- **Suspension** — temporary, reversible. Triggers: policy violation, drift detection, manual action.
- **Revocation** — permanent, irreversible. Triggers: compromise confirmed, decommissioning.

Both MUST be logged in the audit trail with reason, actor, and timestamp.

### 8.4 Drift Detection

The identity provider SHOULD monitor for configuration drift:

- **Capability drift** — agent uses capabilities not in its registration
- **MCP drift** — agent connects to MCP servers not in its `talksTo` list
- **Behavioral drift** — action patterns diverge from historical baseline

When drift is detected:
1. Log a `drift_detected` event
2. Create a security alert (severity: high)
3. Apply trust score penalty (-5% first occurrence, -10% repeated)
4. Optionally suspend the agent (configurable per policy)

---

## 9. Audit

### 9.1 Local Audit Log

Level 1 implementations MUST maintain a local append-only audit log:

```
~/.opena2a/aim-core/audit.jsonl
```

Each line is a JSON event:

```json
{"type":"identity_created","agentId":"aim_7f3a9c2e","timestamp":"2026-03-22T10:00:00Z"}
{"type":"verification_success","agentId":"aim_7f3a9c2e","protocol":"mcp","durationMs":42,"timestamp":"2026-03-22T10:01:00Z"}
{"type":"capability_violation","agentId":"aim_7f3a9c2e","capability":"system:exec","severity":"critical","blocked":true,"timestamp":"2026-03-22T10:02:00Z"}
```

### 9.2 Server Audit Log

Level 2+ implementations MUST maintain a server-side audit log in an append-only data store.

Event types:

| Event | Description |
|-------|-----------|
| `identity_created` | New agent identity registered |
| `identity_verified` | Challenge-response verification completed |
| `identity_suspended` | Agent suspended |
| `identity_revoked` | Agent permanently revoked |
| `capability_granted` | Capability added to agent |
| `capability_revoked` | Capability removed from agent |
| `capability_violation` | Agent attempted unauthorized action |
| `trust_score_changed` | Trust score recalculated |
| `drift_detected` | Configuration drift found |
| `key_rotated` | Agent key rotation completed |
| `policy_evaluated` | Governance policy applied |
| `a2a_delegation` | Agent-to-agent task delegation |
| `mcp_connection` | Agent connected to MCP server |

---

## 10. Discovery

### 10.1 Well-Known Endpoint

An AIP identity provider MUST serve a discovery document at:

```
GET /.well-known/aip
```

```json
{
  "providerDid": "did:opena2a:authority:provider_opena2a",
  "version": "1.0",
  "conformanceLevel": 2,
  "endpoints": {
    "agents": "/api/v1/agents",
    "challenge": "/api/v1/agents/{agentId}/challenge",
    "verify": "/api/v1/agents/{agentId}/verify",
    "capabilities": "/api/v1/capabilities",
    "trustScore": "/api/v1/agents/{agentId}/trust",
    "audit": "/api/v1/agents/{agentId}/audit",
    "didResolve": "/api/v1/did/{did}"
  },
  "publicKey": {
    "algorithm": "Ed25519",
    "publicKeyMultibase": "z6Mkf5rGMoatrSj1f..."
  },
  "supportedAgentTypes": ["claude", "gpt", "gemini", "langchain", "crewai", "mcp-server", "a2a-agent"],
  "supportedCapabilityNamespaces": ["file", "db", "api", "network", "system", "mcp", "data", "payment"],
  "supportedProtocols": ["mcp", "a2a"]
}
```

---

## 11. Integration Patterns

### 11.1 Google Chrome — Browser Agent Identity

For agents running in the browser (Chrome extensions, web-based agents):

```
1. Agent creates identity using WebCrypto API (Ed25519)
2. Private key stored in IndexedDB (encrypted) or hardware key (WebAuthn)
3. Agent card published at /.well-known/agent.json with AIP identity
4. When user installs agent, Chrome verifies AIP trust score
5. Agent capabilities enforced by extension permissions model
```

AIP maps to Chrome's existing permission model:
- `file:read` → Chrome `fileSystem` permission
- `network:listen` → Chrome `webRequest` permission
- `api:call` → Chrome `fetch` permission

### 11.2 MCP Server Integration

```
MCP Server starts up
  → Registers AIP identity with provider
  → Declares capabilities: mcp:tool_use, file:read
  → MCP Client connects
  → Server challenges client for AIP identity
  → Client signs challenge
  → Server verifies identity + capabilities
  → Client can only invoke tools matching its capabilities
```

### 11.3 A2A Agent-to-Agent

```
Agent A wants to delegate to Agent B
  → A looks up B's AIP identity (DID resolution)
  → A verifies B's trust score (via ATP or direct)
  → A includes signed delegation token in A2A message
  → B verifies A's identity and delegation authority
  → B executes task within its own capability boundaries
  → Both agents log the interaction in their audit trails
```

### 11.4 CI/CD Pipeline

```yaml
- name: Register agent identity
  run: npx opena2a-cli identity create --name deploy-agent --type custom

- name: Verify agent before deployment
  run: |
    npx opena2a-cli identity verify --name deploy-agent
    npx opena2a-cli identity check-trust --name deploy-agent --min-score 0.7
```

---

## 12. Security Considerations

### 12.1 Key Storage

Private keys MUST be encrypted at rest. Implementations SHOULD support:
- System keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- Hardware security keys (WebAuthn/FIDO2)
- HSM integration for server deployments

Private keys MUST NEVER be transmitted in plaintext. The identity provider stores only public keys.

### 12.2 Replay Attacks

Challenge-response verification MUST use single-use nonces with a maximum validity of 5 minutes. Nonces MUST NOT be reusable.

### 12.3 Capability Escalation

An agent MUST NOT be able to grant itself capabilities it doesn't have. Capability changes MUST be authorized by the identity provider or an administrator.

### 12.4 Trust Score Manipulation

Trust scores MUST be computed server-side. Agents MUST NOT be able to self-report trust scores. All inputs to the trust calculation MUST be independently verifiable (verification events, uptime checks, audit logs).

---

## 13. IANA Considerations

- **DID Method:** `did:opena2a` (shared across AIP, ATP, and ATX). Decentralized Identifier method for AI agent identity, with registered type prefixes `agent`, `authority`, `publisher`, `mcp_server`, `a2a_agent`, `skill`, `ai_tool`, `llm`.
- **Well-Known URI:** `/.well-known/aip`. Identity provider discovery.
- **Capability Namespace Registry:** Standard capability namespaces (file, db, api, network, system, mcp, data, payment, user, agent).

---

## 14. References

- RFC 2119 — Key words for use in RFCs
- RFC 8032 — Edwards-Curve Digital Signature Algorithm (Ed25519)
- RFC 7519 — JSON Web Token (JWT)
- W3C DID Core — Decentralized Identifiers v1.0
- W3C Verifiable Credentials — Verifiable Credentials Data Model v2.0
- WebAuthn Level 3 — Web Authentication API
- FIPS 204 — Module-Lattice-Based Digital Signature Standard (ML-DSA)
- Google A2A Protocol — Agent-to-Agent communication
- Anthropic MCP — Model Context Protocol
- OpenID Connect Core 1.0

---

## Appendix A: Reference Implementation

The OpenA2A AIM platform (`github.com/opena2a-org/agent-identity-management`) is the reference implementation at Conformance Level 2.

| Component | Implementation |
|-----------|---------------|
| Ed25519 identity | `apps/backend/internal/crypto/keygen.go` |
| Hybrid PQC signing | `apps/backend/internal/crypto/pqc/hybrid.go` |
| Agent lifecycle | `apps/backend/internal/application/agent_service.go` |
| Trust scoring (9-factor reference) | `apps/backend/internal/application/trust_calculator.go` |
| Capability enforcement | `apps/backend/internal/application/capability_service.go` |
| Drift detection | `apps/backend/internal/application/drift_detection_service.go` |
| MCP verification | `apps/backend/internal/application/mcp_service.go` |
| A2A verification | `apps/backend/internal/application/a2a_service.go` |
| Registry bridge | `apps/backend/internal/application/registry_bridge_service.go` |
| TypeScript SDK | `sdk/typescript/src/` |

### A.1 Spec sections currently implemented by AIM

The reference implementation's coverage is uneven and the gaps are tracked publicly here. Any cross-implementation pitch should scope claims to the rows marked Shipped.

| AIP / AIP-adjacent section | AIM status | Notes |
|---|---|---|
| §3 Agent Identity (Ed25519 keypair, agent ID, DID) | Shipped | `crypto/keygen.go`, `domain/agent.go`. Server-side key generation; agent receives Ed25519 public key registered on its record. |
| §3 Hybrid PQC signing (Ed25519 + ML-DSA-65) | Shipped end to end on the registry path | Registry-side `ATCService.IssueATC()` at `opena2a-registry/internal/application/atc_service.go` emits hybrid signatures in production: threshold Ed25519 plus one ML-DSA-65 signature from the hybrid keypair wired in at `cmd/server/main.go:682-685` (startup log: "ATC post-quantum hybrid signing enabled (Ed25519 + ML-DSA-65)"). The ML-DSA-65 signature `Value` is the raw 3309-byte `mldsa65.SignatureSize` blob as of opena2a-registry PR #215 (prior credentials carried a legacy combined Ed25519+ML-DSA blob; ATC TTL is 7 days, so the rollover is naturally complete one week after PR #215 ships). The standalone offline-verify package `opena2a-registry/pkg/atcverify` enforces the hybrid signing mandate as of opena2a-registry PR #214: when a credential declares an ML-DSA-65 signature, at least one ML-DSA-65 signature must verify in addition to at least one Ed25519 signature. A parallel AIM-side CBOR issuer (`agent-identity-management/apps/backend/internal/infrastructure/atc/atc_issuer.go` `RealATCIssuer`) signs Ed25519 only and has no active production callers today. |
| §4 Capabilities | Shipped | `application/capability_service.go`, FGA engine at `application/fga_engine.go` with 5-step blocking enforcement (capability, attribute, context, chain, intent). |
| §4 JIT capability grants with TTL | Partial | TTL exists for PAM (Privileged Access Management) emergency-escalation grants. Routine capability grants are static. |
| §5 Verification (challenge-response) | Shipped | `/authorize` endpoint exists; direct SDK callers are pending. |
| §6 Trust Scoring (9-factor) | Shipped | `application/trust_calculator.go`, reference algorithm with audited weights. |
| §6.5 ATP integration | Not yet integrated | ATP-SPEC v1.0.0-rc1 is recent; cross-wiring of AIP trust scores into ATP transparency log is upcoming work. |
| §9 Audit (append-only) | Shipped, not cryptographically signed | `repository/audit_log_repository.go` enforces append-only at the repository layer. Hash-chain or signed-log fields (`signature`, `hash`, `previous_hash`) are not present; integrity relies on database-level access control today. |
| Local offline verification | Go only in the SDK layer; Go plus Python in the conformance suite | Standalone offline-verify package exists at the registry's `pkg/atcverify` (Go, full hybrid). TypeScript, Python, and Java AIM SDKs do not yet ship a local-verify library. The [`opena2a-org/atx-conformance`](https://github.com/opena2a-org/atx-conformance) suite ships an additional SDK-independent Python reference verifier (Ed25519 only; ML-DSA-65 verification out of scope for the Python stdlib stack) and a Go reference verifier with full Ed25519 plus ML-DSA-65 coverage. Both validate the same byte-stable fixture set and demonstrate that the wire format is implementable in a second language without an SDK dependency. |

Note on runtime self-attestation and protocol-enforcement: AIP does not specify a runtime self-attestation layer (that surface belongs to ATX core §5 and the ARC runtime layer, not AIP). For ecosystem context: OpenA2A's reference implementation of the runtime layer ships today as a first-party module inside HMA (`hackmyagent/src/arp/`), not yet inside AIM. AIM-side integration is on the AIM roadmap as a separate track.

## Appendix B: Relationship to ATP

AIP and ATP are complementary protocols:

```
AIP (Agent Identity Protocol)          ATP (Agent Trust Protocol)
  "Who is this agent?"                   "Should I trust this agent's code?"
  Identity, capabilities, governance     Provenance, supply chain, scanning
  Behavioral trust (how it acts)         Code trust (how it was built)
  Per-organization                       Ecosystem-wide

          ↓ feeds into ↓                        ↓ feeds into ↓
                    Combined Trust Decision
                    "Is this agent safe to use?"
```

An agent with a strong AIP identity (verified, high trust score, clean audit log) but weak ATP score (unscanned code, no provenance) is a well-behaved agent running unverified code.

An agent with a strong ATP score (scanned code, SLSA provenance, federation-verified) but weak AIP identity (no verification history, capability violations) is verified code running in an uncontrolled environment.

Both are needed for a complete trust decision.
