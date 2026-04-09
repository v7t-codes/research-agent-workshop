The research team produced a verified, fully-cited analysis. Here's the final report:

---

# A2A vs MCP: Architecture, Use Cases, and Ecosystem Comparison

## Thesis

MCP and A2A are structurally complementary — MCP standardizes vertical agent-to-tool connections while A2A standardizes horizontal agent-to-agent coordination — but they compete for developer mindshare in the middle layer, where the choice of which to adopt first has compounding ecosystem consequences.

---

## 1. Protocol Architectures

### MCP (Model Context Protocol)

Launched by Anthropic in November 2024. Design metaphor: "USB-C port for AI applications" — replace N×M bespoke integrations with a single N+M standard.

**Participants:**
- **MCP Host** — the AI app (Claude Desktop, VS Code, Cursor)
- **MCP Client** — one instance per server connection, inside the host
- **MCP Server** — exposes data or tools to the host

**Two protocol layers:**
- *Data layer:* JSON-RPC 2.0 message semantics, lifecycle management, primitive definitions
- *Transport layer:* (1) stdio for local processes — no network overhead; (2) Streamable HTTP (POST + optional SSE) for remote, with OAuth

**Server-exposed primitives:**
- *Tools* — executable functions (file ops, API calls, DB queries); model-controlled
- *Resources* — data sources for context; application-controlled
- *Prompts* — reusable LLM interaction templates; user-controlled

**Client-exposed primitives:** Sampling (servers request LLM completions), Elicitation, Logging.

**Lifecycle:** Initialize → capability negotiation → initialized notification → operation → terminate. Stateful by default; stateless via Streamable HTTP.

**Spec version:** 2025-11-25. Design precedent: Language Server Protocol (LSP).

*Sources: modelcontextprotocol.io; MCP Anniversary Blog, Nov 25 2025.*

---

### A2A (Agent-to-Agent)

Launched by Google on April 9, 2025. Defining principle: the **opaque agent** — agents declare capabilities but never disclose internal tools, memory, or proprietary algorithms.

**Two roles:** *Client agent* (formulates tasks) and *Remote agent* (executes tasks).

**Transport (v1.0.0, March 2026):**
- JSON-RPC 2.0 over HTTP/WebSocket
- gRPC (binary Protocol Buffers, added v0.3)
- HTTP/REST
- All bindings must achieve "functional equivalence"

**Agent Cards:** JSON metadata at `/.well-known/agent-card.json` declaring name, description, capabilities, skills, security schemes, and interfaces. v1.0 adds cryptographic signing for cross-org identity.

**Task lifecycle (8 states):** QUEUED → WORKING → INPUT_REQUIRED / AUTH_REQUIRED → COMPLETED / FAILED / CANCELED / REJECTED

**Core operations:** SendMessage, SendStreamingMessage, GetTask, ListTasks, CancelTask, SubscribeToTask, GetExtendedAgentCard

**Authentication:** API keys, OAuth 2.0 (Auth Code, Client Credentials, Device Code per RFC 8628), OpenID Connect, Mutual TLS. Implicit/password OAuth removed in v1.0.

**Architecture:** Stateless by design (v1.0); single endpoint hosts many agents (multi-tenancy).

*Sources: Google Developers Blog (April 9, 2025); a2a-protocol.org spec v1.0.0; GitHub a2aproject/A2A.*

---

### Side-by-Side Architectural Comparison

| Dimension | MCP | A2A |
|---|---|---|
| **Origin / date** | Anthropic, Nov 2024 | Google, Apr 2025 |
| **Current stable** | Spec 2025-11-25 | v1.0.0 (Mar 12, 2026) |
| **Governance** | Agentic AI Foundation (Linux Foundation), Dec 2025 | Linux Foundation, Jun 2025 |
| **Integration direction** | Vertical: agent → tools/data | Horizontal: agent ↔ agent |
| **Core abstraction** | Tools + Resources + Prompts | Tasks + Messages + Artifacts |
| **Discovery** | `tools/list` JSON-RPC call | Agent Card at `/.well-known/agent-card.json` |
| **Primary transport** | stdio (local) or HTTP+SSE (remote) | HTTP+JSON-RPC, gRPC, HTTP/REST |
| **State model** | Stateful (connection-based) | Stateless by design (v1.0) |
| **Supported modalities** | Text, structured data, APIs | Text, audio, video, UI negotiation |
| **Agent opacity** | Servers expose tools explicitly | Remote agents opaque — internals hidden |
| **Security verification** | OAuth/bearer tokens | Signed Agent Cards (cryptographic, v1.0) |
| **Design precedent** | LSP | OpenAPI + web infrastructure standards |

---

## 2. Intended Use Cases

### What MCP Solves

MCP is the right choice when an AI model needs standardized access to external data, tools, or prompts. Per Google's own developer guidance, it's described as "the first step for any agent."

Optimal scenarios:
- Single-agent capability enhancement without bespoke connectors
- Local/offline operation (stdio requires no network)
- Standardized tool execution across multiple agents sharing the same interface
- IDE assistants (Cursor, VS Code) — MCP is the drop-in tool layer
- Long-running multi-step tasks with maintained context within a single session

### What A2A Solves

A2A is the right choice when tasks require coordination between autonomous agents from different vendors, frameworks, or servers. Per Google's developer guidance, A2A addresses where "knowledge lives with different remote agents" and "raw data might never be exposed by API but could be exposed via an agentic interface."

Optimal scenarios:
- Cross-vendor multi-agent workflows (Salesforce + SAP + ServiceNow without exposing internals)
- Long-running distributed task lifecycle with INPUT_REQUIRED and AUTH_REQUIRED states — real-world human-in-the-loop patterns MCP does not natively handle
- Multi-organization collaboration with cryptographically verifiable identities
- Rich modality workflows: audio, video, UI negotiation between agents
- Multi-tenancy: one endpoint hosting many agents at scale

### The Gap Each Fills That the Other Doesn't

**MCP's gap (vs A2A):** No peer coordination model. No native concept of routing a task to another agent, managing task lifecycle across systems, or handling auth handoffs between agents. MCP's stateful connection model also creates scaling concerns at hundreds of concurrent connections.

**A2A's gap (vs MCP):** No tool execution model. A2A defines what agents can do and how they communicate, but delegates "how an agent connects to a database or executes a file operation" entirely to MCP (or equivalent).

The consensus architectural pattern across multiple independent sources: A2A orchestrates between a HR agent, IT agent, and payroll agent; each individual agent uses MCP to access its own databases and tools.

---

## 3. Ecosystem and Adoption

### MCP Adoption (Verified Numbers)

All figures confirmed from primary sources (HIGH confidence per critic's review):

- **97M monthly SDK downloads** (official Agentic AI Foundation announcement, December 2025)
- **10,000 active MCP servers** (official MCP anniversary blog, November 25, 2025)
- **~2,000 registry entries with 407% growth** since initial batch (official MCP anniversary blog)
- **58 maintainers; 2,900+ Discord contributors; 100+ new contributors weekly** (official MCP blog)
- **Client support confirmed in:** Claude, ChatGPT (March 2025), Gemini (April 2025), Microsoft Copilot, VS Code, Cursor
- **Notable MCP servers:** Notion, Stripe, GitHub, Hugging Face, Postman, Amazon Bedrock

**Governance:** MCP donated to the Agentic AI Foundation (AAIF) under the Linux Foundation, December 2025. Co-founded by Anthropic, OpenAI, and Block. Supporting members include AWS, Google, Microsoft, Cloudflare, and Bloomberg.

**Timeline:**
| Date | Milestone |
|---|---|
| Nov 2024 | Anthropic open-sources MCP with Python/TypeScript SDKs |
| Mar 2025 | OpenAI integrates across Agents SDK, Responses API, ChatGPT desktop |
| Apr 2025 | Google DeepMind confirms MCP support in Gemini |
| Sep 2025 | MCP Community Registry launched (~2,000 entries) |
| Nov 2025 | Spec v2025-11-25; 17 SEPs completed; task-based workflows added |
| Dec 2025 | Donated to AAIF/Linux Foundation |

**Security (flagged):** MCP has documented vulnerabilities — prompt injection (April 2025, Willison 2025), GitHub MCP private repo exfiltration (May 2025), CVE-2025-6514. eSentire (vendor) reported 43% of tested implementations vulnerable to prompt injection or tool poisoning — vendor-reported, not independently audited; treat as directionally valid.

**Excluded:** The "17,000+ servers" figure (Pento blog) is not confirmed. Official AAIF counts 10,000 active; current PulseMCP ~11,000. The 17,000 figure appears to combine multiple directories without deduplication.

### A2A Adoption (Verified Numbers)

- **50+ technology partners at launch**, April 2025 (confirmed: official Google announcement). Named: Atlassian, Box, Cohere, Intuit, LangChain, MongoDB, PayPal, Salesforce, SAP, ServiceNow, Workday, and major consultancies (Accenture, BCG, Deloitte, PwC, McKinsey, KPMG, TCS, Wipro)
- **150+ organizations supporting at v0.3**, July 31, 2025 (confirmed: official Google Cloud blog)
- **GitHub: 23,100 stars, 2,300 forks, 10 releases** (confirmed: live GitHub data)
- **SDKs:** Python, Go, JavaScript, Java, .NET/C#
- **v1.0.0 released:** March 12, 2026 (confirmed: GitHub release tag)

**Technical Steering Committee (v1.0):** AWS, Cisco, Google, IBM Research, Microsoft, Salesforce, SAP, ServiceNow (confirmed: official A2A v1.0 announcement).

**Enterprise:** S&P Global and Tyson Foods named in Google's official v0.3 materials — **confirmed identity, unverified implementation specifics**.

**Adoption nuance:** A September 2025 independent developer analysis (fka.dev) documented that A2A suffered complexity barriers through mid-2025 — steep learning curves around discovery, capability negotiation, and security cards made it "practically inaccessible" to independent developers while MCP captured developer mindshare. This predates the v1.0 release in March 2026. Both narratives are accurate for their respective cohorts and time periods — developer adoption friction alongside enterprise partnership momentum — and are not contradictory.

### Governance Trajectory

Both protocols now under Linux Foundation governance:
- **A2A:** Linux Foundation, June 23, 2025
- **MCP:** Agentic AI Foundation (AAIF), December 2025

The A2A TSC includes direct competitors (AWS, Google, Microsoft). How conflicts between TSC members get resolved in practice is not yet established. Neither governance structure's conflict-resolution mechanisms have been publicly stress-tested.

---

## 4. Complementary or Competing?

### Technical Argument for Complementarity

Google's own developer guidance explicitly frames them as complementary: *"MCP standardizes model-tool interactions, while A2A enables agents to coordinate tasks and communicate across systems."*

The vertical/horizontal framing — consistent across multiple independent technical sources — is the most precise description:
- **MCP** = vertical integration (agents connecting *downward* to the tool layer)
- **A2A** = horizontal integration (*lateral* collaboration between peer agents)

These requirements exceed each other's design scope by construction:
- Agent-tool interactions (MCP): explicit input schemas, fixed return formats, atomic operations
- Agent-to-agent communication (A2A): task allocation negotiation, progress synchronization, long-running async task handling, intermediate result streaming

### Where They Overlap (Real Friction Points)

1. **Tool vs. agent boundary ambiguity.** Whether a capability (e.g., a search service, code execution environment) is deployed as an MCP tool or an A2A agent is a design decision with compounding consequences. No canonical guidance currently defines where this boundary should be.

2. **Developer mindshare competition.** MCP arrived first (November 2024 vs. April 2025). For the middle tier of workflows — multi-step tasks that could be a single sophisticated MCP-connected agent *or* an A2A multi-agent pipeline — the path of least resistance leads developers to extend MCP. The September 2025 fka.dev analysis documented this dynamic concretely.

3. **Discovery mechanisms are incompatible.** MCP (`tools/list`) and A2A (`/.well-known/agent-card.json`) require separate infrastructure. No unified service registry spans both protocols as of this writing.

4. **Shared transport substrate.** Both use JSON-RPC 2.0 over HTTP. The current separation is in semantics, not transport primitives — future convergence or divergence is architecturally possible.

### Google's Own Guidance

Google recommends sequential adoption: *"Most agents start with MCP for data access. As your requirements grow (multi-agent communication, rich UI, streaming), bring in the protocol that solves that specific problem."*

Google's developer guide articulates a six-protocol stack (MCP → A2A → UCP → AP2 → A2UI → AG-UI). **Important caveat:** UCP, AP2, A2UI, and AG-UI are not established standards at MCP/A2A maturity levels — they represent Google's aspirational framing, not confirmed industry consensus. Treat the first two layers as actionable; the remaining four as directional.

---

## 5. Where Experts Disagree

| Claim | Position A | Position B | Evidence Strength |
|---|---|---|---|
| Complementary or competing? | Complementary different layers (Google, Koyeb, TrueFoundry) | Competing for mindshare in the middle tier — MCP captured developers first (fka.dev; critic synthesis) | MEDIUM — technical complementarity is well-established; mindshare competition is real but based on qualitative developer sentiment, not survey data |
| Is MCP single-agent only? | Yes — "limiting multi-agent coordination" (TrueFoundry) | No — MCP supports multi-agent setups but lacks *native* peer coordination primitives | MEDIUM — TrueFoundry framing is a simplification; nuanced version is more accurate |
| Is A2A stalled or growing? | Stalled: complexity barriers made it "practically inaccessible" to indie devs by Sep 2025 (fka.dev) | Growing: 150+ org partnerships, enterprise TSC momentum, v1.0 Mar 2026 (official sources) | HIGH — both correct for different cohorts at different times; not contradictory |
| Active MCP server count? | 17,000+ (Pento blog) | 10,000 active (official AAIF, Dec 2025); ~11,000 current PulseMCP | HIGH — 10,000–11,000 is defensible; 17,000 is not confirmed |

---

## 6. Gaps and Limitations

**Gap 1 — No performance benchmarks.** Zero data on transport latency (stdio vs HTTP+SSE vs A2A), throughput under load, or connection establishment cost. Deployment-critical metrics absent from all sources.

**Gap 2 — No developer experience data.** No survey data, GitHub issue analysis, or Stack Overflow volume comparing implementation difficulty. fka.dev is the only qualitative data point.

**Gap 3 — MCP scaling limits underanalyzed.** Coverage is thin on MCP's architectural ceiling: lack of built-in agent-routing, stateful connection model at hundreds of concurrent connections, host management overhead.

**Gap 4 — Competing protocols absent.** Microsoft Semantic Kernel, AutoGen, and OpenAI Assistants API — all directly relevant — are entirely unaddressed in the available literature.

**Gap 5 — Governance implications unanalyzed.** What Linux Foundation transfer means in practice for spec roadmap control, TSC conflict resolution between Google/Microsoft/AWS, and AAIF vs A2A TSC model differences — reported as fact, not analyzed.

**Gap 6 — No production case studies with measured outcomes.** The HR onboarding example is hypothetical. S&P Global and Tyson Foods lack implementation specifics or metrics. No "we deployed MCP + A2A in production, here is what we measured" case study exists.

**Gap 7 — A2A SDK maturity unquantified.** MCP has 97M+ monthly downloads. A2A SDK download numbers are not published. SDK documentation quality, error handling, debugging tooling, and community examples are untouched.

---

## 7. Verification Summary

| Claim | Status | Confidence |
|---|---|---|
| A2A v1.0.0 released March 12, 2026 | CONFIRMED (GitHub releases) | HIGH |
| MCP donated to AAIF/Linux Foundation Dec 2025 | CONFIRMED (official blog + LF press release) | HIGH |
| A2A moved to Linux Foundation June 23, 2025 | CONFIRMED (LF press release) | HIGH |
| A2A GitHub: 23,100 stars, 2,300 forks | CONFIRMED (GitHub live) | HIGH |
| 97M monthly MCP SDK downloads | CONFIRMED (official AAIF announcement) | HIGH |
| 10,000 active MCP servers | CONFIRMED (official MCP blog) | HIGH |
| 150+ organizations supporting A2A at v0.3 | CONFIRMED (Google Cloud blog) | HIGH |
| A2A TSC members listed | CONFIRMED (official A2A announcement) | HIGH |
| MCP AAIF co-founders: Anthropic, OpenAI, Block | CONFIRMED (LF press release) | HIGH |
| S&P Global, Tyson Foods as A2A adopters | PARTIALLY CONFIRMED — identity confirmed, specifics unverified | MEDIUM |
| 17,000+ MCP servers in directories | NOT CONFIRMED (likely directory overcount) | LOW — excluded |
| $1.8B MCP market size 2025 | NOT CONFIRMED — no credible source found | LOW/LIKELY CONFABULATION — excluded |
| MCP security: 43% vulnerable, 437K environments | VENDOR-REPORTED (eSentire), not independently audited | MEDIUM — flagged |

---

## References

1. Anthropic. (2024–2025). *Model Context Protocol — Introduction*. https://modelcontextprotocol.io/introduction
2. Anthropic/MCP Team. (Nov 25, 2025). *One Year of MCP: November 2025 Spec Release*. https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/
3. Google. (Apr 9, 2025). *Announcing the Agent2Agent Protocol (A2A)*. https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/
4. A2A Protocol Project. (2025–2026). *A2A Protocol Specification v1.0.0*. https://a2a-protocol.org/latest/specification/
5. A2A Protocol Project. (Mar 2026). *Announcing Version 1.0*. https://a2a-protocol.org/latest/announcing-1.0/
6. A2A Protocol Project. *GitHub Repository: a2aproject/A2A*. https://github.com/a2aproject/A2A
7. Google. (2025). *Developer's Guide to AI Agent Protocols*. https://developers.googleblog.com/developers-guide-to-ai-agent-protocols/
8. Linux Foundation. (Jun 23, 2025). *Linux Foundation Launches the Agent2Agent Protocol Project*. https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents
9. Google Cloud. (Jul 31, 2025). *Agent2Agent Protocol Is Getting an Upgrade*. https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade
10. Snyder, A. (Dec 2024). *Anthropic Publishes Model Context Protocol Specification*. InfoQ. https://www.infoq.com/news/2024/12/anthropic-model-context-protocol/
11. Willison, S. (Apr 9, 2025). *MCP Prompt Injection*. https://simonwillison.net/2025/Apr/9/mcp-prompt-injection/
12. Jeong, C. (Jun 2025). *A Study on the MCP x A2A Framework…* arXiv preprint arXiv:2506.01804. **[PREPRINT — peer-review status unverified]** https://arxiv.org/abs/2506.01804
13. fka.dev. (Sep 11, 2025). *What Happened to Google's A2A?* [Independent developer blog; pre-v1.0 snapshot] https://blog.fka.dev/blog/2025-09-11-what-happened-to-googles-a2a/
14. eSentire. (2025). *MCP Security: Critical Vulnerabilities Every CISO Should Address*. [Vendor-reported figures] https://www.esentire.com/blog/model-context-protocol-security-critical-vulnerabilities-every-ciso-should-address-in-2025
15. Koyeb. (2025). *A2A and MCP: Start of the AI Agent Protocol Wars?* https://www.koyeb.com/blog/a2a-and-mcp-start-of-the-ai-agent-protocol-wars
16. GetStream. (2025). *LLM Context Protocols: Agent2Agent vs. MCP*. https://getstream.io/blog/agent2agent-vs-mcp/
17. Descope. (2025). *MCP vs A2A*. https://www.descope.com/blog/post/mcp-vs-a2a

---

**Saved to:** `/Users/rshah/research-agent-workshop/final_report.md`

**Research methodology:** Searcher (30 sources, 3 search rounds) → Critic (spot-verified 12 key claims, flagged 3 exclusions and 3 caveats) → Synthesizer (excluded 2 claims, applied 5 flags, built verified reference list).
