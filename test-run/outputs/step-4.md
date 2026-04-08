## Step 5: Coverage Assessment

All six sub-questions now have strong coverage (3+ quality primary sources each). Proceeding to synthesis.

---

---

# A2A vs. MCP: A Protocol-Level Analysis

**Thesis:** MCP and A2A are architecturally complementary and operate at different layers of the agentic stack — MCP connects a single agent to external tools and data; A2A connects autonomous agents to each other. Most production multi-agent systems will need both.

---

## 1. Architecture: What Each Protocol Actually Is

### MCP (Model Context Protocol)

**Origin:** Anthropic, November 2024. Donated to the Agentic AI Foundation (Linux Foundation) in December 2025. Governing members include Anthropic, OpenAI, Block, AWS, Google, Microsoft, Cloudflare, and Bloomberg (Anthropic, 2025).

**Transport:** JSON-RPC 2.0, explicitly inspired by the Language Server Protocol (LSP). The MCP spec notes: "In a similar way, MCP standardizes how to integrate additional context and tools into the ecosystem of AI applications" (MCP Specification, 2025-11-25).

**Roles — three-tier architecture:**

| Role | Responsibility |
|------|---------------|
| **Host** | The container process (e.g., Claude Desktop, Cursor, VS Code Copilot). Manages multiple clients, enforces security policies, coordinates LLM sampling, handles user authorization. |
| **Client** | A 1:1 connector created by the host for each server. Handles protocol negotiation, routes messages bidirectionally, maintains security isolation between servers. |
| **Server** | Exposes focused capabilities. Cannot read full conversation history, cannot "see into" other servers — isolation is a hard design principle. |

**The six core primitives** split along control model:

*Server-side (what servers expose):*
- **Tools** — model-controlled. Functions the LLM decides to call (e.g., `run_query`, `send_email`).
- **Resources** — app-controlled. Context data the host application surfaces (e.g., current file, database schema).
- **Prompts** — user-controlled. Templated workflows users explicitly invoke.

*Client-side (what clients expose to servers):*
- **Sampling** — servers can request that the host make an LLM inference call on their behalf. This is a deep inversion: the tool can ask the model to reason. The message flow is `Server → Client → Host (LLM) → Client → Server`.
- **Roots** — servers can query filesystem/URI boundaries they're allowed to operate within.
- **Elicitation** — servers can request mid-session human input via `elicitation/create` requests (added in the 2025-06-18 spec update).

**Capability negotiation:** Every MCP session begins with an `initialize` handshake where both sides declare their supported features. A server that hasn't declared `tools` cannot have its tools invoked; a client without `sampling` capability will reject sampling requests. This prevents silent failures.

**Authentication (latest spec):** MCP servers are classified as OAuth 2.0 Resource Servers. Clients must include a `resource` parameter per RFC 8707 when requesting tokens, explicitly binding each access token to a specific MCP server (MCP Specification, 2025-11-25).

---

### A2A (Agent2Agent Protocol)

**Origin:** Google, April 2025, with 50+ initial partners (Atlassian, Box, Cohere, Intuit, LangChain, MongoDB, PayPal, Salesforce, SAP, ServiceNow, UKG, Workday). v1.0 (production-stable) governance via an 8-member Technical Steering Committee: AWS, Cisco, Google, IBM Research, Microsoft, Salesforce, SAP, ServiceNow (A2A Protocol, 2025).

**Transport:** Three protocol bindings with functional equivalence across all three:
1. **JSON-RPC 2.0** — primary binding
2. **gRPC** — added in v0.3 (mid-2025), with bidirectional streaming support
3. **HTTP+JSON/REST** — RESTful endpoints with SSE or WebSocket for streaming

**Core abstraction — the "opaque agent":** A2A is explicitly designed for agents that do *not* share their internal memory, tools, or context. The Google announcement states the protocol enables "collaboration without requiring shared memory, tools, or context" (Google Developers Blog, 2025). This is the foundational design distinction from MCP: you don't need to know how the other agent works — only what it can do and how to ask it.

**The Agent Card** — published at `/.well-known/agent-card.json`:
```json
{
  "name": "Pricing Agent",
  "provider": "Acme Corp",
  "endpoint": "https://pricing.example.com/a2a",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  },
  "skills": [...],
  "securitySchemes": {...}
}
```
As of v0.3, cards can be digitally signed via JSON Web Signature (JWS) for cryptographic verification of agent identity (Google Cloud Blog, 2025).

**Task lifecycle — 7 states:**

```
submitted → working → {completed | failed | canceled | rejected}
                  ↕
            input-required
                  ↕
            auth-required
```

Tasks are stateful, persistent objects with unique IDs. They are the fundamental unit of work — unlike MCP's stateless tool calls, an A2A task can run for hours or days.

**The 11 primary operations:**

| Operation | Description |
|-----------|-------------|
| `SendMessage` | Initiate interaction; blocking or non-blocking via `returnImmediately` flag |
| `SendStreamingMessage` | Initiate with real-time SSE updates |
| `GetTask` | Retrieve current task state |
| `ListTasks` | Discovery with filtering/pagination |
| `CancelTask` | Idempotent cancellation |
| `SubscribeToTask` | Establish streaming subscription to existing task |
| `CreatePushNotificationConfig` | Register webhook URL |
| `GetPushNotificationConfig` | Retrieve webhook config |
| `ListPushNotificationConfigs` | List all webhook configs |
| `DeletePushNotificationConfig` | Remove webhook |
| `GetExtendedAgentCard` | Authenticated fetch for role-specific capabilities |

**Asynchronous delivery — three patterns:**
1. **Polling** — client calls `GetTask` repeatedly
2. **Streaming** — SSE connection via `SendStreamingMessage` (HTTP 200 + `Content-Type: text/event-stream`)
3. **Push notifications** — server POSTs to client webhook for long-running/disconnected scenarios (hours/days)

**Five design principles** (Google Developers Blog, 2025):
1. Embrace agentic capabilities (no shared internal state required)
2. Build on existing standards (HTTP, SSE, JSON-RPC)
3. Secure by default (enterprise auth matching OpenAPI schemes)
4. Support long-running tasks
5. Modality agnostic (text, audio, video streaming)

---

## 2. The Critical Architectural Difference

The easiest mental model:

> **MCP** = an agent's nervous system connecting it to the world (tools, data, APIs)
> **A2A** = the diplomatic protocol between sovereign agents

In MCP, the **host/LLM is in control** — it decides when to call a tool, what arguments to pass, what to do with the result. The server is a subordinate capability.

In A2A, the **agents are peers** — there is no assumed hierarchy. A client agent delegates a *task* to a remote agent and waits for the result through a defined lifecycle, regardless of what framework, vendor, or internal architecture the remote agent uses.

This distinction has real technical implications:

| Dimension | MCP | A2A |
|-----------|-----|-----|
| **Relationship model** | Hierarchical (model → tool) | Peer-to-peer (agent ↔ agent) |
| **State persistence** | Stateful session, stateless tool calls | Explicit persistent task objects |
| **Task duration** | Request/response (seconds) | Seconds to days; push notifications for async |
| **Internal visibility** | Servers declare their capabilities openly | Remote agents are opaque black boxes |
| **Discovery mechanism** | Direct configuration by host app | `/.well-known/agent-card.json` URL discovery |
| **Multi-turn conversations** | Via session state in host | Via context IDs grouping related task interactions |
| **UI negotiation** | None | Agents negotiate UI capabilities (iframes, forms, video) |
| **Protocol bindings** | JSON-RPC 2.0 over stdio or HTTP | JSON-RPC 2.0, gRPC, HTTP+REST |
| **Unique primitive** | `sampling` (server-initiated LLM call) | Push notification webhooks |

---

## 3. What A2A Solves That MCP Cannot

**1. Long-running autonomous task delegation**
MCP has no persistent task model. If you call an MCP tool and the server takes 10 minutes, you're holding a connection open or writing custom retry logic. A2A's task lifecycle + push notifications handle hours-long or days-long delegations natively, with standardized cancellation, state querying, and error propagation.

**2. Agent discovery across organizational boundaries**
MCP servers are configured manually in the host application. A2A's `/.well-known/agent-card.json` endpoint lets agents discover each other dynamically — an enterprise agent can query a partner organization's endpoint and learn what that agent offers without any manual setup. Signed cards (v0.3+) add cryptographic verification.

**3. Opaque agent collaboration**
MCP requires servers to declare all their tools, resources, and prompts. A2A allows remote agents to remain black boxes — they expose only what they can do (skills) and accept tasks, not how they do it. This is crucial for cross-vendor deployments: a Salesforce Agentforce agent doesn't need to expose its internals to collaborate with an SAP Joule agent (both are named A2A implementers per Google Cloud Blog, 2025).

**4. Multi-agent orchestration at scale**
A2A is designed for "swarm" scenarios: a planning agent distributes sub-tasks to specialized agents (research, pricing, legal review), each running in parallel with independent lifecycles. MCP has no native model for this — you'd need custom orchestration logic.

**5. UX capability negotiation**
A2A includes a protocol for agents to negotiate UI modalities — one agent can ask another "can you return an iframe? a form? video?" and the receiving agent responds based on its capabilities. MCP has no such concept; it is purely a data/tool interface.

---

## 4. What MCP Solves That A2A Cannot

**1. Direct tool integration — the breadth problem**
MCP has 10,000+ active servers and 5,800+ community/enterprise servers covering databases, CRMs, cloud providers, code execution environments, and more (Pento, 2025). An agent using A2A to delegate to another agent still needs that agent to connect to actual data sources — which is what MCP does. A2A has no equivalent of `mcp__postgres__query` or `mcp__github__create_pr`.

**2. The `sampling` primitive — recursive agentic behavior**
This is MCP's most underappreciated feature. MCP servers can request that the host model make an LLM inference call on their behalf (`sampling/createMessage`). This enables tool servers that themselves reason — for example, a code analysis server that asks the LLM to explain a code snippet as part of its processing. A2A has no equivalent; it assumes agents already have their own reasoning capabilities.

**3. Structured context delivery — Resources and Prompts**
MCP's `Resources` primitive gives the host application control over what contextual information is surfaced to the model (current file, database schema, user profile). This is **app-controlled**, not model-controlled. MCP's `Prompts` primitive allows user-facing template workflows. Neither has a direct A2A equivalent.

**4. Filesystem and URI boundary enforcement**
MCP's `Roots` primitive lets users scope which directories a server can access — critical for IDE integrations like Cursor or VS Code. A2A operates at a higher abstraction level and has no filesystem security model.

**5. Elicitation — mid-session human input from servers**
MCP (2025-06-18 spec update) allows servers to pause and request additional information from the user via `elicitation/create`. A2A handles this via the `input-required` task state, but MCP's model is richer for interactive, conversation-integrated workflows.

**6. Massive existing ecosystem and tooling**
With 97M monthly SDK downloads as of March 2026 (Pento, 2025), first-class support in Claude, ChatGPT, Cursor, GitHub Copilot, VS Code, and Microsoft Copilot Studio, MCP has far deeper tooling penetration. A2A is enterprise-first and production-ready as of v1.0, but the breadth of available server implementations is orders of magnitude smaller.

---

## 5. Adoption: Comparative Landscape

### MCP
| Milestone | Date | Monthly Downloads |
|-----------|------|-------------------|
| Launch (Anthropic) | Nov 2024 | ~2M |
| OpenAI adoption | Apr 2025 | 22M |
| Microsoft Copilot Studio | Jul 2025 | 45M |
| AWS Bedrock | Nov 2025 | 68M |
| All major providers aboard | Mar 2026 | 97M |

Governance: Linux Foundation (AAIF). Steering: Anthropic, OpenAI, Block, AWS, Google, Microsoft, Cloudflare, Bloomberg.

### A2A
| Milestone | Detail |
|-----------|--------|
| Launch | April 2025, 50+ partners |
| v0.3 | ~July 2025, gRPC + signed cards |
| v1.0 | Production-stable, 150+ ecosystem orgs |
| Steering | AWS, Cisco, Google, IBM Research, Microsoft, Salesforce, SAP, ServiceNow |

Named implementations: Tyson Foods + Gordon Food Service (supply chain agent coordination), Adobe, S&P Global Market Intelligence, SAP Joule, Microsoft Azure AI Foundry + Copilot Studio, Salesforce Agentforce (Google Cloud Blog, 2025).

---

## 6. Are They Complementary or Competing?

**Official answer: explicitly complementary.** The A2A v1.0 announcement states directly: "MCP handles 'tool and context integration at the individual agent level' while A2A addresses 'communication and coordination between agents'" (A2A Protocol, 2025). Google's Developer Guide to AI Agent Protocols (Google Developers Blog, 2025) shows both protocols operating in a layered stack:

```
┌─────────────────────────────────────────────┐
│  Orchestrator Agent                          │
│  (uses A2A to delegate tasks to sub-agents) │
└──────────────┬──────────────────────────────┘
               │ A2A
   ┌───────────┼──────────────────┐
   ▼           ▼                  ▼
Sub-Agent A  Sub-Agent B    Sub-Agent C
(uses MCP    (uses MCP      (uses MCP
 for DB)      for APIs)      for files)
```

Concrete pattern from Google's Developer Guide: "A planner agent might reach out to other agents via A2A, which in turn use MCP to fetch tools, separating tool integration from agent orchestration logic" (Google Developers Blog, 2025).

There is one area of **functional overlap** worth acknowledging: both protocols have some form of task/status notification. MCP's `input-required` state in A2A and MCP's `elicitation` primitive serve similar ends. And both protocols are moving toward OAuth 2.0 alignment. But these are boundary cases, not architectural competition.

---

## 7. Source Conflicts

| Claim | Source A | Source B | Assessment |
|-------|----------|----------|------------|
| A2A ecosystem size | "50+ partners" (Google, Apr 2025) | "150+ organizations" (Google Cloud Blog, mid-2025) | Time difference — both are correct at their respective dates |
| MCP control model | "MCP connects models to tools" (DigitalOcean) | "MCP is used by full agent systems, not just models" (Wikipedia) | Both are technically correct; latter is more precise for 2025 usage |
| MCP governance | "Anthropic-owned protocol" (some sources) | "Donated to Linux Foundation AAIF" (Anthropic, Dec 2025) | Post-donation framing is current; pre-donation claims are outdated |

---

## 8. Open Questions / Gaps

- **A2A server discovery at scale**: How do agents find each other in practice without a centralized registry? The spec defines the card format but not a discovery directory. No clear resolution in current documentation.
- **MCP vs. A2A for streaming modalities**: A2A explicitly supports audio/video streaming modality negotiation. MCP's resource streaming is primarily text/data. Whether MCP will add media streaming or defer to A2A for this is unclear.
- **ACP (Agent Communication Protocol)** from IBM/BeeAI is a third contender not covered here — it operates in the same A2A space but with a REST-first, stateless design. Worth a separate research pass.
- **Long-term governance overlap**: Both protocols are now under overlapping stewardship (Google, Microsoft, AWS, Salesforce are on both governance bodies). Whether convergence or forking occurs is an open question.

---

## Sources

- [Announcing the Agent2Agent Protocol (A2A) — Google Developers Blog](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- [Developer's Guide to AI Agent Protocols — Google Developers Blog](https://developers.googleblog.com/developers-guide-to-ai-agent-protocols/)
- [Agent2Agent Protocol is Getting an Upgrade — Google Cloud Blog](https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade)
- [Announcing A2A v1.0 — a2a-protocol.org](https://a2a-protocol.org/latest/announcing-1.0/)
- [Agent2Agent Protocol Specification — a2a-protocol.org](https://a2a-protocol.org/latest/specification/)
- [GitHub: a2aproject/A2A](https://github.com/a2aproject/A2A)
- [Model Context Protocol Specification 2025-11-25 — modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Architecture — modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-11-25/architecture)
- [Introducing the Model Context Protocol — Anthropic](https://www.anthropic.com/news/model-context-protocol)
- [Donating MCP to the Agentic AI Foundation — Anthropic](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)
- [MCP Joins the Agentic AI Foundation — MCP Blog](https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/)
- [A Year of MCP: From Internal Experiment to Industry Standard — Pento](https://www.pento.ai/blog/a-year-of-mcp-2025-review)
- [MCP Hits 97M Downloads — Digital Applied](https://www.digitalapplied.com/blog/mcp-97-million-downloads-model-context-protocol-mainstream)
- [A2A vs MCP — DigitalOcean](https://www.digitalocean.com/community/tutorials/a2a-vs-mcp-ai-agent-protocols)
- [Google Upgrades Agent2Agent Protocol with gRPC and Enterprise-Grade Security — InfoWorld](https://www.infoworld.com/article/4032776/google-upgrades-agent2agent-protocol-with-grpc-and-enterprise-grade-security.html)
- [An Unbiased Comparison of MCP, ACP, and A2A Protocols — Medium (Sandi Besen)](https://medium.com/@sandibesen/an-unbiased-comparison-of-mcp-acp-and-a2a-protocols-0b45923a20f3)
- [Model Context Protocol — Wikipedia](https://en.wikipedia.org/wiki/Model_Context_Protocol)
