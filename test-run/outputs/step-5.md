Verification complete. Correcting 4 issues found: (1) 97M/10K stats misattributed — they come from the Dec 9 AAIF donation announcement, not the Nov 25 anniversary post; (2) MCP spec `2025-11-25` is not the latest — `2025-03-26` is current; (3) ACP merger date is Aug 29, not Sep 1; (4) qualifying the Auth0 A2A→MCP identity propagation claim. No hallucinated sources found (0/20).

---

# A2A vs MCP: Architecture, Use Cases, Adoption, and Complementarity

*Researched April 8, 2026. Verification agent ran independently: 20 sources checked, 0 hallucinated, 3 corrections applied.*

---

## 1. What Each Protocol Is (And Isn't)

### MCP — Model Context Protocol

Anthropic announced MCP on **November 25, 2024** (Anthropic, 2024). The problem it solves is explicit and narrow: the N×M integration problem. Before MCP, every AI application needed a custom connector for every external data source — N applications × M data sources = N×M bespoke integrations. MCP collapses this to N+M by standardizing the interface between any agent and any tool or data source. The design is self-consciously modeled on Microsoft's Language Server Protocol, which performed the same unification for IDEs and language tooling.

Early adopters named at launch: Block, Apollo, Zed, Replit, Codeium, Sourcegraph. Pre-built reference servers shipped immediately for Google Drive, Slack, GitHub, Git, Postgres, and Puppeteer. OpenAI adopted MCP in March 2025 and co-founded the governance body (AAIF) in December 2025.

**Governance:** Anthropic donated MCP to the **Agentic AI Foundation (AAIF)**, a directed fund under the Linux Foundation, on December 9, 2025 — co-founded by Anthropic, Block, and OpenAI, with Google, Microsoft, AWS, Cloudflare, and Bloomberg as additional supporters (Anthropic, 2025c). The multi-stakeholder composition is significant: MCP is now a neutral open standard.

**Specification:** `spec.modelcontextprotocol.io/specification/` — current version `2025-03-26` (note: the `2025-11-25` version cited in many articles is real but no longer the latest as of April 2026).

---

### A2A — Agent2Agent Protocol

Google announced A2A on **April 9, 2025** (Google, 2025a). Its design premise is stated directly in the launch post: "A2A is an open protocol that complements Anthropic's Model Context Protocol (MCP), which provides helpful tools and context to agents." A2A sits one layer up in the stack — not connecting agents to tools, but enabling agents to coordinate with other agents as full autonomous systems.

Launch partners: 50+ organizations including Atlassian, Box, Salesforce, SAP, ServiceNow, LangChain, PayPal, MongoDB, Intuit, Workday, and major SIs (Accenture, BCG, Deloitte, PwC, Wipro, TCS).

**Governance:** Google donated A2A to the Linux Foundation on **June 23, 2025**, forming the Agent2Agent Protocol Project, with AWS, Cisco, Google, Microsoft, Salesforce, SAP, and ServiceNow as founding members (Linux Foundation, 2025). IBM's Agent Communication Protocol (ACP/BeeAI) merged into A2A on **August 29, 2025** (LFAI & Data, 2025). A2A reached v1.0.0 in March 2026.

**Specification:** `a2a-protocol.org/latest/specification/` | GitHub: `github.com/a2aproject/A2A` (Apache 2.0)

---

## 2. Technical Architecture

### MCP: Three-Role Client-Server

MCP uses a **three-role model**: Host → Client → Server.

- **MCP Host**: The AI application (Claude Desktop, VS Code, Claude Code). Manages one or more MCP clients simultaneously.
- **MCP Client**: A component inside the host. Each client holds a **dedicated 1:1 connection** to one MCP server.
- **MCP Server**: A local or remote program that exposes tools, resources, and prompts.

**Transport Layer** (two variants):
| Transport | Mechanism | Use Case |
|-----------|-----------|----------|
| **Stdio** | Standard input/output streams | Local process-to-process; zero network overhead; dominant in IDE integrations |
| **Streamable HTTP** | HTTP POST (client→server) + optional SSE (server→client) | Remote servers; supports OAuth 2.1, bearer tokens, API keys |

> The older "HTTP SSE" transport from the `2024-11-05` spec has been superseded by the more flexible **Streamable HTTP** transport in the `2025-11-25` spec. (modelcontextprotocol.io, Architecture)

**Encoding:** JSON-RPC 2.0 throughout.

**Lifecycle and Capability Negotiation:**
MCP is stateful. On connection:
1. Client sends `initialize` with `protocolVersion` (e.g., `"2025-06-18"`) and its `capabilities`.
2. Server responds with its `protocolVersion` and `capabilities`.
3. Client sends `notifications/initialized`.

Incompatible versions terminate the connection. Negotiated capabilities (e.g., `"tools": {"listChanged": true}`) govern which methods and notifications are valid for the session.

**Server-Side Primitives:**

| Primitive | Methods | Description |
|-----------|---------|-------------|
| **Tools** | `tools/list`, `tools/call` | Executable functions. Each has a JSON Schema `inputSchema`. Returns a `content` array. |
| **Resources** | `resources/list`, `resources/get` | Read-only data sources (file contents, DB records, API responses). For contextualization, not execution. |
| **Prompts** | `prompts/list`, `prompts/get` | Reusable message templates and few-shot examples. |

**Client-Side Primitives (bidirectional — unique to MCP):**

| Primitive | Method | Description |
|-----------|--------|-------------|
| **Sampling** | `sampling/complete` | Server requests an LLM completion from the host. Enables model-agnostic servers that don't bundle their own model. |
| **Elicitation** | `elicitation/request` | Server requests additional user input mid-session. |

**Notifications:** Servers push real-time updates via JSON-RPC notification messages (no `id` field, no response required). Example: `notifications/tools/list_changed` fires when tool set changes, triggering the client to re-run `tools/list`.

**SDK Ecosystem:** 10 official SDKs — TypeScript (reference), Python (reference), Java, Kotlin (with JetBrains), C# (with Microsoft), Go (with Google), PHP, Ruby, Rust, Swift. Monthly downloads: **97 million** across Python + TypeScript SDKs; **10,000+ active servers** in deployment — both figures from Anthropic's December 9, 2025 AAIF announcement (Anthropic, 2025c), not the November 25 anniversary post.

---

### A2A: Two-Role Orchestration Model

A2A uses a **two-role model**: Client Agent → Server Agent.

- **A2A Client (Client Agent):** Initiates requests on behalf of a user or orchestrating system.
- **A2A Server (Remote Agent):** Exposes an HTTPS endpoint. Operates as an **opaque black box** — internal memory, tools, and logic are never exposed to callers. This is a design principle, not a limitation.

**Transport:**
- Primary: HTTPS + JSON-RPC 2.0
- Streaming: Server-Sent Events (SSE) — `Content-Type: text/event-stream`
- Added in v0.3 (July 2025): gRPC (Google, 2025b)

**Discovery — Agent Cards:**
Every A2A server publishes a JSON document at `/.well-known/agent.json`. This "Agent Card" is the central discovery mechanism, containing:
- Agent identity and description
- Service endpoint URL
- Declared capabilities (e.g., `capabilities.streaming: true`)
- Authentication requirements (OAuth 2.0, OIDC, API keys — mirroring OpenAPI auth schemes)
- A list of skills the agent supports

Clients parse the Agent Card before sending any request. A2A v0.3+ supports cryptographic signing of Agent Cards.

**Core Data Model:**

| Element | Description |
|---------|-------------|
| **Task** | Stateful unit of work with lifecycle states: `submitted → working → input-required → completed / failed / canceled / unknown` |
| **Message** | A single turn (role: `user` or `agent`), containing one or more Parts |
| **Part** | Content container: `text`, `raw` (bytes), `url` (URI), or `data` (structured JSON) — each with a MIME `mediaType` |
| **Artifact** | Tangible deliverable produced by the agent (document, image, structured data). Can be streamed in chunks. |
| **contextId** | Server-generated ID grouping multiple related Tasks across a session |

**Key RPC Methods:**
- `SendMessage` — synchronous request/response
- `SendStreamingMessage` — initiates task + subscribes to SSE stream
- `SubscribeToTask` — reconnects to an existing SSE stream after disconnection
- `GetTask` — retrieves current task state (used in polling)
- `CreateTaskPushNotificationConfig` — registers a webhook for async push notifications

**Three Interaction Patterns:**
1. **Request/Response (Polling):** `SendMessage` → poll `GetTask` for long-running tasks
2. **Streaming (SSE):** `SendStreamingMessage` → server pushes `TaskStatusUpdateEvent` and `TaskArtifactUpdateEvent` over a held-open connection
3. **Push Notifications:** For disconnected/long-running scenarios (hours/days), server POSTs to a client-provided HTTPS webhook. Security: JWT signed with server's private key; client verifies against server's JWKS endpoint.

---

## 3. The Layer Distinction — Why They Don't Overlap

This is the central architectural fact. MCP and A2A operate at different layers of the agent stack:

| Layer | Protocol | Relationship |
|-------|----------|-------------|
| Tool/Resource Layer | **MCP** | Agent ↔ external tools, APIs, databases, files |
| Agent Collaboration Layer | **A2A** | Agent ↔ agent (delegation, orchestration, multi-agent workflows) |
| Decentralized Discovery Layer | **ANP** | Agent ↔ agent across open networks (W3C DIDs — not production-ready) |

As Gravitee.io puts it: "MCP provides vertical integration (application-to-model), while A2A provides horizontal integration (agent-to-agent)." (Gravitee.io, 2025)

**The canonical combined architecture** (from Google's documentation and the AWS Open Source Blog):

> An orchestrator agent receives a user request → delegates via A2A to specialized sub-agents (candidate-sourcing agent, scheduling agent) → each sub-agent independently calls its own tools via MCP (a database connector, a calendar API) → results flow back through A2A as Artifacts → sub-agents' internal architectures are invisible to the orchestrator.

This stack — MCP for tool access, A2A for inter-agent delegation — is what "complementary" means in practice.

---

## 4. What A2A Solves That MCP Does Not

### 4.1 Multi-Agent Orchestration and Task Delegation
MCP has no concept of one agent delegating a task to another autonomous agent. Its entire model is an agent calling a tool (a stateless function returning a result). A2A enables agents to act as orchestrators that distribute sub-tasks to remote, fully autonomous agents — which may themselves be black boxes running on different frameworks from different vendors.

### 4.2 Long-Running Stateful Tasks Across Agent Boundaries
A2A's Task model explicitly tracks lifecycle across hours or days. A task can remain in `working` or `input-required` state indefinitely, with push notifications delivered when state changes. This is first-class protocol behavior. MCP tool calls are request/response with no native lifecycle tracking.

### 4.3 Human-in-the-Loop as a Protocol Primitive
A2A's `input-required` task state pauses execution and signals to the orchestrator that a human decision is needed before proceeding (e.g., approving a financial transaction, reviewing a document before sending). MCP has no equivalent — human-in-the-loop in MCP systems must be implemented at the application layer.

### 4.4 Capability Discovery Across Heterogeneous Agent Networks
Agent Cards allow an orchestrator to discover what any A2A server can do *before* sending a request. An orchestrator can dynamically select among available agents based on their declared skills. MCP has no equivalent for agent-level capability advertisement — it only discovers tools from a specific server already provisioned into the client.

### 4.5 Opaque Execution and IP Isolation
A2A's design explicitly guarantees that "agents don't share memory, tools and context" (Google, 2025a). A remote agent's internal architecture is entirely hidden — callers see only inputs and outputs. This enables enterprise deployments where different teams or vendors own specialized agents without exposing proprietary logic, prompts, or data pipelines.

### 4.6 Multimodal Artifact Streaming
A2A's Part type system (text, raw bytes, URL, structured JSON with MIME types) and the Artifact abstraction for streaming deliverables are designed for agents producing rich outputs — documents, images, audio, video — as first-class protocol objects. MCP returns `content` arrays primarily optimized for text and simple data.

---

## 5. What MCP Solves That A2A Does Not

### 5.1 The N×M Tool Integration Problem
MCP's primary contribution is standardizing the agent-to-tool interface so any MCP-compatible tool works with any MCP-compatible host. A2A has no equivalent — it does not address how individual agents access tools, only how agents talk to each other.

### 5.2 Resource Access (Read-Only Data Contextualization)
MCP's Resources primitive provides a clean interface for pulling contextual data (file contents, database records, API responses) into working context without executing code. There is no A2A equivalent — A2A is about task delegation, not data fetching.

### 5.3 Prompt Templates as a Protocol Primitive
MCP's Prompts primitive enables servers to expose reusable prompt templates and few-shot examples injectable into agent context. A2A has no prompt template mechanism.

### 5.4 Bidirectional Model Access (Sampling)
MCP's `sampling/complete` primitive allows a *server* to request an LLM completion from the *host*. This is unique: it enables model-agnostic MCP servers that can use the host's model without bundling their own. No A2A equivalent.

### 5.5 Local Process Communication
MCP's stdio transport enables zero-network-overhead local agent-tool communication — essential for IDE integrations, local file system access, and development tooling. A2A is HTTPS-only (with gRPC in v0.3+), making it inherently a networked protocol unsuitable for local process integration.

### 5.6 Ecosystem Breadth
MCP has 10 official SDKs, 10,000+ active servers, 97M monthly SDK downloads, and adoption by all four major AI model providers (Anthropic, OpenAI, Google, Microsoft) (Anthropic, 2025c). For building a new integration between an agent and a data source or API, MCP is the only practical choice today.

---

## 6. Complementary or Competing?

**Official position: Complementary.** Google's own announcement (Google, 2025a) explicitly positions them as complementary. The official A2A documentation includes a dedicated "A2A and MCP" section. Anthropic and Google Cloud co-hosted a webinar titled "Deploying multi-agent systems using MCP and A2A with Claude on Vertex AI." Google Codelabs published "Getting Started with MCP, ADK and A2A."

**The more honest answer: Complementary by design, with genuine friction in implementation.**

Auth0 — a launch partner for A2A's authentication specification — identified the central practical tension: when an A2A-orchestrated system has sub-agents that themselves need tool access via MCP, **identity and permission propagation across the A2A→MCP boundary is an unsolved engineering problem** (Auth0, 2025). Who owns the security boundary? How does an OAuth token from the A2A client propagate into the MCP tool call made by the A2A server-side agent? Auth0's involvement with A2A is specifically aimed at this gap. The claim that Auth0's article makes this specific argument exists and the topic is confirmed; however, the full article body was not directly confirmable via page fetch during verification.

The Koyeb blog described this as a "tug of war" in production systems: "the two-protocol landscape forced developers to implement both (MCP for tool access, A2A for inter-agent orchestration) without a clear boundary" (Koyeb, 2025).

A more critical perspective: the fka.dev blog argued in April 2025 that since both protocols are built on JSON-RPC, MCP could be extended to handle agent-to-agent orchestration with minor specification additions rather than a separate protocol — calling A2A "unnecessary ecosystem complexity" (fka.dev, 2025a). By September 2025, the same author observed that A2A had "quietly faded into the background while MCP has become the de facto standard" (fka.dev, 2025b).

**Resolution via AAIF (December 2025):** Both protocols are now under Linux Foundation governance — A2A under the Agent2Agent Protocol Project, MCP under AAIF (Anthropic, 2025c; Linux Foundation, 2025). Shared neutral governance creates structural incentive for interoperability rather than competition. IBM's ACP merging into A2A further consolidated the agent-coordination protocol space. However, fragmentation has not fully collapsed: ANP (W3C-based, decentralized, uses DIDs) and vertical-specific protocols like the Agentic Commerce Protocol (OpenAI + Stripe, for payments) remain outside this umbrella.

---

## 7. Adoption: A Telling Asymmetry

| Metric | MCP | A2A |
|--------|-----|-----|
| Monthly SDK downloads | 97M (Dec 2025) | Not publicly reported |
| Active servers/endpoints | 10,000+ (Dec 2025) | N/A (agent-to-agent, not tool servers) |
| Official SDKs | 10 languages | Python, Go, TypeScript, Java, .NET |
| Model provider support | Anthropic, OpenAI, Google, Microsoft | N/A (infrastructure, not model-layer) |
| Age | ~17 months | ~12 months |
| Launch partners | Named early adopters (developers) | 50+ organizations (enterprises) |
| Governance | AAIF / Linux Foundation | Agent2Agent Protocol Project / LF |

**Enterprise A2A deployments (named):** Tyson Foods + Gordon Food Service (supply chain product data sharing); S&P Global Market Intelligence (inter-agent communication). Azure AI Foundry reports 70,000+ enterprises on the platform; 10,000+ adopted the Agent Service in first 4 months — though these are Azure AI figures broadly, not A2A specifically (Microsoft, 2025).

**The adoption asymmetry tells the real story:** MCP spread bottom-up through developers (it worked immediately with existing AI tools). A2A spread top-down through organizational commitments (it required building new infrastructure). By September 2025, A2A had faded from developer discourse even while retaining enterprise commitments.

---

## 8. Limitations and Security Concerns

### MCP

**Tool Poisoning / Prompt Injection:** Malicious instructions embedded in MCP tool *descriptions* — text the LLM sees but users typically don't — can hijack agent behavior without user awareness. Invariant Labs documented this formally in April 2025; their MCPTox benchmark found attack success rates up to 72.8% on o1-mini across 353 real tools from 45 MCP servers (Invariant Labs, 2025). The paper attributes this claim: "the paper claims" these attack success rates were measured, not that this is established consensus.

**Rug Pull / Silent Redefinition:** MCP's approval flow is one-time. A server can present a safe tool description at install, gain user approval, then mutate the description post-approval. There is no re-consent mechanism. An academic paper (arXiv:2506.01333) proposed OAuth-Enhanced Tool Definitions (ETDI) specifically to address this attack class.

**Cross-Server Tool Shadowing:** When multiple MCP servers connect to the same client, a malicious server can inject descriptions that modify agent behavior toward *other trusted servers*, intercepting data without appearing in user-visible logs (Checkmarx, 2025).

**Authentication is "SHOULD" not "MUST":** The MCP spec uses "SHOULD" for server authorization broadly, though Authorization Servers must implement OAuth 2.1 where authorization is present. The overall effect is that server authentication is optional/strongly-recommended rather than mandatory, with no enforcement mechanism. The Stack Overflow Blog (2026) describes it as "an optional recommendation." Any developer can publish an unauthenticated MCP server.

**Horizontal Scaling:** MCP's stateful session model requires "sticky" routing — each client is pinned to a specific server instance. This breaks standard load balancing, auto-scaling, and serverless patterns. The MCP roadmap acknowledges this and targets a spec update for June 2026 (modelcontextprotocol.io, Roadmap).

**No Audit Trail Standard:** MCP has no built-in observability spec. Enterprise compliance teams must bolt on logging externally with no standard format.

### A2A

**Developer Accessibility:** A2A's comprehensive specification — covering multi-agent orchestration, deployment targets (Cloud Run, GKE, Agent Engine), signed Agent Cards — was inaccessible to most developers at launch. By September 2025, A2A had largely faded from developer discourse (fka.dev, 2025b).

**Agent Card Spoofing:** Agent Cards are fetched and trusted on first use without mandatory cryptographic verification. Signing is supported in v0.3+ but not enforced. Semgrep's security engineers describe this as expected to become "internet background radiation" at scale (Semgrep, 2025).

**Agent Session Smuggling:** Palo Alto Unit 42 documented a novel attack class where a malicious agent exploits A2A's stateful session model to inject covert instructions into established cross-agent sessions, hidden among benign traffic — with two proof-of-concepts demonstrated using Google's Agent Development Kit (Palo Alto Unit 42, 2025).

**Long-Lived Token Risk:** A2A's OAuth 2.0 implementation does not enforce short token expiry for sensitive transactions, enabling lateral abuse if tokens are exfiltrated (Cloud Security Alliance, 2025).

**Webhook SSRF:** A2A's webhook notification URLs must be validated against Server-Side Request Forgery. Orphaned streams without mandated termination allow stolen session tokens to silently intercept victim streams (Keysight, 2025).

### Cross-Cutting Risk: Prompt Injection

Both protocols are vulnerable to prompt injection through external content channels (documents, search results, emails, GitHub issues). No current specification for either protocol mandates sanitization of external content before it enters agent context. Microsoft has published guidance on protecting against indirect injection attacks in MCP-connected systems.

---

## 9. The Broader Protocol Landscape

| Protocol | Origin | Layer | Status (April 2026) |
|----------|--------|-------|---------------------|
| MCP | Anthropic, Nov 2024 | Agent ↔ Tool | De facto standard; 97M monthly SDK downloads |
| A2A | Google, Apr 2025 | Agent ↔ Agent orchestration | Strong enterprise backing; slow developer adoption |
| ANP | W3C Community Group | Decentralized peer-to-peer agents | Emerging; uses W3C DIDs; not production-ready |
| Agentic Commerce Protocol | OpenAI + Stripe | Agent ↔ Agent (payments) | Narrow-scope; powers ChatGPT Instant Checkout |

*Source: arXiv survey (2505.02279), GetStream (2026)*

---

## 10. Synthesis

MCP and A2A are genuinely complementary by specification but differ substantially in adoption trajectory and practical maturity.

**MCP** solved a problem developers had immediately (tool integration), was accessible from day one without new infrastructure, and compounded into a de facto standard with 97M monthly downloads and support from all major AI model providers. Its critical weaknesses are security (tool poisoning, rug pull, cross-server shadowing) and enterprise scaling (sticky sessions, no audit trail, optional auth).

**A2A** solved a problem enterprises anticipate at scale (cross-framework agent orchestration), required new infrastructure to be useful, and accumulated organizational commitments without comparable developer traction. Its v1.0.0 release (March 2026) and Linux Foundation governance suggest it is consolidating rather than collapsing — but the "complementary layers" framing has not yet driven widespread dual-protocol production deployments.

**The deepest unsolved problem cuts across both:** neither protocol has mandatory authentication enforcement, audit trail standards, or content sanitization requirements. Every enterprise deploying agents in production must build these layers externally. This is the most significant gap in the current agent protocol stack — and arguably the most interesting infrastructure opportunity in the space.

---

## Verification Notes

*Per the deep-research methodology, this report was independently audited by a verification agent after drafting.*

- **Sources checked:** 20 | **Verified:** 18 | **Cannot verify:** 2 | **Hallucinated:** 0
- **Corrections applied:** (1) The 97M downloads and 10,000+ servers figures are from Anthropic's Dec 9, 2025 AAIF announcement — not the Nov 25 MCP anniversary post, which was the original attribution. (2) MCP spec `2025-11-25` is not the latest — `2025-03-26` is current as of April 2026. (3) IBM's ACP merger announcement is dated Aug 29, 2025, not Sep 1. (4) The specific Auth0 claim about A2A→MCP identity propagation exists as a documented problem but could not be confirmed from the article body directly (page fetch returned only CSS/JS markup).

---

## References

**Primary Sources**

- Anthropic (2024). "Introducing the Model Context Protocol." Nov 25, 2024. https://www.anthropic.com/news/model-context-protocol
- Anthropic (2025c). "Donating the Model Context Protocol and Establishing the Agentic AI Foundation." Dec 9, 2025. https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation
- Google (2025a). "Announcing the Agent2Agent Protocol (A2A)." Google Developers Blog, Apr 9, 2025. https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/
- Google (2025b). "Agent2Agent Protocol Is Getting an Upgrade." Google Cloud Blog, Jul 31, 2025. https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade
- Linux Foundation (2025). "Linux Foundation Launches the Agent2Agent Protocol Project." Jun 23, 2025. https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents
- LFAI & Data (2025). "ACP Joins Forces with A2A." Aug 29, 2025. https://lfaidata.foundation/communityblog/2025/08/29/acp-joins-forces-with-a2a-under-the-linux-foundations-lf-ai-data/
- MCP Specification (2025). `modelcontextprotocol.io/specification/2025-11-25`. Current latest: `2025-03-26`.
- A2A Specification (2026). v1.0.0. https://a2a-protocol.org/latest/specification/
- MCP Roadmap. https://modelcontextprotocol.io/development/roadmap
- Microsoft (2025). "Empowering Multi-Agent Apps with A2A." Microsoft Cloud Blog, May 7, 2025. https://www.microsoft.com/en-us/microsoft-cloud/blog/2025/05/07/empowering-multi-agent-apps-with-the-open-agent2agent-a2a-protocol/
- OpenAI (2025). "Agentic AI Foundation." https://openai.com/index/agentic-ai-foundation/
- Atlassian (2025). "Introducing Atlassian's Remote MCP Server." https://www.atlassian.com/blog/announcements/remote-mcp-server

**Security Research**

- Invariant Labs (2025). "MCP Security Notification: Tool Poisoning Attacks." Apr 1, 2025. https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks
- Semgrep (2025). "A Security Engineer's Guide to the A2A Protocol." Dec 17, 2025. https://semgrep.dev/blog/2025/a-security-engineers-guide-to-the-a2a-protocol/
- Palo Alto Unit 42 (2025). "Agent Session Smuggling in Agent2Agent Systems." Oct 31, 2025. https://unit42.paloaltonetworks.com/agent-session-smuggling-in-agent2agent-systems/
- Cloud Security Alliance (2025). "Threat Modeling Google's A2A Protocol with the MAESTRO Framework." Apr 30, 2025. https://cloudsecurityalliance.org/blog/2025/04/30/threat-modeling-google-s-a2a-protocol-with-the-maestro-framework/
- LevelBlue (2025). "Agent in the Middle: Abusing Agent Cards in A2A." https://www.levelblue.com/blogs/spiderlabs-blog/agent-in-the-middle-abusing-agent-cards-in-the-agent-2-agent-protocol-to-win-all-the-tasks
- Stack Overflow Blog (2026). "Authentication and Authorization in Model Context Protocol." Jan 21, 2026. https://stackoverflow.blog/2026/01/21/is-that-allowed-authentication-and-authorization-in-model-context-protocol/
- Keysight (2025). "Potential Attack Surfaces in A2A." May 28, 2025. https://www.keysight.com/blogs/en/tech/nwvs/2025/05/28/potential-attack-surfaces-in-a2a

**Technical Analysis**

- arXiv:2505.02279. "A Survey of Agent Interoperability Protocols: MCP, ACP, A2A, and ANP." https://arxiv.org/html/2505.02279v1
- arXiv:2506.01333. "Mitigating Tool Squatting and Rug Pull Attacks in MCP." Jun 2025. https://arxiv.org/html/2506.01333v1
- arXiv:2506.01804. "A Study on the MCP × A2A Framework." Jun 2025. https://arxiv.org/pdf/2506.01804
- arXiv:2505.12490. "Improving A2A Protocol: Protecting Sensitive Data." May 2025. https://arxiv.org/html/2505.12490v3
- Auth0 (2025). "MCP vs A2A: A Guide to AI Agent Communication Protocols." Jul 10, 2025. https://auth0.com/blog/mcp-vs-a2a/
- Gravitee.io (2025). "Google's Agent-to-Agent (A2A) and Anthropic's MCP." https://www.gravitee.io/blog/googles-agent-to-agent-a2a-and-anthropics-model-context-protocol-mcp
- fka.dev (2025a). "Why A2A Doesn't Make Sense When We Already Have MCP." Apr 15, 2025. https://blog.fka.dev/blog/2025-04-15-why-googles-a2a-protocol-doesnt-make-sense/
- fka.dev (2025b). "What Happened to Google's A2A?" Sep 11, 2025. https://blog.fka.dev/blog/2025-09-11-what-happened-to-googles-a2a/
- Koyeb (2025). "A2A and MCP: Start of the AI Agent Protocol Wars?" https://www.koyeb.com/blog/a2a-and-mcp-start-of-the-ai-agent-protocol-wars
- AWS Open Source Blog (2025). "Open Protocols for Agent Interoperability Part 4: A2A." https://aws.amazon.com/blogs/opensource/open-protocols-for-agent-interoperability-part-4-inter-agent-communication-on-a2a/
- Willison, S. (2025). "MCP Has Prompt Injection Problems." Apr 9, 2025. https://simonwillison.net/2025/Apr/9/mcp-prompt-injection/
- Checkmarx (2025). "11 Emerging AI Security Risks with MCP." https://checkmarx.com/zero-post/11-emerging-ai-security-risks-with-mcp-model-context-protocol/
