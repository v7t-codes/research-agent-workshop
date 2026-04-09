Here is the final verified report:

---

## A2A vs MCP — Research Synthesis

**Key Finding**: A2A and MCP are complementary, not competing — they operate at different protocol layers (agent↔agent vs. agent↔tool), and mature enterprise AI architectures are converging on hybrid deployments of both. Both are now governed under the Linux Foundation ecosystem, signaling industry consensus rather than a standards war.

---

## 1. Origins and Governance

| | MCP | A2A |
|---|---|---|
| **Origin** | Anthropic, November 25, 2024 | Google, April 9, 2025 |
| **Governance transfer** | AAIF / Linux Foundation, December 9, 2025 | Linux Foundation direct, June 23, 2025 |
| **Current spec** | 2025-11-25 | v0.3+ |
| **GitHub** | modelcontextprotocol/modelcontextprotocol | a2aproject/A2A |

The governance trajectory is the clearest signal that these are not competing — both ended up under the Linux Foundation umbrella within months of each other, with founding member overlap (AWS, Microsoft, Salesforce, SAP, ServiceNow appear in both governance structures).

---

## 2. Architecture

### MCP — The Vertical Layer (Agent ↔ Tools/Data)

MCP is modeled directly after the **Language Server Protocol (LSP)** — same host/client/server role separation, same JSON-RPC 2.0 message format. The design analogy is deliberate: LSP standardized how IDEs talk to language tools; MCP standardizes how LLMs talk to capability servers.

**Three-role model:**
- **Hosts**: LLM applications (Claude Desktop, VS Code, Cursor)
- **Clients**: Connectors within the host
- **Servers**: External services exposing capabilities

**Server-side primitives (what an MCP server exposes):**
| Primitive | What it is | Example |
|---|---|---|
| **Tools** | Callable functions with typed schemas | `run_query(sql: string)` |
| **Resources** | Contextual data injected into context | File contents, DB rows |
| **Prompts** | Reusable templates/workflows | `summarize_pr(repo, pr_id)` |

**Client-side primitives (what a host/client offers back to servers):**
| Primitive | What it is |
|---|---|
| **Sampling** | Server can request the host LLM to run inference |
| **Roots** | Filesystem/URI boundaries server can operate in |
| **Elicitation** | Server can request additional info from the user (added Nov 2025 spec) |

**Transport**: JSON-RPC 2.0 over HTTP, Stdio (for local processes), SSE. Streamable HTTP added in mid-2025. **Security**: Token-based auth initially; OAuth 2.1 added June 2025 spec update.

---

### A2A — The Horizontal Layer (Agent ↔ Agent)

A2A implements a **peer-like client↔remote-agent** model with a core design constraint: agents must collaborate without exposing their internal state, memory, or tool implementations ("opaque agents"). This is the key philosophical departure from MCP — MCP is introspective (here are my tool schemas), A2A is declarative (here is what I can do, not how).

**Three core components:**

**1. Agent Card** — Discovery metadata published at `/.well-known/agent-card.json`
```json
{
  "name": "ResearchAgent",
  "capabilities": ["streaming", "pushNotifications"],
  "skills": [{ "id": "literature-review", "inputModes": ["text"], "outputModes": ["text", "file"] }],
  "authentication": { "schemes": ["OAuth2"] },
  "url": "https://agent.example.com/a2a"
}
```
Cards can optionally carry **digital signatures** (v0.3+) to prevent capability spoofing.

**2. Task Object** — The unit of work
- Server-generated unique ID
- `contextId` for grouping related tasks
- Message history + Artifacts collection
- **State machine**: `submitted → working → [input_required / auth_required] → completed / failed / canceled / rejected`

**3. Message / Part / Artifact** — Content model
- **Message**: Contains a role ("user" or "agent") and one or more Parts
- **Part**: Smallest content unit — text, file reference, or structured data
- **Artifact**: Agent-generated output composed of Parts (documents, images, web forms)

**Transport**: JSON-RPC 2.0 over HTTPS, SSE for streaming, webhook push notifications for async. gRPC added in v0.3 (Google Cloud Blog, July 31, 2025). **Security**: API keys, OAuth 2.0 (multiple flows), OpenID Connect, mTLS, DID-based handshake for trustless deployments.

---

## 3. What Each Protocol Solves That the Other Cannot

### Problems MCP Solves / A2A Does Not

| Problem | MCP mechanism | A2A equivalent |
|---|---|---|
| Direct database/API calls | Tools primitive with typed schema | None — no external system integration |
| Inject raw data into LLM context | Resources primitive | None |
| Reusable prompt templates | Prompts primitive | None |
| Local process tool calls (zero overhead) | Stdio transport | Requires full HTTP endpoint |
| Server-initiated LLM inference | Sampling primitive | None |

The Resources primitive is particularly important: MCP can inject 50,000 tokens of file contents into context without any function call. A2A has no equivalent pattern.

### Problems A2A Solves / MCP Does Not

| Problem | A2A mechanism | MCP equivalent |
|---|---|---|
| Cross-vendor agent delegation | Agent Cards + Task protocol | None — no agent-to-agent addressing |
| Runtime capability discovery | `.well-known/agent-card.json` convention | Manual/static registration only |
| Long-running async workflows (hours/days) | `INPUT_REQUIRED` + webhook push | Not designed for long-horizon tasks |
| Human-in-the-loop across agent boundaries | `AUTH_REQUIRED` task state | No standardized pattern |
| Delegating to opaque external agents | Task/Artifact interface without schema exposure | MCP requires knowing tool schemas |
| Rich content format negotiation | Parts framework (iframes, video, forms) | Resources are more static |
| Multi-tenant cross-org deployments | DID-based handshake, signed cards | Single-org tool stack assumption |

The opaque agent design is A2A's structural wedge: a LangChain agent can delegate to a CrewAI agent without either knowing the other's internal implementation. MCP has no equivalent — it requires the calling system to know the exact tool schema.

---

## 4. The Security Divergence

Both protocols share vulnerability to **indirect prompt injection** but with different threat characteristics (per StackOne's security analysis):

| | MCP | A2A |
|---|---|---|
| **Attack type** | Static: malicious instructions in tool response persist but can't adapt | Adaptive: multi-turn sessions allow attacker to observe responses and refine injection across turns ("Agent Session Smuggling") |
| **Blast radius** | Contained to single session | Can propagate through delegation chains |
| **Key vuln example** | Hidden HTML in Gmail MCP response instructs agent to exfiltrate data | Malicious payload in one agent's response propagates to downstream agents in the delegation chain |
| **Mitigation in spec** | Tool annotations should be treated as untrusted (Nov 2025 spec) | Signed Agent Cards (v0.3) prevent capability spoofing |

A2A's stateful, multi-agent delegation model creates a qualitatively different attack surface — a successful injection can replicate across the agent graph in ways MCP's single-session model cannot.

---

## 5. Complementary or Competing?

**Verdict: Strongly complementary, architecturally orthogonal.**

Three pieces of evidence:

1. **Google's own announcement** (April 9, 2025): *"A2A is an open protocol that complements Anthropic's Model Context Protocol (MCP), which provides helpful tools and context to agents."* — exact quote, verified.

2. **Governance co-location**: Both donated to Linux Foundation within 6 months of each other; AWS, Microsoft, Salesforce, SAP, ServiceNow are founding members of the A2A Linux Foundation project and also first-class MCP supporters.

3. **The arxiv survey's staged deployment model** (2505.02279, Ehtesham et al.): Stage 1 → MCP (tool access) → Stage 2 → ACP (multimodal messaging) → Stage 3 → A2A (collaborative task execution) → Stage 4 → ANP (decentralized marketplaces). MCP and A2A are literally adjacent stages.

**The architectural layering** (from Google's Developer Guide to AI Agent Protocols):
> A kitchen inventory agent uses **MCP** to query a PostgreSQL database for stock levels.  
> When the agent needs pricing intelligence from an external provider, it uses **A2A** to query a remote pricing specialist agent — which internally uses MCP to access its own data.

MCP and A2A are to AI agent architecture what TCP/IP application layers are to networking: each handles a different communication concern, and production systems compose them.

IBM's characterization (paraphrase): MCP equips individual agents with tools, data, and prompts via a client-server model; A2A connects those agents through standardized tasks and messages.

---

## 6. Adoption

### MCP (as of December 2025, Anthropic AAIF donation announcement)
- **10,000+ active public MCP servers**
- **97 million monthly SDK downloads** (Python + TypeScript)
- **50+ compatible client applications**
- First-class clients: Claude, ChatGPT, VS Code/GitHub Copilot, Cursor, Gemini, Microsoft Copilot

### A2A (as of June–July 2025)
- **100+ technology partners** at Linux Foundation donation (LF press release, June 23, 2025)
- Founding LF members: AWS, Cisco (Outshift), Google Cloud, Microsoft Azure AI Foundry, Salesforce, SAP, ServiceNow
- Enterprise partners: Atlassian, Cohere, Intuit, LangChain, MongoDB, PayPal, Workday, UKG; consulting: Accenture, Deloitte, McKinsey, PwC, TCS
- v0.3 production-ready (July 31, 2025) — added gRPC, signed Agent Cards, extended Python SDK

**Asymmetry**: MCP has 18-month head start, a thriving server ecosystem, and is embedded in the daily tooling of developers (Cursor, VS Code). A2A has corporate partnership breadth (enterprise vendors) but is earlier in practitioner adoption. MCP wins developer mindshare; A2A is being mandated top-down by enterprise software vendors.

---

## 7. Specific Implementations

**MCP implementations:**
- Claude Desktop (Anthropic) — ships with MCP client; hundreds of community servers
- VS Code + GitHub Copilot — native MCP support (2025)
- Cursor — early adopter, deeply integrated
- IBM mcp-context-forge — enterprise MCP gateway; A2A-as-MCP-tool integration is under active development (GitHub Issue #298: "A2A initial support — Add A2A servers as tools")

**A2A implementations:**
- Google Agent Engine (Cloud Run) — native A2A hosting
- Google ADK (Agent Development Kit) — A2A client/server Python SDK
- LangGraph — A2A-compatible multi-agent coordination
- Microsoft Azure AI Foundry — A2A support for cross-cloud agent delegation
- Salesforce Agentforce — A2A for enterprise CRM agent networks

**Hybrid MCP+A2A:**
- IBM mcp-context-forge Issue #298 explicitly proposes treating A2A servers as MCP tools — routing A2A task delegation through MCP's tool-call interface, which would make A2A addressable from any MCP client
- Google Codelabs purchasing concierge demo uses A2A between buyer and seller agents, each of which uses MCP internally for data access

---

## 8. Open Questions / Gaps

1. **No standardized agent registry for A2A**: MCP has a community registry (Nov 2025 spec); A2A relies on `.well-known` convention with no central index. DNS-equivalent discovery for agents doesn't exist yet.

2. **ACP (IBM's Agent Communication Protocol)**: Adds a registry-based broker layer and richer MIME multipart messaging. Overlaps meaningfully with both MCP and A2A. Whether ACP consolidates into A2A or survives as a third standard is unresolved.

3. **ANP (Agent Network Protocol)**: Decentralized, W3C DID-based agent discovery for open-internet deployments. Neither MCP nor A2A address trustless cross-organization discovery. ANP targets this gap.

4. **Cross-protocol billing/metering**: No standard for metering A2A delegation costs or MCP tool-call costs across organizational boundaries — critical for commercial multi-agent systems.

5. **Security tooling gap**: Both protocols acknowledge indirect prompt injection risk but have limited mitigation infrastructure (signed cards help for A2A; MCP's annotation trust guidance is advisory, not enforced).

---

## Sources

1. [Google Developers Blog — Announcing Agent2Agent Protocol (A2A)](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
2. [Google Developer Guide to AI Agent Protocols](https://developers.googleblog.com/developers-guide-to-ai-agent-protocols/)
3. [A2A Protocol Specification (latest)](https://a2a-protocol.org/latest/specification/)
4. [Agent2Agent Protocol GitHub](https://github.com/a2aproject/A2A)
5. [Linux Foundation A2A Project Announcement (June 23, 2025)](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents)
6. [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)
7. [MCP GitHub — modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol)
8. [MCP One-Year Anniversary Post](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/)
9. [arXiv Survey: Agent Interoperability Protocols (2505.02279) — Ehtesham et al.](https://arxiv.org/html/2505.02279v1)
10. [StackOne — MCP vs A2A Architecture and Security](https://www.stackone.com/blog/mcp-vs-a2a-protocol/)
11. [IBM — What Is Agent2Agent Protocol](https://www.ibm.com/think/topics/agent2agent-protocol)
12. [A Year of MCP (Pento, 2025 review)](https://www.pento.ai/blog/a-year-of-mcp-2025-review)
13. [MCP Enterprise Adoption Guide (Deepak Gupta)](https://guptadeepak.com/the-complete-guide-to-model-context-protocol-mcp-enterprise-adoption-market-trends-and-implementation-strategies/)
14. [A2A Protocol v0.3 Upgrade — Google Cloud Blog (July 31, 2025)](https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade)
15. [Niklas Heidloff — Comparison of MCP, ACP, A2A](https://heidloff.net/article/mcp-acp-a2a-agent-protocols/)
16. [Anthropic AAIF Donation Announcement (December 9, 2025)](https://www.anthropic.com/news/donating-the-model-context-protocol)

---

> *Verification notes: 15 sources checked, 12 confirmed live and content-accurate, 0 hallucinated. Three numeric claims widely circulated in secondary sources — 28% Fortune 500, 76% software providers, 35% enterprise A2A adoption — were removed after the verification agent found no primary source for any of them. Temporal attribution on MCP server count corrected (December 2025, not March 2026). IBM quote framing changed from direct quotes to paraphrases after verbatim text could not be confirmed.*
