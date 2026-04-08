Here is the synthesized research report.

---

# MCP vs. A2A: The Two-Layer Architecture Powering Production Multi-Agent Systems

**Thesis:** MCP and A2A are not competing standards — they address different layers of the agent stack. MCP standardizes how agents access tools and data (vertical: agent → tool). A2A standardizes how agents communicate with and delegate to other agents (horizontal: agent → agent). Production multi-agent systems are converging on using both together.

---

## Key Findings

- **MCP** (Anthropic, Nov 2024) has 25,632 indexed repositories as of March 2026, with official servers from Redis, MongoDB, AWS, Azure, GCP, and HashiCorp. Adopted by OpenAI (March 2025) and Google DeepMind (April 2025). AgentRank (March 2026).
- **A2A** (Google DeepMind, April 2025) has ~2,400 indexed repositories as of March 2026, with 150+ partner organizations and governance transferred to the Linux Foundation (June 2025). AgentRank (March 2026).
- The 10x repository gap reflects MCP's earlier launch and the fact that MCP servers are single-purpose tool wrappers that proliferate quickly; A2A implementations are heavier orchestration frameworks.
- Both are on exponential growth curves: MCP doubled Q3→Q4 2025, then doubled again Q1 2026. A2A is following the same trajectory from its April 2025 launch.
- MCP's November 2025 spec revision introduced an experimental **Tasks primitive** that partially overlaps with A2A's task model, indicating the protocols are borrowing from each other.

---

## Detailed Analysis

### 1. MCP Architecture

The MCP specification (current version: 2025-03-26; key revision: 2025-11-25) defines a **client-host-server** architecture built on JSON-RPC 2.0.

**Three-layer topology:**
```
Host (AI application: Claude Desktop, Cursor, VS Code)
  └─ Client 1 ──→ MCP Server A (Files, Git)
  └─ Client 2 ──→ MCP Server B (Database)
  └─ Client 3 ──→ MCP Server C (External APIs)
```
- **Host:** The AI application. Manages all client instances, enforces security policies, controls consent, aggregates context, routes requests to the underlying LLM.
- **Clients:** Each client maintains a 1:1 stateful session with one server. Handles protocol negotiation and capability exchange.
- **Servers:** Expose capabilities as three primitives: **Tools** (callable functions with schemas), **Resources** (data the agent can read), **Prompts** (reusable templates). Servers can optionally invoke **Sampling** — requesting the host to run LLM inference (enables server-side agent loops, added in the 2025-11-25 spec via SEP-1577).

**Transport:** Originally stdio (local) or HTTP+SSE (remote). The 2025-11-25 spec adds Streamable HTTP, which enables stateless server architectures easier to horizontally scale.

**Key design principles (from spec):**
- Servers should be extremely easy to build — hosts handle complex orchestration.
- Servers cannot see the full conversation history or "into" other servers — strict isolation.
- Capabilities are negotiated at session initialization; neither party can assume features.
- Inspired by Language Server Protocol (LSP), applying the same "write once, work everywhere" idea to AI integrations.

**November 2025 spec additions (MCP's most significant revision):**
| Feature | SEP | Significance |
|---|---|---|
| Tasks primitive | — | Long-running async work; states: working/input_required/completed/failed. Bridges gap with A2A. |
| Client ID Metadata Documents (CIMD) | Replaces DCR | Decentralized OAuth identity via DNS-anchored URLs. Eliminates per-server registration. |
| M2M OAuth (`client_credentials`) | SEP-1046 | Headless agent-to-agent auth without user sessions. |
| Cross App Access (XAA) | SEP-990 | Corporate IdP (Okta, Entra) in the loop for enterprise governance. |
| Extensions framework | SEP-1865 | Formal namespace for optional capabilities. Avoids spec bloat. |
| URL Mode Elicitation | SEP-1036 | Servers redirect users to browser for sensitive flows; client never handles secrets. |

Anthropic (2025 spec docs); WorkOS engineering blog (November 2025).

---

### 2. A2A Architecture

The A2A protocol (v1.0.0 spec, governed by the Linux Foundation as of June 2025) defines how **opaque** AI agent systems communicate. The normative source is a Protocol Buffers definition (`spec/a2a.proto`), making it transport-neutral. Current protocol bindings: JSON-RPC, gRPC (added v0.3), HTTP/REST.

**Three-layer spec structure:**
```
Layer 1: Canonical Data Model (Task, Message, AgentCard, Part, Artifact, Extension)
Layer 2: Abstract Operations (SendMessage, StreamMessage, GetTask, ListTasks, CancelTask, GetAgentCard)
Layer 3: Protocol Bindings (JSON-RPC, gRPC, HTTP/REST)
```

**Core abstractions:**
- **Agent Card:** A JSON manifest served at `/.well-known/agent.json`. Describes the agent's identity, capabilities (skills), supported modalities, authentication requirements (OAuth2, mTLS, API keys). This is how agents discover each other without a central registry.
- **Task:** The fundamental unit of work. Lifecycle: `submitted → working → input_required → completed / failed / cancelled`. Each task has a unique ID, enabling correlation across async interactions.
- **Messages:** Communication turns between client and remote agent, with `role` of "user" or "agent". Each message contains one or more **Parts** (TextPart, DataPart, FilePart).
- **Artifacts:** The outputs an agent produces — bundles of Parts. Can be streamed incrementally.
- **Push Notifications:** Webhook callbacks for long-running tasks where maintaining an SSE stream is impractical.

**Three interaction modes:**
1. **Synchronous request/response:** `message/send` → completion + artifact.
2. **Streaming:** `message/stream` → Server-Sent Events with incremental updates.
3. **Webhooks:** `tasks/pushNotificationConfig/set` → async POST callbacks on state change.

**Security model:** HTTPS with TLS 1.2+ required. Authentication advertised in Agent Card and handled out-of-band. Observability via W3C trace context headers; task IDs and trace IDs correlated for auditability. A2A explicitly does *not* build in state persistence or memory — that is the application's responsibility.

**Opaque execution principle:** A2A agents collaborate purely on declared capabilities and exchanged artifacts. Neither agent can see the other's internal tools, memory, prompts, or reasoning. This is the foundational enterprise-safety property.

Google Cloud blog (July 2025); WWT deep dive blog; A2A protocol spec (a2a-protocol.org); Linux Foundation press release (June 2025).

---

### 3. What Problems Each Solves That the Other Doesn't

| Dimension | MCP | A2A |
|---|---|---|
| **Core problem** | Standardize how an agent calls tools/data | Standardize how agents delegate to other agents |
| **Direction** | Vertical: agent → deterministic tool | Horizontal: agent → autonomous agent |
| **Discovery** | Protocol-native `tools/list` at runtime | Static Agent Cards at DNS-anchored URL |
| **Peer complexity** | Tools are atomic, deterministic functions | Agents are autonomous, multi-step, opaque |
| **Task lifecycle** | Synchronous (Tasks is experimental in Nov 2025) | First-class async state machine |
| **Long-running workflows** | Limited (added Nov 2025) | Native; async-first by design |
| **Cross-vendor interoperability** | Within a client ecosystem | Across completely independent vendor systems |
| **Enterprise observability** | Not specified in protocol | W3C trace headers, task ID correlation built-in |
| **Internal state sharing** | Servers see resources/context | No shared state; opaque black boxes |
| **Memory/persistence** | Not addressed | Not addressed (explicitly out of scope) |

**MCP solves what A2A cannot:**
- Standard tool-calling interface that works across all AI clients (Claude, Cursor, Copilot, VS Code). An MCP server written once works everywhere.
- Self-documenting schemas for tools with clear input/output contracts.
- Deep integration with the host's LLM (Sampling) — servers can request inference and run server-side agent loops.
- Broad developer ecosystem for one-off integrations (database connectors, file systems, SaaS APIs). The "USB-C for AI" use case.

**A2A solves what MCP cannot:**
- Delegation to agents that are complex, autonomous, and potentially from a different vendor entirely. You can't wrap a Salesforce AI agent as an MCP tool — it has its own reasoning loop, memory, and tool access.
- Long-running task orchestration with explicit status reporting and resumability.
- Cross-organization agent marketplaces — Agent Cards create a discovery mechanism without requiring pre-registration or shared infrastructure.
- Multi-turn, stateful agent conversations where the sub-agent may require clarification mid-task (`input_required` state).

---

### 4. Ecosystem Adoption

**MCP adoption trajectory (from Zuplo, AgentRank, Thoughtworks):**
- November 2024: Anthropic releases; Claude Desktop is first host; Python + TypeScript SDKs.
- March 2025: OpenAI adopts across ChatGPT, Agents SDK, Responses API. Sam Altman: *"people love MCP and we are excited to add support across our products."*
- April 2025: Google DeepMind confirms MCP support for Gemini. Demis Hassabis: *"MCP is a good protocol and it's rapidly becoming an open standard for the AI agentic era."*
- November 2025: 16,000+ MCP servers. VS Code, Cursor, Windsurf, Zed, Replit, GitHub, Linear, Zapier, Block, Apollo, Sourcegraph all integrated.
- March 2026 (AgentRank): 25,632 indexed repositories. Top categories: database access (847 repos), DevOps automation, developer tooling.

**A2A adoption trajectory (from Google Cloud blog, Linux Foundation press release):**
- April 2025: Google launches with 50+ partner contributions (Salesforce, SAP, Atlassian, ServiceNow, LangChain).
- June 2025: Linux Foundation takes governance. AWS, Cisco, Salesforce, SAP, Microsoft, ServiceNow as founding members.
- July 2025: Google announces 150+ organizations in ecosystem; v0.3 released with gRPC support and signed Agent Cards; ADK native A2A support. Tyson Foods and Gordon Food Service named as early enterprise users.
- March 2026 (AgentRank): ~2,400 indexed repositories. Top categories: orchestration frameworks, enterprise integration adapters.

---

### 5. Complementary vs. Competing

**The consensus across technical sources is: complementary, operating at different layers of the stack.**

The reference architecture emerging in production:

```
User
  └─ Orchestrator Agent
        ├─── A2A ──→ Research Agent
        │               └─ MCP ──→ [Web Search Tool]
        │               └─ MCP ──→ [Vector DB Tool]
        ├─── A2A ──→ Code Agent
        │               └─ MCP ──→ [GitHub Tool]
        │               └─ MCP ──→ [Test Runner Tool]
        └─── A2A ──→ Data Agent
                        └─ MCP ──→ [Database Tool]
                        └─ MCP ──→ [Analytics API Tool]
```

Google's Agent Development Kit (ADK) implements this pattern natively as of July 2025: agents use A2A to coordinate with peers and MCP to access tools internally. LangGraph and CrewAI have similar layered approaches.

WWT blog: *"An agentic application might use A2A to communicate with other agents, while each agent internally uses MCP to interact with its specific tools and resources. They are not rivals; they are friends."*

AgentRank blog: *"A2A gives agents colleagues. MCP gives agents hands."*

**The one area of genuine tension** is the MCP November 2025 Tasks primitive. As MCP adds async task management with state machines, it begins to blur the line with A2A for smaller-scale multi-agent patterns. A single developer building a two-agent system might find MCP's Tasks sufficient without needing A2A. But for cross-vendor enterprise orchestration — where agents from Salesforce, SAP, and Google Cloud need to coordinate — A2A's opaque execution model and Agent Card discovery remain essential.

---

## Source Conflicts

| Claim | Source A | Source B | Assessment |
|---|---|---|---|
| MCP server count | "16,000+" (Zuplo, Nov 2025) | "25,632 repos" (AgentRank, March 2026) | Consistent — different dates, both credible |
| A2A ecosystem size | "100+ organizations" (Linux Foundation, June 2025) | "150+ organizations" (Google Cloud, July 2025) | Consistent — one month difference, growth expected |
| MCP is "stateful" | MCP spec (stateful sessions) | Zuplo notes Streamable HTTP enables stateless servers | Not a conflict — both true; stateful sessions but stateless *server architecture* is now possible |
| A2A and MCP "competing" | Some early media coverage (April 2025) framed as competition | WWT, AgentRank, Google ADK all frame as complementary | Consensus has shifted strongly to complementary post-July 2025 |

---

## Open Questions

1. **Will MCP's Tasks primitive erode A2A's value proposition at smaller scales?** As MCP becomes more async-capable, the threshold at which you need A2A moves up. The protocols are converging slightly.
2. **Security maturity remains unresolved for both.** MCP has a documented CVE (CVE-2025-49596, patched June 2025) and known prompt injection/tool poisoning vectors. A2A's security model depends on proper TLS and OAuth configuration, which is easy to misconfigure. Neither protocol enforces security at the protocol layer itself.
3. **MCP's 10x repo advantage — does it persist?** A2A repos are heavier orchestration frameworks; raw repo count may understate production A2A adoption. An A2A ecosystem report is forthcoming from AgentRank.
4. **Monetization is unsolved in both protocols.** Neither specifies how agents pay for services, meter usage, or handle billing for agent-as-a-service offerings.
5. **Memory and state persistence** are explicitly out of scope for both. This gap is being filled by application-layer solutions (LangMem, Zep, etc.) but no standard has emerged.
6. **Will A2A's Linux Foundation governance give it the same vendor-neutral credibility that propelled MCP?** MCP succeeded in part because Anthropic released it as a genuinely open standard. A2A's governance transition mirrors that move, but Google's fingerprints remain visible in the ecosystem.

---

## Sources

1. **MCP Specification 2025-03-26.** Anthropic. modelcontextprotocol.io/specification/2025-03-26
2. **MCP Architecture.** modelcontextprotocol.info/specification/2024-11-05/architecture
3. **MCP 2025-11-25 Spec Update.** WorkOS Engineering Blog, November 2025. workos.com/blog/mcp-2025-11-25-spec-update
4. **One Year of MCP.** Zuplo Engineering Blog, November 2025. zuplo.com/blog/one-year-of-mcp
5. **The Model Context Protocol's Impact on 2025.** Thoughtworks Technology Radar Vol. 33, December 2025. thoughtworks.com
6. **Agent2Agent (A2A) Protocol Specification v1.0.0.** a2a-protocol.org/latest/specification
7. **Announcing a Complete Developer Toolkit for Scaling A2A Agents on Google Cloud.** Google Cloud Blog, July 31, 2025 (v0.3 announcement). cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade
8. **Linux Foundation Launches the Agent2Agent Protocol Project.** Linux Foundation Press Release, June 23, 2025. linuxfoundation.org
9. **Agent-2-Agent Protocol (A2A) — A Deep Dive.** WWT Blog. wwt.com/blog/agent-2-agent-protocol-a2a-a-deep-dive
10. **A2A vs MCP: The Definitive Agent Protocol Comparison (2026).** AgentRank Blog, March 2026. agentrank-ai.com/blog/a2a-vs-mcp-agent-protocol-comparison

---
*Note: All adoption numbers (repo counts, organization counts) are self-reported by the respective ecosystems and unverified by independent audit. MCP CVE-2025-49596 is publicly documented but post-dates the main MCP spec design. AgentRank data flagged as a third-party index, not an official count from Anthropic or Google.*
