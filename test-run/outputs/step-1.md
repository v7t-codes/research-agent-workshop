Here is the full analysis, built directly from official specifications, Google's launch documentation, Anthropic's MCP spec, and current ecosystem data.

---

# A2A vs MCP: Architecture, Use Cases, Adoption, and Complementarity

---

## 1. Model Context Protocol (MCP)

### Origin and Framing

Anthropic published MCP in **November 2024** as an open standard. The stated analogy in the specification (modelcontextprotocol.io, 2025-06-18) is to the **Language Server Protocol (LSP)**: just as LSP standardized how IDE tooling integrates programming language support across editors, MCP standardizes how LLM applications integrate external context and tools. The protocol is documented at modelcontextprotocol.io and hosted openly; Anthropic holds no vendor lock on its use.

### Architecture

MCP follows a **Host → Client → Server** three-tier model.

```
Application Host Process
  ├── Client 1  ──►  Server A (Files & Git, local)
  ├── Client 2  ──►  Server B (Database, local)
  └── Client 3  ──►  Server C (External API, remote)
```

**Host**: The LLM application (Claude Desktop, Cursor, VS Code). It manages security policy, user authorization decisions, and context aggregation across clients. It creates and controls all client instances.

**Client**: Lives inside the host; maintains a 1:1 stateful session with exactly one server. Handles capability negotiation, subscriptions, and bidirectional message routing. Critically, each client is *isolated* — servers cannot "see into" each other, and no server sees the full conversation history.

**Server**: A process (local subprocess or remote HTTP service) that exposes one or more of three primitive types:
- **Tools** — callable functions with JSON Schema definitions (e.g., `query_database(sql: string) → ResultSet`)
- **Resources** — data sources or documents the agent or user can access
- **Prompts** — reusable templated message workflows

The server can also issue requests back to the host via the client:
- **Sampling** — request the host's LLM to generate a completion (server-initiated agentic behavior)
- **Roots** — inquire about filesystem or URI boundaries
- **Elicitation** — request additional information from the user

### Transport and Protocol

- **Wire format**: JSON-RPC 2.0 for all messages (Requests, Responses, Notifications)
- **Local transport**: stdio (subprocess pipe) — the dominant pattern for developer tooling
- **Remote transport**: HTTP + Server-Sent Events (SSE) for streaming

Capability negotiation happens at session initialization: both sides declare what they support, and the session is constrained to the intersection. This enables backward compatibility — a client and server from different versions of the spec can still interoperate within their shared capability set.

### Design Principles (per official spec)

The spec (modelcontextprotocol.info, draft) enumerates four explicit principles:
1. **Servers should be easy to build** — clear separation, minimal implementation overhead
2. **Servers should be highly composable** — modular design, multiple servers combined seamlessly
3. **Servers should not see the full conversation** — host enforces isolation; security boundary is architectural
4. **Progressive capability addition** — core protocol is minimal; features negotiated at session time

### Security Model

MCP requires explicit **user consent** before tool invocation. The spec states: *"Users must explicitly consent to and understand all data access and operations... Hosts must obtain explicit user consent before invoking any tool."* Tool annotations (capability descriptions) are treated as untrusted unless obtained from a trusted server. This is deliberately conservative — the assumption is that tool execution is code execution and must be treated accordingly.

### Adoption (as of March–April 2026)

**Client support** (per AgentRank, March 2026): Claude Code, Claude Desktop, Cursor, GitHub Copilot, VS Code (native via microsoft/vscode issue #287660), Windsurf, Cline, Zed.

**Server ecosystem**: 25,632 repositories indexed on AgentRank (March 2026). Official servers from Redis, MongoDB, AWS, Azure, GCP, HashiCorp, Snyk. Top categories: database access (847 repos in that category alone), DevOps automation, developer tooling.

**Growth trajectory**: 2× growth Q3→Q4 2025, 2× again Q1 2026 (AgentRank). The one-server-per-integration pattern means the repository count scales with the number of distinct tools, explaining rapid proliferation.

---

## 2. Agent2Agent Protocol (A2A)

### Origin and Framing

Google DeepMind published A2A in **April 2025**, explicitly positioning it as a complement to MCP. The launch blog post (Google Developers Blog, April 9, 2025) states: *"A2A is an open protocol that complements Anthropic's Model Context Protocol (MCP), which provides helpful tools and context to agents."* It launched with contributions from **50+ technology partners** — Atlassian, Box, Cohere, Intuit, LangChain, MongoDB, PayPal, Salesforce, SAP, ServiceNow, UKG, Workday — plus major services firms including Accenture, BCG, Capgemini, Deloitte, McKinsey, PwC, TCS, and Wipro.

The stated motivation (per the launch post): enterprises are deploying multiple specialized agents built by different vendors across different frameworks. Without a coordination protocol, each integration requires custom glue code. A2A provides the standard so agents from Salesforce, SAP, and Google can collaborate on a single workflow without either vendor knowing the implementation details of the other.

### Architecture

A2A is structured around two roles:

**Client Agent**: Formulates tasks, delegates work, assembles results. Analogous to an orchestrator.

**Remote Agent**: Advertises capabilities, receives tasks, executes them, and returns artifacts. Analogous to a specialized sub-agent or worker.

The core abstractions (per a2a-protocol.org specification):

**Agent Card** — A JSON manifest served at `/.well-known/agent.json` (or `/.well-known/agent-card.json` in some implementations). Describes the agent's name, capabilities, supported modalities, and authentication requirements. This is how agents discover each other — no central registry required, just HTTP discovery at a known path. Example fields: supported input/output modalities, task types the agent can handle, authentication schemes.

**Task** — The fundamental unit of work. Has a unique ID and a defined **status lifecycle**:
```
submitted → working → (input_required) → completed | failed | canceled
```
Tasks can complete immediately or run for hours/days with human-in-the-loop steps. The task ID allows the client to poll or receive push updates asynchronously.

**Artifacts** — The outputs a remote agent produces: text, files, structured data, images, etc. Streamed back to the caller via SSE during execution.

**Parts** — Within each message, a "part" is a fully formed piece of content with a specified content type. This enables **user experience negotiation**: client and remote agents can negotiate whether to use iframes, web forms, video, or plain text, based on the client's declared UI capabilities.

**Push Notifications** — Webhook callbacks for long-running async tasks when SSE isn't appropriate (e.g., tasks that take hours; the server calls back when done).

### Transport and Protocol

- **Transport**: HTTP with SSE for streaming results
- **Data format**: JSON throughout
- **Authentication**: Standard HTTP auth — OAuth 2.0, API keys, bearer tokens. The spec requires parity with OpenAPI authentication schemes.
- **Discovery**: HTTP GET to `/.well-known/agent.json` — no special protocol required, just DNS + HTTP

### Design Principles (per launch blog, April 2025)

Google enumerated five explicit principles:
1. **Embrace agentic capabilities** — agents collaborate *as agents*, not as tools; they can have memory, internal reasoning, and their own tool stacks
2. **Build on existing standards** — HTTP, SSE, JSON-RPC; no new infrastructure needed
3. **Secure by default** — enterprise-grade auth, OAuth 2.0 parity
4. **Long-running task support** — from seconds to days; real-time status updates throughout
5. **Modality agnostic** — text, audio, video streaming supported

### Adoption (as of March–April 2026)

**Framework support**: Google ADK (native, one-line `to_a2a()` wrapper), LangGraph, CrewAI, Salesforce Agentforce, SAP Joule.

**Enterprise integrations**: Salesforce, SAP, ServiceNow, Atlassian Rovo, UiPath, UKG — all committed at launch to implementing A2A-compatible agents.

**Repository count**: ~2,400 indexed on AgentRank (March 2026). Concentrated in three categories: Agent Development Kits (Google ADK, LangGraph, CrewAI), orchestration layers, and enterprise adapters wrapping Salesforce/SAP/ServiceNow as A2A-compatible agents.

The 10× gap in repo count vs MCP reflects both MCP's earlier launch (5 months earlier) and the structural difference: MCP servers are often single-purpose point integrations (one repo per tool), while A2A implementations are typically heavier orchestration frameworks.

---

## 3. Side-by-Side Comparison

| Dimension | MCP | A2A |
|---|---|---|
| **Axis** | Vertical: agent → tool/data | Horizontal: agent → agent |
| **Core question** | "What tools can I use?" | "What agents can I hire?" |
| **Primary abstraction** | Tools, Resources, Prompts | Tasks, Artifacts, Agent Cards |
| **Who talks to what** | Agent to deterministic APIs/tools | Autonomous agent to autonomous agent |
| **Computation model** | Synchronous function call | Async task with lifecycle |
| **Transport (local)** | stdio subprocess | N/A (inherently networked) |
| **Transport (remote)** | HTTP + SSE | HTTP + SSE |
| **Discovery** | Protocol-native `tools/list` at session start | HTTP GET to `/.well-known/agent.json` |
| **Session model** | Stateful, persisted session | Stateless per task (ID-correlated) |
| **Auth** | Env vars or header injection at transport | OAuth 2.0, API keys, bearer (HTTP-native) |
| **Long-running ops** | Not natively designed for this | First-class (task lifecycle + push notifications) |
| **UI/modality negotiation** | No | Yes (Parts with content-type negotiation) |
| **Published by** | Anthropic (Nov 2024) | Google DeepMind (Apr 2025) |
| **GitHub repos** | 25,632 (AgentRank, Mar 2026) | ~2,400 (AgentRank, Mar 2026) |
| **Client support** | All major AI coding tools | Google ADK, LangGraph, CrewAI |

---

## 4. What Problems Each Solves That the Other Does Not

### MCP-only problems

**1. Standardized, zero-overhead tool access.**
Before MCP, connecting an agent to an external system required writing a custom JSON Schema function definition *per model* and *per client*. An MCP server written once works identically in Claude Desktop, Cursor, GitHub Copilot, and VS Code. The Alpha Vantage MCP server (per Samplay, Google Cloud Community, March 2026) exposes 60+ financial data tools via a single HTTP endpoint — the agent discovers all of them at startup without any manual schema definitions.

**2. Local-first, process-level integration.**
The stdio transport allows MCP servers to run as local subprocesses — reading files, querying local databases, running shell commands — without any network exposure. This is central to coding assistants: Claude Code's file system access, git operations, and terminal execution all run via MCP over stdio.

**3. Fine-grained, user-visible consent.**
MCP's security model requires explicit per-tool user consent. This is a UX capability that A2A doesn't address — A2A assumes enterprise-level authentication but doesn't specify per-action user approval flows.

**4. Context/Resource sharing.**
MCP's Resources primitive allows agents to share structured data (documents, database records, API responses) as part of the session context. This has no direct A2A equivalent — A2A passes task artifacts, not session-scoped resources.

**5. Cross-client portability today.**
MCP has 7+ major AI client integrations. A2A's client support is concentrated in Google ADK and a few orchestration frameworks. If you want an integration that works across all AI coding tools, MCP is the only viable choice today.

### A2A-only problems

**1. Delegating to autonomous, non-deterministic sub-agents.**
MCP tools are *deterministic functions* — clear inputs, clear outputs, synchronous execution. An A2A agent is an autonomous process: it can run its own reasoning loop, call its own tools (via MCP), handle uncertainty, and produce outputs that take seconds to hours. The distinction is explicit in the AgentRank analysis (March 2026): *"If you'd be tempted to put an LLM inside your MCP tool handler, you probably want an A2A agent instead."*

**2. Cross-vendor agent interoperability.**
This is A2A's primary enterprise motivation (Google Developers Blog, April 2025). A Salesforce CRM agent and an SAP ERP agent can collaborate on a customer workflow without either knowing the other's implementation. The Agent Card is the entire contract — discovery, capability description, and auth requirements in a single JSON document. MCP has no equivalent mechanism for inter-agent trust and capability advertisement.

**3. Long-running task management.**
The task lifecycle (`submitted → working → completed/failed`) with SSE streaming and push notification webhooks is designed for operations that span minutes to days, potentially with human-in-the-loop checkpoints. The MCP spec's request-response model (per modelcontextprotocol.io, 2025-06-18) includes progress tracking and cancellation, but it is not architected around multi-hour async workflows with external callback patterns.

**4. Streaming progressive outputs.**
A2A's Artifacts system streams partial results back via SSE as the remote agent works. An orchestrator can display incremental progress (e.g., a research agent returning article summaries as it finds them) without waiting for the entire task to complete. MCP does support streaming responses but within a single synchronous tool call.

**5. UI/modality negotiation.**
Each A2A message includes "parts" with specified content types, and the protocol supports explicit negotiation of what the client's UI can render (iframes, video, web forms). MCP has no equivalent — it returns tool results and trusts the host to render them.

**6. Agent specialization at scale.**
The philosophical bet in A2A is that monolithic agents hit capability and cost ceilings — you want a research agent, a code agent, a data analyst, each specialized and independently maintained. A2A provides the coordination layer that lets these specialists compose into a system. MCP cannot express this architecture.

---

## 5. Are They Complementary or Competing?

**They are explicitly complementary, and Google said so at A2A's launch.**

The Google Developers Blog (April 9, 2025) states directly: *"A2A is an open protocol that complements Anthropic's Model Context Protocol (MCP)."* This is not marketing hedging — it reflects a genuine architectural separation.

The reference architecture that has emerged in production (documented in AgentRank March 2026 and implemented in Google ADK) is:

```
User
  │
  ▼
Orchestrator Agent
  │  (A2A: capability discovery via Agent Cards)
  ├──► Research Agent  ──► [MCP: web search, database tools]
  ├──► Code Agent      ──► [MCP: filesystem, git, terminal]
  ├──► Data Agent      ──► [MCP: SQL, analytics APIs]
  └──► Writer Agent    ──► [MCP: document editing tools]
              │
              ▼
        Assembled Result (via A2A Artifacts)
```

**A2A operates horizontally** (between agents at the same level of abstraction). **MCP operates vertically** (between an agent and the tools/data it uses). They serve different layers of the stack and do not overlap in their core use cases.

The only point of *apparent* competition is at the boundary: could you wrap an MCP server as an A2A agent? Technically yes — and this is done when the MCP tool is complex enough to warrant its own reasoning loop. But this is composition, not conflict.

**Google ADK makes the complementarity concrete in code** (per Samplay, Google Cloud Community, March 2026):

```python
# MCP: give the agent its tools
toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url=MCP_URL)
)
root_agent = LlmAgent(model="gemini-2.5-flash", tools=[toolset, ...])

# A2A: expose the agent as a network service for other agents to hire
a2a_app = to_a2a(root_agent, port=10000)
# Now accessible at GET /.well-known/agent-card.json and POST /
```

`McpToolset` and `to_a2a()` are different layers of the same ADK framework — one gives the agent capabilities, the other exposes the agent to the network. They don't interfere.

---

## 6. Security and Identity

Auth0 (Johnson, July 10, 2025) identified the emerging security gap: *"Whether an agent is calling a tool via MCP or delegating to another agent via A2A, we need ways to: authenticate agent identities, control what they can access, trace their behavior."*

- **MCP security** is user-consent-centric: the user approves each tool invocation; the host enforces isolation between servers; servers cannot see the full conversation.
- **A2A security** is enterprise-auth-centric: OAuth 2.0, API keys, bearer tokens at the HTTP layer; Auth0 is formally partnering with Google Cloud to define the A2A auth spec (Auth0 blog, July 2025).

Neither protocol alone solves the full identity problem for multi-agent systems. MCP handles *user → agent* trust; A2A is building out *agent → agent* trust. The field notes that agent identity (proving that "this request came from a legitimate Salesforce agent, not an impersonator") is still an open problem at the protocol level.

---

## 7. Current Limitations and Open Questions

**MCP limitations** (flagged in the spec):
- No native multi-agent coordination — you can run multiple MCP servers per host, but agents don't communicate through MCP
- The stdio transport is local-only; remote MCP requires HTTP+SSE setup
- Sampling (server-requesting an LLM completion) is implemented inconsistently across hosts

**A2A limitations** (per ecosystem data):
- Much smaller client ecosystem — not yet supported in Claude Desktop, Cursor, or Copilot directly
- Agent Card discovery is HTTP-pull, not broadcast — no registry or discovery mesh
- The spec (as of April 2025) was still in draft; a production-ready version was planned for "later 2025" (per launch blog)
- Smaller open-source ecosystem (~2,400 repos vs 25,632 for MCP) means fewer off-the-shelf implementations

---

## 8. Summary for Research Purposes

| Question | Answer |
|---|---|
| What is MCP? | Anthropic's standard for agent→tool/data access. Published Nov 2024. |
| What is A2A? | Google's standard for agent→agent task delegation. Published Apr 2025. |
| Key MCP primitive | Tool (callable function with JSON Schema) |
| Key A2A primitive | Task (unit of work with lifecycle) + Agent Card (capability manifest) |
| Are they competing? | No — explicitly complementary by design and by Google's own statement |
| Reference architecture | A2A coordinates between agents; MCP gives each agent its tools |
| Dominant implementation | Google ADK natively implements both (`McpToolset` + `to_a2a()`) |
| MCP ecosystem size | 25,632 GitHub repos (AgentRank, Mar 2026); every major AI client |
| A2A ecosystem size | ~2,400 GitHub repos (AgentRank, Mar 2026); concentrated in enterprise frameworks |
| Best single-protocol choice | MCP if you need tools; A2A if you need multi-agent orchestration; both for production systems |

---

*Note: As of April 2026, A2A was approximately 11 months old. Ecosystem data and spec details should be verified against the current a2aproject/A2A GitHub and modelcontextprotocol.io for any updates.*

ENDOFFILE
echo "Saved"</parameter>
<parameter name="description">Save comprehensive research analysis to sources directory</parameter>
</invoke>
