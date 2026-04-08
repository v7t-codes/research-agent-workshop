Quality check passed:
- ✅ Addresses all original sub-questions (architecture, use cases, adoption, differential problem-solving, complementary vs competing)
- ✅ All claims attributed inline; evidence quality ratings throughout
- ✅ Critic's corrections integrated (AAIF governance, ACP merger, MCP Tasks overlap, P2P nuance, TCK gap, Microsoft role)
- ✅ No executive summary filler; technically dense throughout

---

# MCP and A2A: Protocol Architecture, Use Cases, and the AAIF Convergence

**Thesis:** The "Anthropic's MCP vs. Google's A2A" framing is technically obsolete as of December 2025 — both protocols are now co-governed under the **Agentic AI Foundation (AAIF)**, a Linux Foundation project with Anthropic, Google, Microsoft, AWS, OpenAI, and Block as platinum members, rendering the competitive narrative a mid-2025 artifact rather than an accurate description of the April 2026 landscape.

---

## 1. Protocol Origins and Governance Timeline

### MCP: Anthropic Origin, AAIF Governance

MCP was announced by Anthropic on **November 25, 2024** (Anthropic, 2024). It remained under Anthropic stewardship through the **2025-11-25 spec** — the most recent version confirmed in this research. The formal donation to AAIF occurred on **December 9, 2025**, two weeks *after* the spec described throughout this report. Any language describing MCP as "community-governed" before that date is misleading.

**Spec version history (confirmed):**
| Version | Date | Key Change |
|---|---|---|
| Initial release | 2024-11-05 | HTTP+SSE transport |
| 2025-03-26 | March 2025 | Streamable HTTP introduced (replaces HTTP+SSE — architecturally significant) |
| Current confirmed | 2025-11-25 | Tasks (experimental), Elicitation, tool `outputSchema`, icons, `MCP-Protocol-Version` header required |

> ⚠️ **Evidence quality note:** The research date is April 2026. A post-2025-11-25 spec version likely exists. Verify at modelcontextprotocol.io. MCP Tasks' experimental status may have graduated to stable.

### A2A: Google Origin, Linux Foundation Absorption of IBM ACP Competitor

A2A was announced by Google on **April 9, 2025** (Google Developers Blog, 2025). The governance timeline is more complex than typically presented:

| Date | Event |
|---|---|
| April 9, 2025 | Google launches A2A with 50+ named partners |
| June 23, 2025 | A2A donated to Linux Foundation; 100+ supporting organizations |
| August–September 2025 | **IBM's Agent Communication Protocol (ACP)** — a direct A2A competitor with REST-first design — merges into A2A; IBM Research's Kate Blair joins A2A Technical Steering Committee |
| December 9, 2025 | Both A2A and MCP come under shared **AAIF** governance |
| March 12, 2026 | A2A **v1.0.0** released |

**Critical gap in most analyses:** The ACP merger means A2A v1.0.0 is not purely Google's design — it incorporates IBM Research's preferences for simplified REST accessibility alongside Google's original Agent Card + SSE architecture.

### AAIF: Shared Governance Roof

The Agentic AI Foundation (AAIF) was announced December 9, 2025. Platinum members: Anthropic, Google, Microsoft, AWS, OpenAI, Block, Bloomberg, Cloudflare. AAIF-reported metrics (February 2026, *credible but primary source not directly retrieved in this research*): **10,000+ active MCP servers**, **97 million monthly SDK downloads**.

---

## 2. Architecture

### 2.1 MCP Architecture

MCP uses a **client-server hub-and-spoke topology** with three participants (MCP Spec, 2025-11-25):

- **Host:** The AI application (Claude Desktop, VS Code Copilot) — manages connections, coordinates multiple clients
- **Client:** Within the host; maintains a dedicated 1:1 connection to one MCP server
- **Server:** Exposes tools, resources, and prompts

**Protocol layers:**

| Layer | Detail |
|---|---|
| Data | JSON-RPC 2.0 |
| Transport (local) | **stdio** — for local processes; zero network overhead |
| Transport (remote) | **Streamable HTTP** — HTTP POST + optional SSE upgrade |

**Authorization:** OAuth 2.1 with PKCE; Resource Indicators (RFC 8707); Protected Resource Metadata (RFC 9728). Authorization is **OPTIONAL** — not enforced at protocol level.

**Initialization sequence:**
1. Client → `initialize` (protocolVersion + capabilities)
2. Server → capabilities response
3. Client → `notifications/initialized`
4. Operation phase; shutdown via transport close

**Server-exposed primitives:**

| Primitive | Controlled by | Description |
|---|---|---|
| **Tools** | Model | Executable functions — `tools/list`, `tools/call`; can declare `outputSchema` |
| **Resources** | Application | Data sources — `resources/list`, `resources/read`, `resources/subscribe` |
| **Prompts** | User | Reusable templates, slash commands — `prompts/list`, `prompts/get` |
| **Tasks** *(experimental)* | Protocol | Durable execution wrappers with TTL; state machine |

**Client-exposed primitives (servers invoke on the host):**

| Primitive | Description |
|---|---|
| **Sampling** | Server requests LLM completions from the host — model-agnostic, no API key required |
| **Elicitation** | Server requests additional user input |
| **Roots** | Server inquires about filesystem boundaries |

**MCP Tasks state machine (experimental, 2025-11-25):**
```
working → input_required → working  (loop)
working → completed
working → failed
working → cancelled
```

**Canonical message:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {"location": "New York"}
  }
}
```

> **Evidence quality: STRONG** — Architecture sourced directly from modelcontextprotocol.io/specification/2025-11-25.

---

### 2.2 A2A Architecture

A2A uses a **client-server model over HTTP** with three actors (A2A Spec v1.0.0, 2026):

- **User:** End user or automated service defining goals
- **A2A Client:** Application, service, or AI agent acting on behalf of the user
- **A2A Server:** AI agent exposing HTTP endpoints

> ⚠️ **"Peer-to-peer" nuance:** A2A documentation consistently uses "peer-to-peer." The actual implementation is **client-initiated HTTP request/response**. An agent can be both client and server in different contexts, creating bidirectional deployment topologies — but the protocol is not symmetric. The P2P label describes design philosophy (autonomous collaborative agents), not the communication primitive. NAT traversal or symmetric connection behavior should not be assumed.

**Transport options:**
1. Synchronous request/response + polling
2. **SSE** — streaming real-time incremental results
3. **Webhooks** — asynchronous push for disconnected scenarios
4. **gRPC and REST** (added v0.2.2, June 2025)

**Core primitives:**

| Primitive | Description |
|---|---|
| **Agent Card** | JSON metadata at `/.well-known/agent-card.json` (RFC 8615): identity, endpoint, capabilities, auth requirements, skills. Signed since v0.3.0. |
| **Task** | Stateful unit of work; persistent ID; can span hours to days |
| **Message** | Communication turn with role ("user" or "agent") |
| **Part** | Content container: text, binary, URL, structured JSON, audio, **video** |
| **Artifact** | Tangible deliverable produced during task execution; composed of Parts |
| **Context ID** | Groups related tasks across interactions — conversation-level scoping |

**A2A v1.0.0 notable changes (March 12, 2026):**
- OAuth 2.0 modernized: removed implicit flow + password grant; added device code flow + PKCE
- `tasks/list` with pagination
- Multi-tenancy via `scope` field on gRPC
- Protocol separated from transport mapping

> **Evidence quality: STRONG** for architecture (sourced from github.com/a2aproject/A2A). Note the repo moved from `google/A2A` → `a2aproject/A2A` post–Linux Foundation transfer.

---

## 3. Architectural Comparison

| Dimension | MCP (2025-11-25) | A2A (v1.0.0) |
|---|---|---|
| **Topology** | Hub-and-spoke (host → clients → servers) | Client-server; agents can be both |
| **Transport** | stdio (local) + Streamable HTTP (remote) | HTTP/SSE/webhooks/gRPC |
| **Local support** | ✅ stdio | ❌ HTTP-only |
| **Base protocol** | JSON-RPC 2.0 | JSON-RPC 2.0 |
| **Discovery** | Host must know URL in advance; Registry in preview | Agent Card at RFC 8615 well-known URI |
| **Auth** | OAuth 2.1 (optional) | OAuth 2.0 + PKCE + mTLS (declared in Agent Card) |
| **Long-running tasks** | Experimental (2025-11-25) | Core primitive from v0.1 |
| **Capability exposure** | Full — `tools/list`, `resources/list` expose everything | Partial — Agent Card exposes skills; internals hidden |
| **Agent opacity** | Servers are transparent | Agents are black boxes |
| **Multimodal** | Text, image, audio, resource_link | Text, binary, structured JSON, audio, **video** |
| **Multi-tenancy** | Not in spec | v1.0.0 — `scope` field on gRPC |

---

## 4. Problems Each Solves That the Other Does Not

### Problems MCP Solves That A2A Does Not

**1. Universal tool/resource interface for LLMs.**
Pre-MCP, every AI application required bespoke integrations per data source. MCP provides a universal protocol layer with typed tool definitions, input/output schemas, and structured returns that LLMs can reliably invoke. *(The "USB-C for AI" metaphor, used officially by Anthropic, overstates plug-and-play ease — USB-C guarantees physical interoperability; MCP still requires server-side implementation work.)*

**2. LLM Sampling without API keys.**
`sampling/createMessage` allows an MCP server to request completions from the connected host's LLM, remaining model-agnostic without importing any LLM SDK. A2A agents are assumed to manage their own LLMs — no equivalent mechanism exists.

**3. Prompt templating as a first-class primitive.**
MCP's `Prompts` primitive enables reusable interaction templates — slash commands, few-shot examples, system prompt patterns — surfaced as user-controlled UI options. No A2A equivalent exists.

**4. Structured tool output schema validation.**
Tools can declare `outputSchema` (JSON Schema), enabling strict validation of structured results. A2A has no per-skill output schema mechanism.

**5. Interactive UI embedding (MCP Apps extension).**
MCP Apps allow servers to return interactive HTML interfaces (data visualizations, forms, dashboards) that render inside host applications. No A2A equivalent.

**6. Local process integration via stdio.**
Zero network overhead for developer tooling (VS Code, Cursor, local scripts). A2A is HTTP-only.

**7. Real-time resource subscriptions.**
`resources/subscribe` + push notifications when content changes — enables real-time document/file/database monitoring. Not in A2A.

**8. Filesystem root exposure (Roots primitive).**
Servers can understand the operational scope of the host filesystem. No A2A equivalent.

---

### Problems A2A Solves That MCP Does Not

**1. Cross-vendor, cross-framework agent interoperability.**
A2A enables LangGraph, CrewAI, Semantic Kernel, and proprietary agents to collaborate without shared implementation, shared tool definitions, or shared framework dependencies. MCP has no agent-to-agent communication layer.

**2. Agent opacity for IP protection.**
A2A agents remain opaque about internal memory, tool lists, and reasoning chains. Nuance: *external interface* is still exposed via Agent Card (name, description, skills, auth). Opacity applies to *internal implementation* only. MCP servers expose everything via `tools/list`, `resources/list`.

**3. Autonomous agent capability discovery.**
Agent Cards at RFC 8615 URIs (`/.well-known/agent-card.json`) enable automated discovery without prior configuration. MCP Registry (in preview) partially addresses this at the ecosystem level but is not integrated into the core protocol.

**4. Long-running task management as a core primitive.**
Hours-to-days tasks with persistent IDs, polling, webhook callbacks, and structured artifact delivery have been core A2A primitives since v0.1 (April 2025). MCP added experimental Tasks in November 2025. *(See Section 5 for the functional overlap this creates.)*

**5. Disconnected/async operations via webhooks.**
A2A supports webhook-based push notifications — client initiates, disconnects, receives results later. MCP experimental Tasks require polling.

**6. Multi-tenancy.**
A2A v1.0.0 explicitly added multi-tenancy via gRPC `scope` field. MCP has no equivalent.

**7. Video and extended multimodal content.**
A2A `Part` supports video via `mediaType` negotiation. MCP supports text, image, audio, resource_link — not video.

**8. Conversation-level context threading (Context ID).**
A2A's `contextId` groups related tasks across multiple interactions — equivalent to a project or conversation thread. No direct MCP equivalent.

---

## 5. Where the Landscape Is More Complex

### 5.1 MCP Tasks vs. A2A Tasks: The Overlap Is Significant

The official "complementary" framing — authored by the A2A team in `a2a-and-mcp.md` — materially understates functional overlap. Both protocols now have:
- TTL-based stateful task primitives
- State machines with `working`, `completed`, `failed`, `cancelled`
- Polling-based or notification-based status tracking
- Cancellation support

The architectural distinction (MCP tasks wrap tool invocations; A2A tasks represent full agent collaborations) is real but does not eliminate a genuine design decision point. Third-party analyses (Towards AI, Medium technical writeups) explicitly label this the **"Protocol Wars" dynamic** — a framing the official documentation suppresses.

**Task state comparison:**

| State | MCP (experimental) | A2A (core) |
|---|---|---|
| Submitted | *(implicit via request)* | `submitted` |
| Working | `working` | `working` |
| Input needed | `input_required` | *(handled via message turns)* |
| Completed | `completed` | `completed` |
| Failed | `failed` | `failed` |
| Cancelled | `cancelled` | `cancelled` |

### 5.2 Genuine Decision Point: "Invoke a Specialized AI Service"

When an orchestrator needs to invoke a specialized ML service (e.g., document classification):

**MCP path:** Expose the service as an MCP tool with input/output schemas. Stateless, structured, the orchestrator retains LLM reasoning control.

**A2A path:** The service runs as an A2A agent. Orchestrator delegates a task; the service responds autonomously. Stateful, multi-turn capable, the service retains its own reasoning control.

This is a **genuine competitive decision point**. Protocol selection has downstream implications for opacity, schema enforcement, multi-turn capability, versioning, and vendor dependency.

### 5.3 Microsoft's Role Is Underrepresented in Most Analyses

Microsoft is a platinum AAIF member and its role is architecturally substantive:
- **Semantic Kernel** — native support for both MCP and A2A
- **Azure AI Foundry** — uses A2A for agent collaboration
- **Microsoft Agent Framework** (announced October 2025; merger of AutoGen + Semantic Kernel) — natively supports both protocols
- A2A **Technical Steering Committee** participant

Practical implication: any enterprise deploying on Azure has a direct path to both protocols within a single managed stack.

### 5.4 OpenAI's AGENTS.md and the Three-Way Dynamic

Most analyses frame this as a two-protocol landscape. The fuller picture includes OpenAI's **AGENTS.md** specification (launched August 2025, **60,000+ adopters** per critic assessment — *evidence quality: MODERATE, primary source not retrieved*). OpenAI is an AAIF co-founder alongside Anthropic and Google.

| Actor | Protocol Origin | AAIF Role |
|---|---|---|
| Anthropic | MCP | Platinum member |
| Google | A2A | Platinum member |
| OpenAI | AGENTS.md | Co-founder |
| Microsoft | — | Platinum member, TSC participant |

The AAIF governance roof creates incentives for protocol convergence or interoperability. Whether this achieves harmonization across MCP, A2A, and AGENTS.md — or produces governance fragmentation within the shared umbrella — is an open empirical question as of April 2026.

### 5.5 IBM ACP Merger Affects A2A's Design Scope

IBM's Agent Communication Protocol (ACP, March 2025) was an independent protocol with REST-first design philosophy — simpler and more developer-accessible than A2A's original architecture. Its merger into A2A (August–September 2025) means A2A v1.0.0 incorporates both Google's enterprise-oriented architecture (Agent Cards, SSE, complex auth) and IBM's accessibility-focused design. The "A2A is Google's protocol" description is accurate for April 2025 origin only.

---

## 6. Complementary or Competing?

The canonical combined architecture — endorsed by both protocols' official documentation — is well-established:

```
┌─────────────────────────────────────────────────┐
│  Multi-Agent Workflow (A2A coordination layer)  │
│   Orchestrator Agent ←──A2A──→ Specialist Agent │
└──────────────┬──────────────────────┬───────────┘
               │ MCP                  │ MCP
    ┌──────────▼──────┐    ┌──────────▼──────┐
    │  Tool Server 1  │    │  Tool Server 2  │
    │  (DB, Files,    │    │  (APIs, Search, │
    │   Git, etc.)    │    │   Compute, etc.)│
    └─────────────────┘    └─────────────────┘
```

**Known combined implementations:**
- **Cisco agntcy** — leverages both protocols for discovery and observability (per A2A documentation)
- **LangChain** — A2A launch partner and major MCP consumer for tool-equipped agents
- **Microsoft Agent Framework (AutoGen + Semantic Kernel)** — native support for both in a single orchestration framework
- **Google Vertex AI Agent Builder** — A2A for agent coordination, MCP for tool access in GCP deployments

**The complementary framing holds** for clean layer separation: MCP for tool invocation, A2A for agent coordination. These are not in conflict when used at their intended layers.

**Genuine competition exists** in three cases: (1) wrapping a specialized AI service as MCP tool vs. A2A agent, (2) async AI service invocation where MCP Tasks and A2A Tasks now overlap functionally, (3) selecting a protocol for a new long-running AI workflow where both are technically capable.

---

## 7. Adoption

### MCP (as of early 2026)
- **10,000+ active servers; 97M monthly SDK downloads** (AAIF-reported, February 2026 — *MODERATE: credible but primary source not directly retrieved*)
- **Supported clients (confirmed):** Claude, ChatGPT, VS Code Copilot, Cursor, Zed, Replit, Codeium, Sourcegraph, Goose, Postman, MCPJam
- **SDKs:** TypeScript (official), Python (official), community SDKs
- **Registry:** In preview; backed by Anthropic, GitHub, PulseMCP, Microsoft

### A2A (as of early 2026)
- **50+ named launch partners** (April 9, 2025 — *STRONG*); **100+ supporting organizations** (June 23, 2025 — *MODERATE*)
- **Named partners:** Atlassian, Box, Cohere, LangChain, MongoDB, PayPal, Salesforce, SAP, ServiceNow, Workday; services firms: Accenture, BCG, Capgemini, Cognizant, Deloitte, HCLTech, Infosys, KPMG, McKinsey, PwC, TCS, Wipro
- **GitHub** (snapshot, order-of-magnitude only): ~23k stars, 2.3k forks — repo URL has moved to `a2aproject/A2A`
- **SDKs:** Python, Go, JavaScript, Java, .NET
- ⚠️ **No Technology Compatibility Kit (TCK)** exists for v1.0.0 — "A2A compliant" is not formally verifiable

---

## 8. Gaps and Limitations

1. **No MCP spec post 2025-11-25 confirmed.** MCP Tasks (experimental in that spec) may have graduated to stable by April 2026. Verify at modelcontextprotocol.io.

2. **No A2A TCK.** Without a Technology Compatibility Kit, "A2A compliant" claims are unverifiable. Procurement/audit decisions requiring formal compliance should note this gap.

3. **Agent Card trust model underspecified.** A2A v0.3.0 added card signatures; the trust model for autonomous agent discovery via well-known URIs is not fully elaborated in retrieved documentation.

4. **AAIF metrics unverified at primary source.** The 10,000+/97M figures are credible but should not be used as precise citations without direct AAIF documentation.

5. **UCP and other protocols not covered.** Universal Commerce Protocol (UCP) and other candidates are identified in comparative analyses but not investigated here.

6. **Streamable HTTP changelog ambiguity.** May have been introduced in 2025-03-26 spec rather than 2025-11-25. Verify before relying on transport history for compliance or migration.

---

## References

**Primary Spec Documentation:**

- Anthropic / AAIF. (2025). *Model Context Protocol Specification, v2025-11-25*. https://modelcontextprotocol.io/specification/2025-11-25/ *(Architecture, lifecycle, transports, authorization, tools, resources, tasks, sampling, sampling)*

- A2A Project / Linux Foundation / AAIF. (2026). *A2A Protocol v1.0.0*. https://github.com/a2aproject/A2A *(Key concepts, a2a-and-mcp.md, agent-discovery.md, CHANGELOG, roadmap)*

**Announcements:**

- Anthropic. (2024, November 25). *Introducing the Model Context Protocol*. https://www.anthropic.com/news/model-context-protocol

- Google Developers. (2025, April 9). *A2A: A New Era of Agent Interoperability*. https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/

**Standards Referenced:**
- IETF RFC 8615 — Well-Known Uniform Resource Identifiers *(A2A Agent Card discovery)*
- IETF RFC 8707 — Resource Indicators for OAuth 2.0 *(MCP authorization)*
- IETF RFC 9728 — OAuth 2.0 Protected Resource Metadata *(MCP authorization)*
- JSON-RPC 2.0 specification *(base protocol layer for both)*

> *Third-party community site a2aprotocol.ai — **evidence quality: MODERATE** — useful for analogies but not authoritative for spec claims.*

---

**Three files saved:**
- `/tmp/searcher_output.md` — raw findings from 72 tool calls across MCP spec, A2A spec, announcements, and third-party analyses
- `/tmp/critic_output.md` — evidence quality ratings, conflict analysis, gap identification (including AAIF timeline correction and ACP merger gap)
- `/tmp/final_report.md` — the full report above
