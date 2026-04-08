I have enough primary data. Synthesizing now.

---

## A2A vs MCP — Research Synthesis

**Key Finding**: MCP and A2A solve orthogonal problems at different layers of the agent stack — MCP connects a single model to tools/data (vertical), A2A connects autonomous agents to each other (horizontal). They are structurally complementary but are converging: MCP's November 2025 spec added task-based workflows, and A2A's v0.3 added gRPC — both protocols are acquiring the other's differentiating features.

---

### Architecture Comparison

| Dimension | MCP (Model Context Protocol) | A2A (Agent-to-Agent) |
|---|---|---|
| **Announced** | November 2024 (Anthropic) | April 2025 (Google) |
| **Governance** | AAIF / Linux Foundation (Dec 2025) | Linux Foundation (June 2025) |
| **Problem solved** | Model ↔ external tool/data | Agent ↔ agent coordination |
| **Topology** | Star (one host, many servers) | Peer-to-peer / mesh |
| **Transport** | stdio (local), HTTP + SSE (remote) | HTTP/S + SSE + webhooks; gRPC (v0.3+) |
| **Payload format** | JSON-RPC 2.0 | JSON-RPC 2.0 |
| **Discovery** | Capability negotiation at connection time | Agent Cards at `/.well-known/agent.json` |
| **Core primitives** | Tools, Resources, Prompts | Agent Cards, Tasks, Messages/Artifacts |
| **State model** | Stateful session per server connection | Task lifecycle (submitted → working → input-required → completed/failed/canceled/rejected) |
| **Context sharing** | Full context window shared with host | Agent opacity preserved — no internal state shared |
| **Auth model** | OAuth 2.1 + PKCE (mandatory in Nov 2025 spec); stdio has no auth | 5 schemes: API Key, HTTP Bearer/Basic, OAuth 2.0, OIDC, mTLS |
| **Primary design goal** | Easy-to-build servers; composable integrations | Enterprise interoperability across vendor boundaries |
| **Inspiration** | Language Server Protocol (LSP) | OpenAPI / enterprise service mesh patterns |

---

### MCP Architecture: Vertical Integration

MCP follows a **client-host-server** architecture (Anthropic, MCP Spec 2025-11-25):

```
Application Host (e.g., Claude Desktop)
├── Client 1 ──→ Server: Files & Git
├── Client 2 ──→ Server: Database
└── Client 3 ──→ Server: External APIs
```

The **host** orchestrates, **clients** maintain 1:1 stateful sessions with servers, **servers** expose three primitive types:
- **Tools** (model-controlled): functions the LLM invokes autonomously
- **Resources** (app-controlled): structured data the developer curates
- **Prompts** (user-controlled): reusable instruction templates

Client features the host can offer back to servers:
- **Sampling**: server-initiated recursive LLM calls
- **Roots**: server-scoped filesystem/URI boundaries
- **Elicitation** (June 2025 spec): servers request information from users mid-session

Design principle hardcoded in spec: *"Servers should not be able to read the whole conversation, nor 'see into' other servers."* The host enforces isolation — no MCP server gets full conversation history. However, all servers operate within a shared trust boundary (the host process), which creates cross-contamination risk absent in A2A.

**November 2025 spec additions** (MCP's biggest release):
- Task-based workflows (SEP-1686) — states matching A2A: working, input_required, completed, failed, cancelled
- Extensions Framework for optional composable capabilities
- Machine-to-machine OAuth support (enterprise IdP policy controls)
- Sampling with tools (SEP-1577) — server-side agentic loops

The task-based workflow addition is MCP directly encroaching on A2A's primary differentiator.

---

### A2A Architecture: Horizontal Coordination

A2A defines a **three-layer spec** (a2a-protocol.org, v0.3):
- **Data Model Layer**: Tasks, Messages, AgentCards, Parts, Artifacts
- **Operations Layer**: 11 defined operations (Send Message, Send Streaming Message, Get Task, List Tasks, Cancel Task, Subscribe to Task, Push Notification Config CRUD, Get Extended Agent Card)
- **Protocol Bindings**: JSON-RPC, gRPC (v0.3+), HTTP/REST

**Agent Cards** are the central discovery mechanism — JSON documents at `/.well-known/agent.json` advertising:
- Agent name, description, skills
- Supported input/output modalities (text, file, structured data, audio, video)
- Authentication requirements
- Service endpoint URL

**Task lifecycle states** (9 states): `submitted → working → input-required → completed` | `canceled` | `failed` | `rejected` | `auth-required` | `unknown`

**Message Parts** (typed content units within messages): `TextPart`, `FilePart`, `DataPart` — enables content-type negotiation between agents (e.g., "I can handle iframes" vs "text only").

**Push notifications**: Agents can register webhooks to receive async task updates — a webhook-first design pattern absent in baseline MCP.

**Agent opacity** is a first-class design principle: agents collaborate on *outcomes* without exposing internal state, memory, or tool configurations. A client agent formulates a task; a remote agent executes it and returns artifacts. What happened inside is intentionally invisible. This maps cleanly to cross-organizational deployments where vendors won't expose proprietary logic.

---

### Problem Space: What Each Solves the Other Cannot

**What MCP solves that A2A doesn't:**

1. **Tool/data grounding for a single model**: Giving one LLM access to files, databases, APIs, and prompts in a standardized, composable way. A2A has no concept of a "tool" at the resource level — it only coordinates between agents that already have tools.

2. **Local (stdio) operation**: MCP's stdio transport enables fully offline, on-device integrations with zero network exposure. A2A is inherently networked.

3. **Sampling (model-initiated recursion)**: MCP lets servers request that the host LLM process additional context, enabling recursive agentic loops within a session. A2A has no equivalent — once a task is delegated, the remote agent runs independently.

4. **Prompts primitive**: Reusable, user-controlled instruction templates with slot-filling — no A2A equivalent. Useful for IDE assistants, chat interfaces, and workflow builders.

5. **Ecosystem depth**: 5,500+ servers on PulseMCP as of October 2025; 97M monthly SDK downloads by December 2025. A2A is comparatively nascent.

**What A2A solves that MCP doesn't:**

1. **Cross-vendor, cross-organizational agent coordination**: A2A was explicitly designed for agents built by different vendors operating across org boundaries. MCP's trust model (shared host process) assumes you control the full stack.

2. **Agent opacity**: A2A allows "black box" agents to collaborate. An HR agent, IT agent, and Facilities agent can coordinate an onboarding workflow without any agent exposing internal tooling. MCP's architecture requires shared context.

3. **Long-running, asynchronous task management**: A2A's 9-state task lifecycle, webhook push notifications, and streaming updates are first-class primitives. MCP added task states in November 2025, but A2A's push-notification/webhook model for genuinely async, days-long tasks has no MCP equivalent.

4. **Dynamic agent discovery**: Agent Cards at `/.well-known/agent.json` enable runtime discovery of new agents without reconfiguring clients. MCP servers are statically configured in the host at startup.

5. **Multi-modal content negotiation**: A2A's `Part` system (TextPart/FilePart/DataPart) with UI capability negotiation (iframes, web forms, video) handles richer content contracts than MCP's resource/tool model.

6. **Enterprise auth breadth**: 5 authentication schemes in spec (including mTLS) vs. MCP's OAuth 2.1 + PKCE (with 35% of real servers having no auth as of January 2026 scan of 560 servers, per SnailSploit).

---

### Security: The Sharpest Structural Difference

| Threat | MCP | A2A |
|---|---|---|
| **Tool/prompt injection** | High — tool descriptions are executable intent; MCP has 30+ CVEs tied to this | Moderate — Agent Cards have similar risk but blast radius is contained by opacity |
| **Context bleed** | High — multiple servers share same LLM context window | None — task isolation is by design |
| **Confused deputy** | June 2025 spec explicitly prohibits token pass-through to upstream APIs | N/A — agents authenticate independently |
| **Auth missing in practice** | 35% of 560 scanned servers had no auth on tools/list (Jan 2026, SnailSploit) | Auth declarations required in Agent Card |
| **Local attack surface** | stdio transport has zero auth mechanism (env vars for credentials) | Inherently networked; no local-only transport |

MCP's auth posture improved dramatically from November 2024 to November 2025 (PKCE mandatory, CIMD as default registration), but implementation reality lags spec. A2A was designed from the start with enterprise auth as a hard constraint.

---

### Adoption Data

| Metric | MCP | A2A |
|---|---|---|
| **Launch** | Nov 2024 | Apr 2025 |
| **Servers/implementations** | 5,500+ on PulseMCP (Oct 2025); 17,000+ across all registries | 150+ partner organizations |
| **SDK downloads** | ~8M by Apr 2025; 97M monthly (Python + TypeScript) by Dec 2025 | Not publicly reported |
| **Governance** | AAIF / Linux Foundation (Dec 2025), co-founded with Block, OpenAI | Linux Foundation (Jun 2025) |
| **Major adopters** | GitHub, Notion, Stripe, Hugging Face, Postman, Google Cloud, Microsoft | Salesforce, SAP, ServiceNow, Workday, Atlassian, Box, PayPal; consulting arms at McKinsey, Deloitte, PwC, Accenture |
| **Cloud integrations** | Azure Foundry, Copilot Studio, Cursor, Claude Desktop | Azure AI Foundry (committed, coming), Vertex AI Agent Builder |
| **Search volume (top server)** | Playwright MCP: 35,000/month (Oct 2025, Ahrefs) | Not measured |

**Caveat on MCP numbers**: The 17,000 server figure includes unofficial marketplaces with unknown quality. Actual active user connections to any server are unknown — the data is server registrations, not usage (MCP Manager, Oct 2025). The 28% Fortune 500 adoption figure circulates but lacks primary source attribution — treat as unverified.

**Caveat on A2A numbers**: The "150+ organizations" and "$2.3B market by 2026" figures are from industry estimates and partner announcements, not verified deployments.

---

### Are They Competing or Complementary?

**Structurally complementary — practically converging.**

The canonical architecture that both protocols' own documentation describes:

```
Orchestrator Agent
├── Searcher Agent (via A2A)
│   └── arXiv MCP Server (via MCP)
├── Critic Agent (via A2A)
│   └── Web Search MCP Server (via MCP)
└── Synthesizer Agent (via A2A)
    └── File System MCP Server (via MCP)
```

A2A handles the *horizontal layer* (inter-agent delegation, task coordination, cross-vendor trust). MCP handles the *vertical layer* (each agent's tool and data access). Google's own announcement explicitly positions A2A as complementing MCP (Google Dev Blog, April 2025).

**But convergence is real:**
- MCP's November 2025 spec added task-based workflows (SEP-1686) — directly overlapping A2A's core primitive
- A2A v0.3 added gRPC — matching MCP's performance-oriented tooling direction
- IBM's ACP (Agent Communication Protocol) — a third protocol targeting the gap between both, with stronger native streaming, memory persistence, and pause/resume semantics — suggests the space isn't settled

**The actual competitive question** isn't MCP vs A2A. It's: which governance body, ecosystem, and toolchain wins when enterprises build multi-agent systems? Both are now under Linux Foundation, which lowers that risk. The more interesting tension is between:
- Google/A2A's enterprise-first, cross-org, opacity-preserving model
- Anthropic/MCP's developer-first, tool-integration-depth, rapidly compounding ecosystem

Given MCP's 12-month head start and 97M monthly SDK downloads vs. A2A's enterprise partner breadth, the likely outcome is MCP dominates developer tooling and IDEs; A2A dominates enterprise cross-vendor orchestration. Production systems will use both layers.

---

### Gaps & Unknowns

1. **Real A2A production deployments**: Partner announcements ≠ live systems. No verified case studies with traffic numbers.
2. **MCP actual user connections**: Server counts are marketing; no data on active integrations.
3. **ACP's trajectory**: IBM's protocol overlaps with both and is under-researched. If it gains traction it complicates the "two complementary protocols" narrative.
4. **Security audit gap**: A2A's opacity model is theoretically cleaner, but it's less battle-tested. MCP's 30+ CVEs came from production exposure — A2A may have latent vulnerabilities not yet surfaced.
5. **November 2025 MCP task-states in practice**: SEP-1686 was specced but implementation adoption in real servers is unknown.
6. **MCP's sampling primitive** — potentially the most powerful (and dangerous) capability, enabling servers to recursively invoke LLMs — has almost no security analysis or production case study data.

---

### Sources

- [Announcing the Agent2Agent Protocol (A2A) — Google Developers Blog](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- [A2A Official Specification (latest)](https://a2a-protocol.org/latest/specification/)
- [A2A Protocol GitHub — a2aproject/A2A](https://github.com/a2aproject/A2A)
- [Agent2Agent Protocol is Getting an Upgrade — Google Cloud Blog](https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade)
- [Linux Foundation Launches A2A Protocol Project](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents)
- [MCP Specification 2025-11-25 — modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Architecture Specification](https://modelcontextprotocol.io/specification/2025-11-25/architecture)
- [One Year of MCP: November 2025 Spec Release — MCP Blog](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/)
- [MCP Authorization Spec (June 2025) — modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
- [MCP OAuth 2.1 and PKCE — Auth0 Blog](https://auth0.com/blog/mcp-specs-update-all-about-auth/)
- [November 2025 MCP Authorization Spec Update — Aaron Parecki](https://aaronparecki.com/2025/11/25/1/mcp-authorization-spec-update)
- [MCP vs A2A Clearly Explained — Clarifai](https://www.clarifai.com/blog/mcp-vs-a2a-clearly-explained)
- [MCP vs A2A Attack Surface — SnailSploit](https://snailsploit.com/ai-security/mcp-vs-a2a-attack-surface/)
- [Agentic AI with A2A and MCP using Apache Kafka — Kai Waehner](https://www.kai-waehner.de/blog/2025/05/26/agentic-ai-with-the-agent2agent-protocol-a2a-and-mcp-using-apache-kafka-as-event-broker/)
- [MCP, ACP, and A2A Comparison — Niklas Heidloff](https://heidloff.net/article/mcp-acp-a2a-agent-protocols/)
- [MCP Adoption Statistics 2025 — MCP Manager](https://mcpmanager.ai/blog/mcp-adoption-statistics/)
- [Microsoft on A2A — Microsoft Cloud Blog](https://www.microsoft.com/en-us/microsoft-cloud/blog/2025/05/07/empowering-multi-agent-apps-with-the-open-agent2agent-a2a-protocol/)
- [IBM on A2A — IBM Think](https://www.ibm.com/think/topics/agent2agent-protocol)
- [A2A + MCP Guide — DigitalOcean Community](https://www.digitalocean.com/community/tutorials/a2a-vs-mcp-ai-agent-protocols)
