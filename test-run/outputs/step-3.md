I now have sufficient data from primary and secondary sources. Let me synthesize the full analysis.

---

# MCP vs. A2A: Two Protocols Solving Different (But Converging) Problems in Agentic AI

**Thesis:** MCP and A2A are architecturally complementary — one handles vertical model-to-tool integration, the other handles horizontal agent-to-agent coordination — but they are economically competing for developer mindshare as each protocol's roadmap encroaches on the other's territory.

---

## Key Findings

| Dimension | MCP (Anthropic) | A2A (Google) |
|---|---|---|
| **Launch** | November 2024 | April 9, 2025 |
| **Governance** | Agentic AI Foundation (AAIF/Linux Foundation), Dec 2025 | Linux Foundation, June 23, 2025 |
| **Current version** | Spec 2025-11-25 | v1.0.0 (March 12, 2026) |
| **Scale** | 97M monthly SDK downloads; 10,000+ public servers | 23.1k GitHub stars; 150+ org ecosystem |
| **Core abstraction** | Tools, Resources, Prompts | Agent Cards, Tasks, Messages |
| **Integration axis** | **Vertical** (model ↔ tools/data) | **Horizontal** (agent ↔ agent) |
| **Transport** | JSON-RPC 2.0 over stdio or Streamable HTTP | JSON-RPC 2.0 over HTTP(S) + gRPC (v0.3+) |
| **State management** | Stateful sessions; async Tasks experimental (SEP-1686, 2026) | Async-first; three-level state (session, task, agent-internal) |
| **Discovery** | Planned `.well-known` (2026 roadmap) | Built-in `/.well-known/agent-card.json` from day one |

---

## 1. Architecture Deep-Dive

### MCP: The Vertical Integration Layer

MCP was explicitly inspired by the Language Server Protocol (LSP): just as LSP standardized the IDE-to-language-tooling interface, MCP standardizes the LLM-to-external-system interface (Anthropic, *Model Context Protocol Specification 2025-11-25*).

**Participants:**
- **Hosts**: LLM applications (Claude Desktop, Cursor, VS Code) that initiate connections
- **Clients**: Connectors within the host managing the protocol lifecycle
- **Servers**: Services exposing capabilities (GitHub, databases, APIs, file systems)

**Three server-side primitives:**
- **Tools** — Functions the AI model *calls* (execute code, write to DB, call APIs). These represent arbitrary code execution and the spec treats them as untrusted unless from a verified server.
- **Resources** — Context the AI model *reads* (files, database rows, API responses). Identified by URIs.
- **Prompts** — Reusable message templates and workflows shared across applications.

**Three client-side primitives (servers can invoke back):**
- **Sampling** — Server-initiated LLM invocation (recursive model calls mid-task)
- **Roots** — Server queries about filesystem boundaries the client operates in
- **Elicitation** — Server requests additional user input mid-session via a JSON schema form

**Transport evolution:** MCP launched with stdio (local subprocess), added HTTP+SSE, and in 2025 released *Streamable HTTP* — its most significant transport update, enabling session resumption and message redelivery. This directly enabled the multi-agent patterns Microsoft later demonstrated could be built on MCP alone.

**Auth:** OAuth 2.1 comprehensive framework; MCP servers are classified as OAuth 2.0 Resource Servers; RFC 8707 resource parameters bind access tokens to specific servers. Schema is TypeScript-first with JSON Schema export for cross-language compatibility.

---

### A2A: The Horizontal Coordination Layer

A2A's fundamental premise is that MCP doesn't solve the case where *an autonomous agent needs to talk to another autonomous agent* — not call a tool, but negotiate, delegate, and track work across an organizational or vendor boundary (Google Developers Blog, *A2A: A New Era of Agent Interoperability*, April 2025).

**Three-layer architecture:**
- **Layer 1** — Protocol-agnostic data model: `Task`, `Message`, `Artifact`, `Part`, `SecurityScheme`
- **Layer 2** — Abstract operations: `SendMessage`, `GetTask`, `ListTasks`, `CancelTask`, `SubscribeToTask`
- **Layer 3** — Protocol bindings: JSON-RPC over HTTP POST, gRPC (added v0.3, July 2025)

The normative source of truth is `spec/a2a.proto`; all SDKs derive from it.

**Agent Cards** — The key differentiator from MCP. Every A2A agent publishes a JSON manifest at `/.well-known/agent-card.json` declaring: identity, endpoint URL, authentication schemes (API Key, HTTP Auth, OAuth2, OpenID Connect, Mutual TLS), capability flags (`streaming`, `pushNotifications`, `extendedAgentCard`), and Skills. Cards can be cryptographically signed (v0.3+). Extended cards provide authenticated clients additional detail beyond the public card.

**Task lifecycle** — Tasks move through states: `working` → `input-required` / `auth-required` → `completed` / `failed` / `canceled` / `rejected`. This models *long-running work* as a first-class citizen, unlike MCP's original synchronous tool-call model.

**Three async delivery mechanisms** (all built-in from v1):
1. **Polling**: `GetTask` on interval
2. **Streaming**: SSE persistent connection (requires `capabilities.streaming: true`)
3. **Push notifications**: Agent POSTs to client webhook (requires `capabilities.pushNotifications: true`)

**Three-level state management:** session-level (via `contextId`), task-level (TaskStore persistence survives server restarts), and agent-internal state (deliberately opaque — not visible across agent boundaries by design).

**SDKs as of v1.0.0** (March 2026): Python (`pip install a2a-sdk`), JavaScript (`npm install @a2a-js/sdk`), Go (`go get github.com/a2aproject/a2a-go`), Java (Maven), .NET (NuGet).

---

## 2. What Each Solves That the Other Cannot (by Design)

### Problems A2A solves that MCP explicitly does not address

**1. Cross-vendor/cross-framework agent discovery.** MCP has no built-in discovery standard — a client must already know a server's URL. A2A's `/.well-known/agent-card.json` lets any HTTP client discover what an agent can do, what it costs, what auth it requires, and what skills it has — dynamically, at runtime, without code changes. Google's kitchen manager example: adding a new specialist agent is "as simple as adding a new URL" (Google Developers Blog).

**2. Opaque delegation with capability negotiation.** In MCP, the host orchestrates tools; the model sees tool schemas. In A2A, agents collaborate *without internal state visibility* — Agent B doesn't know how Agent A is implemented, what model it uses, or what tools it has. This is critical for enterprise scenarios where Agent A might be a competitor's system.

**3. Long-running async task tracking across agent boundaries.** A task in A2A is a durable entity with a lifecycle, a unique ID, and persistent state. An orchestrator agent can `SendMessage`, receive a Task ID, check back days later via `GetTask`, or receive a push notification on completion. MCP originally had no equivalent — its Tasks primitive (SEP-1686) only entered experimental status in 2026 (*2026 MCP Roadmap*, modelcontextprotocol.io).

**4. Multi-modal interaction modality negotiation.** A2A Messages contain typed `Parts` — text, file references, or structured JSON — and agents negotiate which modalities they support via Agent Cards. MCP's tool calls pass arguments as JSON with no equivalent "what format do you prefer?" negotiation layer.

**5. Push notifications across organizational boundaries.** A2A's webhook-based push model lets an external agent POST a completion notification to a registered callback URL — no polling, no persistent connection. MCP has no equivalent server-to-external-client push mechanism in its base spec.

---

### Problems MCP solves that A2A explicitly does not address

**1. Tool invocation standardization.** MCP is the *lingua franca* for "model calls function, gets result." Any MCP-compatible tool (there are 1,600+ public servers as of March 2026) can be plugged into any MCP-compatible host. A2A has no concept of tools — it only knows about agents.

**2. Contextual grounding with live data.** MCP Resources let a model read a file, query a database, or fetch an API response *in context* — the data flows into the model's context window. A2A has no equivalent; it assumes the agents themselves have already resolved their data needs.

**3. Prompt template sharing.** MCP Prompts enable reusable, parameterized message templates — a concept with no A2A counterpart.

**4. Server-initiated LLM calls (Sampling).** An MCP server can request the host application to perform an LLM inference (recursive AI calls mid-task). This enables agentic loops within a single server context. A2A has no equivalent because it treats agent internals as opaque.

**5. Mid-session user input requests (Elicitation).** An MCP server can, during execution, send a structured form schema asking the user for additional input (added June 2025 spec). A2A handles `input-required` task states, but with no structured schema for what input is needed.

**6. The "last mile" for existing software.** MCP's killer application is wrapping existing APIs, databases, and SaaS tools in a standardized interface. The 97M monthly downloads reflect that thousands of developers have written MCP servers for tools they already use. A2A requires the counterparty to *also* implement A2A — there's no "wrap your REST API in A2A" story as simple as MCP's.

---

## 3. Are They Complementary or Competing?

### The official position: complementary layers

Google's official positioning is unambiguous: "A2A is intended to be complementary to Anthropic's MCP" (Google Developers Blog, April 2025). Both Google (via its ADK) and Anthropic support using them together. The canonical pattern:

```
[User] → [Orchestrator Agent]
              ↓ uses MCP         ↓ uses A2A
         [Tool Servers]    [Specialist Agents]
         (databases, APIs) (billing agent, research agent)
```

Each specialist agent internally uses MCP for its own tool access; agents coordinate externally via A2A.

### The real tension: converging feature roadmaps

**MCP expanding into A2A territory:**
- Tasks primitive (SEP-1686) adds A2A-style async task tracking to MCP (experimental, 2026 roadmap)
- `.well-known` metadata discovery on 2026 roadmap — directly mirrors A2A's Agent Card mechanism
- Microsoft demonstrated that A2A-style agent coordination can already be built on MCP using StreamableHTTP session resumption, durability via resource links, and elicitation (*Microsoft Developer Blog, "Can You Build Agent2Agent Communication on MCP? Yes!"*)

**A2A's acknowledged limitation:** A2A does not address tool invocation at all. It *requires* MCP (or equivalent) as a dependency for any agent that needs external context. This structural dependency prevents A2A from ever fully displacing MCP.

**Solomon Hykes (Dagger CEO) on developer economics:** "In theory they can coexist, in practice I foresee a tug of war. Developers can only invest their energy into so many ecosystems" (quoted in Koyeb, *A2A and MCP: Start of the AI Agent Protocol Wars?*).

The tug-of-war is real at the implementation layer: frameworks like LangChain, CrewAI, and LlamaIndex must decide how much native A2A support to build versus how much to extend MCP's multi-agent capabilities. Most, as of early 2026, are implementing both.

---

## 4. Adoption: The Numbers

### MCP

| Milestone | Date | Monthly SDK Downloads |
|---|---|---|
| Launch | Nov 2024 | ~2M |
| OpenAI adoption | Apr 2025 | ~22M |
| Microsoft Copilot Studio | Jul 2025 | ~45M |
| AWS integration | Nov 2025 | ~68M |
| Current | Mar 2026 | **97M** |

10,000+ active public MCP servers; 1,600+ listed in public registries. All major AI providers (OpenAI, Anthropic, Microsoft, AWS, Google) supporting MCP as of early 2026 (*Use Apify, "MCP Standard and Ecosystem 2026"*). Anthropic donated MCP to the Agentic AI Foundation (AAIF) under the Linux Foundation in December 2025 — co-founded with Block and OpenAI, marking a decisive industry standardization moment.

### A2A

Launched with 50+ technology partners; grew to 150+ organizations by mid-2025. Linux Foundation governance announced June 23, 2025 at Open Source Summit North America, with founding partners including **AWS, Cisco, Salesforce, SAP, Microsoft, and ServiceNow**. v1.0.0 released March 12, 2026 with 23.1k GitHub stars, 2.3k forks, 551 commits (*a2aproject/A2A GitHub*). A DeepLearning.AI course on A2A implementation (with Google Cloud and IBM Research) launched alongside v1.0.0.

**Caveat:** One critical secondary source (fka.dev, September 2025) claimed A2A's development "slowed significantly" relative to MCP and characterized its enterprise-first approach as a barrier to developer adoption. This claim appears *partially* credible — MCP's adoption numbers vastly outpace A2A's — but is likely overstated given the v1.0.0 release in March 2026 and the Linux Foundation governance structure with major cloud vendors. The "slowed" framing may reflect slower *indie developer* adoption, not enterprise implementation pace.

---

## 5. The ACP Wild Card

A third protocol deserves mention: IBM's **Agent Communication Protocol (ACP)**, launched March 2025 under Linux Foundation alongside the BeeAI platform. ACP occupies the same inter-agent coordination space as A2A but with key differences:

- **Pure REST** (not JSON-RPC wrapper), enabling invocation with cURL or Postman without specialized libraries
- **MIME-type extensible messages** rather than A2A's pre-defined Part types — more flexible but less type-safe
- **Build-time discovery** (metadata embedded at build, discoverable via Docker registries) vs. A2A's runtime `/.well-known` discovery
- Lighter-weight; targets smaller/individual agent deployments where A2A's full complexity is overkill

The ACP/A2A distinction is directionally: A2A is enterprise-first (cross-organizational, cross-vendor federation); ACP is developer-first (intra-platform, rapid agent composition). Both target a gap MCP doesn't fill (*agentcommunicationprotocol.dev, "MCP and A2A"*; *WorkOS, "IBM's Agent Communication Protocol"*).

---

## Source Conflicts

| Claim | Source A | Source B | Assessment |
|---|---|---|---|
| A2A development status (Sep 2025) | fka.dev: "development slowed, MCP consolidated ecosystem" | GitHub: v1.0.0 shipped March 2026, 23.1k stars; LF partners: AWS, Cisco, Microsoft | fka.dev likely captured a *temporary* slowdown in indie adoption; enterprise trajectory remained strong |
| A2A vs MCP relationship | Google, Anthropic, IBM: "complementary, not competing" | Solomon Hykes, Koyeb: "tug of war for developer mindshare" | Both are true at different levels of analysis; architectural complementarity doesn't preclude economic competition |
| Can A2A be built on MCP? | Microsoft: "Yes, via StreamableHTTP + elicitation" | A2A spec authors: "Different protocol, fills different need" | Microsoft's argument is technically valid for many use cases; A2A's value is standardizing what Microsoft's approach requires custom implementation of |

---

## Open Questions

1. **Will MCP's Tasks primitive (SEP-1686) reach parity with A2A's task model?** If so, much of A2A's architectural advantage disappears for intra-org deployments.
2. **Will the `.well-known` discovery standard in MCP's 2026 roadmap supersede A2A's Agent Cards?** Both aim to solve the same "how does an agent know what another agent can do" problem.
3. **Can ACP challenge A2A at the enterprise level**, or does A2A's 150+ org ecosystem and v1.0.0 stability lock in enterprise preference?
4. **As the tool/agent boundary blurs** — tools become increasingly long-running and agent-like — which abstraction layer wins? The agent paradigm (A2A) or the tool paradigm (MCP)?
5. **Governance convergence**: Both protocols are now under Linux Foundation entities (AAIF for MCP, standalone A2A project for A2A). Does this create pressure for eventual merger or formal interoperability spec?

---

## Sources

1. [Announcing the Agent2Agent Protocol (A2A) — Google Developers Blog](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) — primary source, April 2025
2. [Developer's Guide to AI Agent Protocols — Google Developers Blog](https://developers.googleblog.com/developers-guide-to-ai-agent-protocols/) — official positioning of A2A vs MCP
3. [A2A Protocol Specification (a2a-protocol.org)](https://a2a-protocol.org/latest/specification/) — primary technical spec
4. [Agent2Agent GitHub Repository](https://github.com/a2aproject/A2A) — v1.0.0, March 2026
5. [Agent2Agent Protocol Upgrade — Google Cloud Blog](https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade) — v0.3 release notes
6. [Model Context Protocol Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — primary technical spec
7. [One Year of MCP: November 2025 Spec Release — MCP Blog](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/)
8. [2026 MCP Roadmap — MCP Blog](http://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/) — roadmap items including Tasks SEP-1686, transport evolution
9. [Linux Foundation Launches A2A Protocol Project](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents) — governance announcement, June 23, 2025
10. [Can You Build Agent2Agent Communication on MCP? Yes! — Microsoft Developer Blog](https://developer.microsoft.com/blog/can-you-build-agent2agent-communication-on-mcp-yes) — technical argument for MCP sufficiency
11. [A2A and MCP: Start of the AI Agent Protocol Wars? — Koyeb](https://www.koyeb.com/blog/a2a-and-mcp-start-of-the-ai-agent-protocol-wars) — competitive framing + Solomon Hykes quote
12. [What Happened to Google's A2A? — fka.dev](https://blog.fka.dev/blog/2025-09-11-what-happened-to-googles-a2a/) — critical September 2025 assessment ⚠️ *partially outdated by March 2026 v1.0.0 release*
13. [MCP and A2A — Agent Communication Protocol (ACP)](https://agentcommunicationprotocol.dev/about/mcp-and-a2a) — IBM ACP positioning
14. [Comparison of MCP, ACP, A2A — Niklas Heidloff](https://heidloff.net/article/mcp-acp-a2a-agent-protocols/) — three-protocol comparison
15. [MCP Standard and Ecosystem 2026 — Apify](https://use-apify.com/blog/mcp-standard-ecosystem-2026) — adoption trajectory numbers
16. [A2A vs MCP — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2025/05/a2a-and-mcp/) — technical comparison
17. [Gravitee: Google's A2A and Anthropic's MCP](https://www.gravitee.io/blog/googles-agent-to-agent-a2a-and-anthropics-model-context-protocol-mcp) — API gateway/enterprise angle
