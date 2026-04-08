## Step 5: Evaluate Coverage

| Sub-question | Sources | Quality |
|---|---|---|
| MCP architecture & primitives | Primary spec (2025-11-25), official docs, Wikipedia | ✅ Strong |
| A2A architecture & Agent Cards | a2a-protocol.org spec, GitHub README | ✅ Strong |
| A2A v1.0 changes | Official what's-new page | ✅ Strong |
| Auth models (both) | MCP: OAuth 2.1 spec page + Aembit/Auth0; A2A: spec Section 4.5 | ✅ Strong |
| Adoption numbers | MCP: mcpmanager.ai, zuplo report, medium stats; A2A: GitHub + announcements | ✅ Adequate |
| Complementary vs competing | Google dev guide, merge.dev, composio | ✅ Strong |

**3 rounds sufficient.** Proceeding to synthesis.

---

# A2A vs. MCP: A Protocol-Layer Analysis

**Thesis:** MCP and A2A are non-competing, layer-distinct protocols — MCP standardizes the *model↔tool* interface, A2A standardizes *agent↔agent* coordination — but as both mature, capability overlap is growing and convergence pressure is real.

---

## 1. Architecture: What Each Protocol Actually Does

### MCP (Model Context Protocol)
*Anthropic, November 2024. Current spec: 2025-11-25. Donated to Linux Foundation/AAIF, December 2025.*

MCP is a **vertical integration protocol** — it connects an AI model running in a host application down to external tools, data sources, and prompts. The topology is:

```
Host Application (Claude Desktop, VS Code, IDE)
    └── MCP Client (connector)
            ├── MCP Server A → Tools (functions LLM executes)
            ├── MCP Server B → Resources (data/files in context)
            └── MCP Server C → Prompts (user-controlled templates)
```

The inspiration is explicit: MCP borrows from the Language Server Protocol (LSP) — the same way LSP decoupled language intelligence from any particular editor, MCP decouples tool/data access from any particular AI system. Transport is JSON-RPC 2.0 over two mechanisms: **stdio** (local process, low-latency for dev tooling) and **HTTP + SSE** (remote, for production server deployments).

**Six first-class primitives in the 2025-11-25 spec:**

| Primitive | Controller | What it is |
|---|---|---|
| **Tools** | Model-controlled | Functions the LLM calls (search, write file, query DB) |
| **Resources** | App-controlled | Data exposed to context (files, DB records, live feeds) |
| **Prompts** | User-controlled | Reusable message templates and workflows |
| **Sampling** | Client feature | Server requests LLM inference mid-operation |
| **Roots** | Client feature | Constrains which filesystem paths/URIs server can access |
| **Elicitation** | Client feature | Server requests additional input from user |

The **Sampling** primitive deserves particular attention: it allows an MCP server to initiate LLM calls back through the client, enabling recursive/agentic behavior *within* one session. This is MCP's closest analog to multi-agent behavior — but it's intra-session, not cross-system.

**Auth:** MCP adopted **OAuth 2.1 with PKCE** as its authorization model (June 2025 spec update, per Auth0/MarkTechPost). Servers act as OAuth 2.1 resource servers; MCP clients are OAuth 2.1 clients. Key mandates: Authorization Code flow + PKCE (RFC 7636), Protected Resource Metadata via RFC 9728, Resource Indicators via RFC 8707 to prevent token misuse across servers. A notable security constraint: MCP servers are *explicitly prohibited* from passing through tokens to upstream APIs (prevents confused deputy attacks).

---

### A2A (Agent-to-Agent Protocol)
*Google, announced April 2025. v1.0.0 released March 12, 2026. Apache 2.0, Linux Foundation.*

A2A is a **horizontal coordination protocol** — it lets independent, potentially opaque AI agents discover each other, delegate work, and track long-running tasks across organizational boundaries. No agent needs to see another's internal state, memory, or tools.

```
Orchestrator Agent
    ├── A2A Client → [Agent Card Discovery] → Remote Agent A (pricing)
    │                                         Remote Agent B (quality)
    └── MCP Client → PostgreSQL (inventory)
```

Google's own reference implementation uses *both simultaneously*: A2A to route queries to specialist agents, MCP to access structured databases.

**Core objects:**

**Agent Card** — published at `/.well-known/agent-card.json`. Contains: `id`, `name`, `description`, `version`, `AgentProvider`, `AgentCapabilities`, `skills[]`, `interfaces[]`, `securitySchemes`, `security[]`, `extensions[]`. In v1.0, signed via JWS (RFC 7515) + JCS canonicalization (RFC 8785), enabling cryptographic verification of agent identity before any interaction.

**Task lifecycle** — 8 states:
```
UNSPECIFIED → WORKING → INPUT_REQUIRED → AUTH_REQUIRED
                      → COMPLETED (terminal)
                      → FAILED (terminal)
                      → CANCELED (terminal)
                      → REJECTED (terminal)
```
`INPUT_REQUIRED` and `AUTH_REQUIRED` are structurally important: they model human-in-the-loop and authorization gates as first-class task states, not exceptions.

**Transport:** HTTP/JSON-RPC 2.0 + SSE (streaming). **v1.0 added full gRPC support**, with `a2a.proto` elevated to normative source of truth for all protocol bindings. Equivalence guarantees between JSON-RPC, gRPC, and HTTP/REST bindings.

**Auth — 6 schemes** (per Section 4.5 of spec):
1. APIKeySecurityScheme
2. HTTPAuthSecurityScheme (Basic/Bearer)
3. OAuth2SecurityScheme (Auth Code, Client Credentials, Device Code / RFC 8628, with PKCE required)
4. OpenIdConnectSecurityScheme (OIDC discovery)
5. MutualTlsSecurityScheme (mTLS certificate pinning)

v1.0 explicitly removed deprecated OAuth flows: Implicit flow and Password flow removed per OAuth 2.0 Security BCP. Added `pkce_required` field on Authorization Code flow.

---

## 2. Problem Space: What Each Uniquely Solves

### What A2A solves that MCP doesn't

| Problem | A2A's solution | MCP's gap |
|---|---|---|
| **Runtime agent discovery** | Agent Cards at well-known URLs; capability advertised, no redeployment to add agents | No standard agent registry; tools are enumerated at connection time |
| **Long-running async tasks** | Full task lifecycle with polling (`GetTask`), streaming (`SubscribeToTask`), push webhooks | Tool calls are synchronous request/response; no native task state |
| **Opaque agent delegation** | Delegate to agent you can't inspect — no access to internal state, memory, tools | MCP requires knowing the tool schema; not designed for black-box agents |
| **Cross-org agent trust** | Signed Agent Cards (JWS+JCS) establish cryptographic identity before interaction | No equivalent agent identity primitive |
| **Multi-tenancy** | v1.0: `tenant` field in all gRPC requests; single endpoint serves multiple logical agents | N/A — no tenancy concept |
| **Agent-level auth gates** | `AUTH_REQUIRED` task state pauses workflow pending authorization | Auth is an MCP server concern, not a protocol-level task state |
| **Human-in-the-loop** | `INPUT_REQUIRED` state is a protocol primitive | No protocol-level pause-for-human mechanism |
| **Peer agent topology** | Agents can be peers (no hierarchy required) | Client → Server hierarchy is fixed |

### What MCP solves that A2A doesn't

| Problem | MCP's solution | A2A's gap |
|---|---|---|
| **Tool/function standardization** | 14,000+ servers, any model can call any MCP tool | A2A describes agent capabilities, not individual function signatures |
| **Context injection** | Resources as first-class primitive — push files, DB rows, live feeds into LLM context | No equivalent; A2A passes messages between agents, not structured context |
| **Prompt reuse** | Prompts primitive: templated, reusable message workflows | No prompt management layer |
| **Bidirectional inference** | Sampling: server-initiated LLM calls back through the client | A2A is one-direction delegation; no model sampling primitive |
| **Local process integration** | stdio transport for zero-latency IDE/developer tooling | HTTP-only; no local IPC |
| **Broad model compatibility** | Adopted by OpenAI (March 2025), Google (Gemini 2.5 Pro), Anthropic, 14k servers | 50 enterprise partners; primarily Google Cloud ecosystem |
| **Elicitation** | Server can request additional info from users mid-operation | No equivalent; A2A's `INPUT_REQUIRED` routes through task lifecycle, not direct user elicitation |
| **Token security scoping** | Resource Indicators (RFC 8707): tokens scoped to specific MCP server | Tokens scoped at agent card level; less granular resource binding |

---

## 3. Current Adoption

### MCP
- **14,000+ servers** across all registries (early 2026); ~5,500 in PulseMCP registry alone
- **300 MCP clients** indexed
- **97 million** combined Python + TypeScript SDK downloads/month (December 2025)
- Remote server deployment up **~400%** since May 2025
- SDK downloads grew from ~100k/month (Nov 2024) to **8 million/month** (April 2025)
- **OpenAI adopted** March 2025 (Agents SDK, Responses API, ChatGPT Desktop)
- **Google adopted** natively in Gemini 2.5 Pro API and SDK
- **Governance transfer**: December 2025, donated to **Agentic AI Foundation (AAIF)** under Linux Foundation, co-founded by Anthropic, Block, and OpenAI; backed by AWS, Google, Microsoft, Salesforce, Snowflake
- Gartner projects: 75% of API gateway vendors and 50% of iPaaS vendors will have MCP features by 2026

### A2A
- **50+ technology partners** at launch: Atlassian, Box, Cohere, Intuit, LangChain, MongoDB, PayPal, Salesforce, SAP, ServiceNow, Workday
- **23,100 GitHub stars**, 2,300 forks (as of research date)
- **SDKs**: Python, Go, JavaScript, Java, .NET
- **v1.0.0**: March 12, 2026 — first production-stable release
- Governance: Apache 2.0, Linux Foundation (same umbrella as MCP)
- Google Cloud native integration, Google Agent Engine support

---

## 4. Complementary or Competing?

**Short answer: Complementary by design, with growing overlap pressure.**

**The clearest evidence for complementarity** is Google's own reference architecture. In the [Developer's Guide to AI Agent Protocols](https://developers.googleblog.com/developers-guide-to-ai-agent-protocols/), a single kitchen manager agent uses:
- **MCP** to query a PostgreSQL inventory database
- **A2A** to route queries to remote pricing and quality specialist agents

These aren't alternatives for the same job — they're different layers. MCP handles vertical data access (agent→tool), A2A handles horizontal coordination (agent→agent).

**Governance alignment confirms non-competition**: Both protocols now sit under the Linux Foundation umbrella. MCP via AAIF (December 2025); A2A directly under Linux Foundation (Apache 2.0). Google is listed as a backer of AAIF even while building A2A. This isn't two companies racing to own the protocol layer — it's an industry converging on layered standards.

**The growing overlap areas to watch:**

| Tension point | Specifics |
|---|---|
| **Skills vs. Tools** | A2A's `AgentSkill` in the Agent Card describes what an agent can do — structurally similar to MCP's `Tool` schema. As A2A matures, "discover-and-call an agent skill" starts to resemble "discover-and-call an MCP tool" |
| **MCP Sampling vs. A2A delegation** | MCP's Sampling primitive enables server-initiated LLM inference through the client — a form of agent-like behavior that could handle some intra-system cases A2A targets |
| **Auth convergence** | Both now use OAuth 2.1 + PKCE. A2A has more auth flexibility (5 schemes + mTLS); MCP has more precise token scoping (RFC 8707 Resource Indicators). Neither has adopted the other's approach |
| **Long-running tasks** | MCP's `Progress` notifications and `Cancellation` utilities handle some of what A2A's Task lifecycle does — but not the full state machine (no INPUT_REQUIRED, AUTH_REQUIRED in MCP) |

**Verdict**: The protocols are complementary *today*. Convergence is possible within 2-3 years if the Linux Foundation umbrella governance leads to a unified agentic communication spec. The most likely scenario isn't replacement but **layering** — A2A becomes the inter-agent routing layer, MCP becomes the tool/context injection layer, and a future spec may define how the two handoff cleanly.

---

## 5. Source Conflicts & Open Questions

### Conflicts
| Claim | Source A | Source B | Assessment |
|---|---|---|---|
| A2A version | GitHub README cites v1.0.0 (Mar 12, 2026) | Some articles reference v0.3 as latest | v1.0.0 is correct per official a2a-protocol.org |
| MCP servers count | MCP Manager: 14k across registries | PulseMCP: 5,500 | Both correct — PulseMCP is one registry; 14k is aggregate |
| Google's MCP support | "Google added native MCP support in Gemini 2.5 Pro" | A2A positioned as Google's agent protocol | Not a conflict — Google supports both |

### Open Questions (not resolved despite searching)
- No public data on A2A production deployment volume (GitHub stars are a proxy, not traffic)
- MCP auth spec (June 2025) predates the AAIF transfer — unclear if AAIF will maintain, extend, or revise auth requirements
- No independent benchmark of A2A task reliability under real multi-agent workloads
- The A2A spec's `extensions[]` mechanism allows arbitrary protocol extensions — no registry of which extensions are in use in production

---

## Sources

- [Anthropic: Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol) — Anthropic, Nov 2024
- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — modelcontextprotocol.io
- [MCP Authorization Specification](https://modelcontextprotocol.io/specification/draft/basic/authorization) — modelcontextprotocol.io
- [Google Developers: Announcing the Agent2Agent Protocol](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) — Google, Apr 2025
- [Developer's Guide to AI Agent Protocols](https://developers.googleblog.com/developers-guide-to-ai-agent-protocols/) — Google
- [A2A Protocol Specification](https://a2a-protocol.org/latest/specification/) — a2a-protocol.org
- [What's New in A2A v1.0](https://a2a-protocol.org/latest/whats-new-v1/) — a2a-protocol.org, Mar 2026
- [A2A GitHub Repository](https://github.com/a2aproject/A2A) — a2aproject, Apache 2.0
- [MCP vs A2A — Auth0 Guide](https://auth0.com/blog/mcp-vs-a2a/) — Auth0
- [MCP vs A2A — DigitalOcean](https://www.digitalocean.com/community/tutorials/a2a-vs-mcp-ai-agent-protocols) — DigitalOcean
- [MCP Adoption Statistics 2025](https://mcpmanager.ai/blog/mcp-adoption-statistics/) — MCP Manager
- [The State of MCP Report](https://zuplo.com/mcp-report) — Zuplo (292-developer survey)
- [MCP OAuth 2.1 and PKCE](https://aembit.io/blog/mcp-oauth-2-1-pkce-and-the-future-of-ai-authorization/) — Aembit
- [MCP Spec Updates June 2025 — All About Auth](https://auth0.com/blog/mcp-specs-update-all-about-auth/) — Auth0
- [A2A Protocol Getting an Upgrade](https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade) — Google Cloud Blog
- [IBM: What Is Agent2Agent Protocol](https://www.ibm.com/think/topics/agent2agent-protocol) — IBM
- [Understanding OAuth 2.1 for MCP Servers](https://www.marktechpost.com/2025/08/31/understanding-oauth-2-1-for-mcp-model-context-protocol-servers-discovery-authorization-and-access-phases/) — MarkTechPost
- [A Year of MCP: 2025 Review](https://www.pento.ai/blog/a-year-of-mcp-2025-review) — Pento
- [MCP vs A2A vs ACP — 2026](https://bonjoy.com/articles/mcp-vs-a2a-vs-acp-agent-protocols-compared/) — Bonjoy
