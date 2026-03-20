# 🦞 OpenClaw — Complete Architecture & Codebase Documentation

> **Purpose:** This document is a ground-up, systematic walkthrough of the OpenClaw codebase. It is written for a new developer joining the team who needs to understand everything — from folder structure to how messages flow from WhatsApp to an AI agent and back.

---

## Table of Contents

1. [What is OpenClaw?](#1-what-is-openclaw)
2. [High-Level Architecture Overview](#2-high-level-architecture-overview)
3. [Tech Stack & Tooling](#3-tech-stack--tooling)
4. [Monorepo Structure (pnpm Workspaces)](#4-monorepo-structure-pnpm-workspaces)
5. [Folder Structure — Full Breakdown](#5-folder-structure--full-breakdown)
6. [The Gateway (Control Plane)](#6-the-gateway-control-plane)
7. [The Agent Runtime (Pi Embedded)](#7-the-agent-runtime-pi-embedded)
8. [Channels — Multi-Platform Messaging](#8-channels--multi-platform-messaging)
9. [Routing & Session Management](#9-routing--session-management)
10. [Configuration System](#10-configuration-system)
11. [CLI — Command Line Interface](#11-cli--command-line-interface)
12. [UI — Control Panel & WebChat](#12-ui--control-panel--webchat)
13. [Browser Control](#13-browser-control)
14. [Skills & Plugins (Extension System)](#14-skills--plugins-extension-system)
15. [Companion Apps (macOS, iOS, Android)](#15-companion-apps-macos-ios-android)
16. [Deployment & Docker](#16-deployment--docker)
17. [Testing Strategy](#17-testing-strategy)
18. [Security Model](#18-security-model)
19. [Complete Feature List](#19-complete-feature-list)
20. [How OpenClaw Differs From Other AI Assistants](#20-how-openclaw-differs-from-other-ai-assistants)
21. [End-to-End Message Flow (Putting It All Together)](#21-end-to-end-message-flow-putting-it-all-together)

---

## 1. What is OpenClaw?

OpenClaw is a **personal AI assistant** that you self-host on your own devices. Unlike ChatGPT or Gemini where you go to a website, OpenClaw brings the AI to the messaging apps you already use — WhatsApp, Telegram, Slack, Discord, Signal, iMessage, Microsoft Teams, Google Chat, and more.

**In simple terms:** You run a server (the "Gateway") on your computer or a cloud VM. You connect it to your messaging apps. Now you can text your AI assistant on WhatsApp just like texting a friend, and it responds using models from Anthropic (Claude) or OpenAI (GPT).

**Key characteristics:**
- **Single-user, personal assistant** — built for one person, not a team/SaaS product
- **Local-first** — runs on your hardware, your data stays with you
- **Multi-channel** — one assistant, many messaging surfaces
- **Always-on** — runs as a daemon/background service
- **Extensible** — skills, plugins, browser control, voice, canvas

---

## 2. High-Level Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     MESSAGING CHANNELS                           │
│  WhatsApp │ Telegram │ Slack │ Discord │ Signal │ iMessage │ ... │
└─────────────────────────┬────────────────────────────────────────┘
                          │ Inbound messages
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                     GATEWAY (Control Plane)                      │
│                   ws://127.0.0.1:18789                           │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ WebSocket   │  │ HTTP Server  │  │ Channel Connectors      │ │
│  │ Server      │  │ (Hono/       │  │ (Baileys, grammY,       │ │
│  │ (ws)        │  │  Express)    │  │  Bolt, discord.js, ...) │ │
│  └──────┬──────┘  └──────┬───────┘  └────────────┬────────────┘ │
│         │               │                        │               │
│  ┌──────┴───────────────┴────────────────────────┴──────────┐   │
│  │              Gateway Core (server.impl.ts)                │   │
│  │  Sessions │ Routing │ Cron │ Hooks │ Config │ Plugins     │   │
│  └──────────────────────────┬────────────────────────────────┘   │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   PI AGENT RUNTIME (Embedded)                    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ System       │  │ Model Auth   │  │ Tool Execution       │   │
│  │ Prompt       │  │ & Failover   │  │ (bash, browser,      │   │
│  │ Builder      │  │ (profiles)   │  │  skills, nodes, ...) │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  Powered by: @mariozechner/pi-agent-core + pi-ai                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     LLM PROVIDERS (External APIs)                │
│         Anthropic (Claude) │ OpenAI (GPT) │ Google │ Ollama     │
│         Bedrock │ GitHub Copilot │ Venice │ Custom providers     │
└──────────────────────────────────────────────────────────────────┘
```

**Architecture style:** This is a **modular monolith** — all code lives in one repository, builds into one binary (`dist/index.js`), and runs as a single process. However, it is organized like microservices internally with clear module boundaries. The extensions system (`extensions/*`) and skills (`skills/*`) act as plugins loaded at runtime.

---

## 3. Tech Stack & Tooling

### Core Language & Runtime
| Component | Technology |
|-----------|-----------|
| Language | **TypeScript** (strict mode, ESM modules) |
| Runtime | **Node.js ≥ 22** (also supports Bun for dev) |
| Target | ES2023 |
| Module system | ESM (`"type": "module"` in package.json) |

### Build & Dev Tools
| Tool | Purpose |
|------|---------|
| **pnpm** | Package manager (monorepo workspaces) |
| **tsdown** (+ rolldown) | TypeScript bundler (builds `dist/`) |
| **tsx** | TypeScript execution for dev (runs `.ts` directly) |
| **Vitest** | Test framework (unit, e2e, live tests) |
| **oxlint** | Linter (Rust-based, fast) |
| **oxfmt** | Formatter (Rust-based, fast) |
| **Vite** | UI build tool (for the Control UI) |

### Key Dependencies (3rd Party Libraries)
| Library | Purpose |
|---------|---------|
| **ws** | WebSocket server (Gateway control plane) |
| **hono** | HTTP framework (lightweight, used for HTTP endpoints) |
| **express** | HTTP framework (used alongside Hono for some routes) |
| **commander** | CLI framework (all `openclaw` commands) |
| **@whiskeysockets/baileys** | WhatsApp Web API (unofficial, reverse-engineered) |
| **grammy** | Telegram Bot API framework |
| **@slack/bolt** | Slack Bot framework |
| **discord.js** (via @buape/carbon) | Discord Bot framework |
| **playwright-core** | Browser automation (CDP/Chrome control) |
| **@mariozechner/pi-agent-core** | Pi agent runtime (the AI agent loop) |
| **@mariozechner/pi-ai** | Pi AI model adapters |
| **@sinclair/typebox** | JSON Schema / TypeBox for type-safe schemas |
| **zod** | Schema validation (config validation) |
| **sharp** | Image processing (media pipeline) |
| **chokidar** | File watcher (hot-reload config) |
| **croner** | Cron job scheduler |
| **lit** | Web Components framework (UI) |
| **chalk** | Terminal colors |
| **tslog** | Structured logging |
| **@clack/prompts** | Interactive CLI prompts (onboarding wizard) |
| **sqlite-vec** | SQLite vector search (memory/embeddings) |
| **pdfjs-dist** | PDF parsing |
| **linkedom** | Server-side DOM (link understanding) |
| **markdown-it** | Markdown rendering |
| **node-edge-tts** | Text-to-speech |
| **yaml / json5** | Config file parsing |

### Native / Platform Dependencies
| Library | Purpose |
|---------|---------|
| **@lydell/node-pty** | Pseudo-terminal (bash tool execution) |
| **@homebridge/ciao** | mDNS/Bonjour discovery (device pairing) |
| **@napi-rs/canvas** | Canvas rendering (optional peer dep) |
| **node-llama-cpp** | Local LLM support (optional peer dep) |

---

## 4. Monorepo Structure (pnpm Workspaces)

OpenClaw uses **pnpm workspaces** to manage a monorepo. The workspace definition lives in `pnpm-workspace.yaml`:

```yaml
packages:
  - .           # Root package (the main openclaw CLI + Gateway)
  - ui          # Control UI (Vite + Lit web components)
  - packages/*  # Internal shared packages
  - extensions/* # Channel/feature plugins
```

**What this means:** There are multiple `package.json` files in the repo. Each workspace package can have its own dependencies. pnpm links them together so they can import from each other.

### Workspace Packages

| Workspace | Path | Purpose |
|-----------|------|---------|
| **openclaw** (root) | `.` | Main CLI, Gateway, agent, channels — the core product |
| **openclaw-control-ui** | `ui/` | Web-based Control UI and WebChat |
| **clawdbot / moltbot** | `packages/*` | Internal shared packages |
| **31 extensions** | `extensions/*` | Channel plugins (Teams, Matrix, Zalo, etc.) |

---

## 5. Folder Structure — Full Breakdown

### Root-Level Files

```
openclaw/
├── package.json              # Main package config, scripts, dependencies
├── pnpm-workspace.yaml       # Monorepo workspace definition
├── pnpm-lock.yaml            # Dependency lock file (~369KB, lots of deps)
├── tsconfig.json             # TypeScript compiler config
├── tsdown.config.ts          # Build bundler config (TypeScript → dist/)
├── vitest.config.ts          # Main test config
├── vitest.e2e.config.ts      # End-to-end test config
├── vitest.live.config.ts     # Live test config (real API keys)
├── vitest.unit.config.ts     # Unit test config
├── vitest.extensions.config.ts # Extension test config
├── vitest.gateway.config.ts  # Gateway-specific test config
├── Dockerfile                # Production Docker image
├── Dockerfile.sandbox        # Sandbox container (for tool execution)
├── Dockerfile.sandbox-browser # Sandbox with browser support
├── docker-compose.yml        # Docker Compose for gateway + CLI
├── fly.toml                  # Fly.io deployment config
├── fly.private.toml          # Private Fly.io config
├── render.yaml               # Render.com deployment config
├── openclaw.mjs              # CLI entry point (bin script)
├── AGENTS.md                 # Repository guidelines for AI agents
├── CLAUDE.md                 # Claude-specific instructions
├── README.md                 # Project README
├── CONTRIBUTING.md           # Contribution guidelines
├── SECURITY.md               # Security policy
├── CHANGELOG.md              # Release changelog (~143KB, very active)
├── LICENSE                   # MIT License
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore rules
├── .npmrc                    # npm/pnpm config
├── .oxlintrc.json            # Linter config
├── .oxfmtrc.jsonc            # Formatter config
└── .pre-commit-config.yaml   # Pre-commit hooks
```

### Root-Level Directories

```
openclaw/
├── src/                # 🟢 CORE SOURCE CODE (TypeScript)
├── ui/                 # 🟡 CONTROL UI (Vite + Lit web app)
├── apps/               # 🔵 NATIVE APPS (macOS, iOS, Android)
├── extensions/         # 🟣 CHANNEL PLUGINS (31 extensions)
├── skills/             # 🟠 TOOL SKILLS (53 bundled skills)
├── packages/           # ⚪ INTERNAL SHARED PACKAGES
├── docs/               # 📄 DOCUMENTATION (Mintlify-powered)
├── scripts/            # 🔧 BUILD/DEV/RELEASE SCRIPTS
├── test/               # 🧪 ADDITIONAL TEST HELPERS
├── patches/            # 🩹 PNPM PATCHES (for dependencies)
├── vendor/             # 📦 VENDORED DEPENDENCIES
├── assets/             # 🖼  IMAGES, ICONS
├── git-hooks/          # 🪝 GIT HOOKS
├── Swabble/            # INTERNAL TOOLING
├── .github/            # GITHUB ACTIONS, LABELER CONFIG
├── .vscode/            # VSCODE SETTINGS
├── .pi/                # PI AGENT CONFIG
└── .agents/ .agent/    # AGENT WORKFLOW FILES
```

### `src/` — The Heart of the Codebase (50+ subdirectories)

This is where all the business logic lives. Here is every subdirectory explained:

```
src/
├── index.ts                 # Main entry: loads env, builds CLI, runs
├── entry.ts                 # Process bootstrap: respawns with correct Node flags
│
├── gateway/                 # 🏗  THE GATEWAY (control plane) - 128+ files
│   ├── server.impl.ts       #    Main Gateway server (starts WS + HTTP)
│   ├── server-http.ts       #    HTTP endpoints (health, webhooks, etc.)
│   ├── server-chat.ts       #    Chat handling (message → agent → reply)
│   ├── server-channels.ts   #    Channel lifecycle management
│   ├── server-cron.ts       #    Cron job scheduling
│   ├── server-methods.ts    #    WebSocket RPC method dispatch
│   ├── server-methods/      #    Individual WS method handlers
│   ├── server/              #    Server subsystems
│   ├── protocol/            #    WS protocol schema definitions
│   ├── session-utils.ts     #    Session resolution & management
│   ├── hooks.ts             #    Hooks system (before/after events)
│   ├── auth.ts              #    Gateway authentication
│   ├── client.ts            #    WS client library (for CLI/apps to connect)
│   ├── openai-http.ts       #    OpenAI-compatible HTTP API
│   ├── openresponses-http.ts #   OpenAI Responses API compatibility
│   ├── ws-log.ts            #    WebSocket logging/debugging
│   └── ...                  #    Many more: nodes, plugins, tailscale, etc.
│
├── agents/                  # 🤖 AGENT RUNTIME - 297+ files (largest module!)
│   ├── pi-embedded-runner.ts #   Core: runs the Pi agent in-process
│   ├── pi-embedded-subscribe.ts # Subscribes to agent events (streaming)
│   ├── pi-embedded-helpers.ts #  Helper utilities for the agent
│   ├── pi-embedded-utils.ts  #   More utilities
│   ├── system-prompt.ts      #   Builds the system prompt for the LLM
│   ├── pi-tools.ts           #   Tool definitions (what the agent can do)
│   ├── bash-tools.exec.ts    #   Bash/shell execution tool (~54KB, complex!)
│   ├── bash-tools.process.ts #   Process management tool
│   ├── model-selection.ts    #   Which AI model to use
│   ├── model-auth.ts         #   API key / OAuth authentication
│   ├── model-fallback.ts     #   Automatic model failover
│   ├── auth-profiles/        #   Auth profile management (rotate keys)
│   ├── skills/               #   Skills loading & prompt injection
│   ├── sandbox/              #   Docker sandbox for tool execution
│   ├── compaction.ts         #   Context window compaction (summarize history)
│   ├── workspace.ts          #   Agent workspace management
│   ├── identity.ts           #   Agent identity/persona
│   ├── cli-runner.ts         #   Run agent from CLI (non-Gateway mode)
│   ├── cli-runner/           #   CLI runner subsystems
│   ├── pi-extensions/        #   Extension hooks for Pi agent
│   ├── schema/               #   Agent config schemas
│   ├── tools/                #   Additional tool implementations
│   └── test-helpers/         #   Test utilities
│
├── config/                  # ⚙️  CONFIGURATION - 123+ files
│   ├── schema.ts            #    Main config schema (~55KB, TypeBox)
│   ├── zod-schema.ts        #    Zod-based validation schema (~20KB)
│   ├── zod-schema.*.ts      #    Per-domain Zod schemas
│   ├── io.ts                #    Config file read/write (~19KB)
│   ├── defaults.ts          #    Default configuration values
│   ├── paths.ts             #    File path resolution
│   ├── types.*.ts           #    TypeScript types for each config domain
│   ├── validation.ts        #    Config validation logic
│   ├── legacy.*.ts          #    Legacy config migration (3 parts)
│   ├── sessions.ts          #    Session store config
│   ├── includes.ts          #    Config file includes/merging
│   └── group-policy.ts      #    Group message policy resolution
│
├── cli/                     # 💻 CLI COMMANDS - 98+ files
│   ├── program.ts           #    CLI program builder (Commander.js)
│   ├── run-main.ts          #    Main CLI entry point
│   ├── gateway-cli.ts       #    `openclaw gateway` command
│   ├── channels-cli.ts      #    `openclaw channels` command
│   ├── config-cli.ts        #    `openclaw config` command
│   ├── models-cli.ts        #    `openclaw models` command
│   ├── browser-cli*.ts      #    `openclaw browser` commands
│   ├── skills-cli.ts        #    `openclaw skills` command
│   ├── plugins-cli.ts       #    `openclaw plugins` command
│   ├── memory-cli.ts        #    `openclaw memory` command
│   ├── update-cli.ts        #    `openclaw update` command (~44KB!)
│   ├── pairing-cli.ts       #    `openclaw pairing` command
│   ├── nodes-*.ts           #    `openclaw nodes` commands
│   ├── completion-cli.ts    #    Shell auto-completion
│   └── ...                  #    Many more CLI commands
│
├── channels/                # 📡 CHANNEL FRAMEWORK - 28+ files
│   ├── dock.ts              #    Channel lifecycle manager (~15KB)
│   ├── registry.ts          #    Channel registry (register/discover)
│   ├── channel-config.ts    #    Channel configuration resolver
│   ├── allowlists/          #    Per-channel allowlists
│   ├── plugins/             #    Channel plugin system
│   ├── web/                 #    Web channel implementation
│   ├── mention-gating.ts    #    Group mention activation rules
│   ├── command-gating.ts    #    Command permission rules
│   └── typing.ts            #    Typing indicator support
│
├── routing/                 # 🔀 MESSAGE ROUTING - 5 files
│   ├── resolve-route.ts     #    Route inbound message → session/agent
│   ├── session-key.ts       #    Session key derivation
│   └── bindings.ts          #    Channel → agent bindings
│
├── whatsapp/                # 📱 WHATSAPP CHANNEL
├── telegram/                # ✈️  TELEGRAM CHANNEL
├── discord/                 # 🎮 DISCORD CHANNEL
├── slack/                   # 💬 SLACK CHANNEL
├── signal/                  # 🔒 SIGNAL CHANNEL
├── imessage/                # 🍎 IMESSAGE CHANNEL (legacy)
├── line/                    # LINE CHANNEL
│
├── browser/                 # 🌐 BROWSER CONTROL - 67+ files
│   ├── pw-session.ts        #    Playwright session management
│   ├── cdp.ts               #    Chrome DevTools Protocol
│   ├── chrome.ts            #    Chrome/Chromium management
│   ├── server-context.ts    #    Browser server context
│   ├── extension-relay.ts   #    Browser extension relay
│   └── pw-tools-core.*.ts   #    Tool implementations (click, type, etc.)
│
├── sessions/                # 📋 SESSION MODEL
├── providers/               # 🔑 LLM PROVIDER AUTH (Copilot, Google, etc.)
├── memory/                  # 🧠 MEMORY / EMBEDDINGS (sqlite-vec)
├── media/                   # 🖼  MEDIA PIPELINE (images, audio, video)
├── media-understanding/     # 🔍 MEDIA ANALYSIS
├── link-understanding/      # 🔗 LINK/URL CONTENT EXTRACTION
├── markdown/                # 📝 MARKDOWN PROCESSING
├── cron/                    # ⏰ CRON JOBS
├── hooks/                   # 🪝 EVENT HOOKS
├── pairing/                 # 🤝 DEVICE PAIRING
├── security/                # 🔐 SECURITY (DM policies, sandboxing)
├── web/                     # 🌍 WEB SERVER (Control UI + WebChat host)
├── canvas-host/             # 🎨 CANVAS (A2UI visual workspace)
├── node-host/               # 📡 NODE HOST (device node management)
├── acp/                     # 🔌 AGENT CLIENT PROTOCOL (IDE integration)
├── tui/                     # 🖥  TERMINAL UI
├── tts/                     # 🔊 TEXT-TO-SPEECH
├── wizard/                  # 🧙 ONBOARDING WIZARD
├── commands/                # 📋 CHAT COMMANDS (/status, /reset, etc.)
├── auto-reply/              # 🤖 AUTO-REPLY TEMPLATES
├── plugin-sdk/              # 🧩 PLUGIN SDK (for extension authors)
├── plugins/                 # 🧩 PLUGIN LOADER
├── infra/                   # 🏗  INFRASTRUCTURE (env, ports, runtime)
├── process/                 # ⚙️  PROCESS MANAGEMENT
├── logging/                 # 📊 STRUCTURED LOGGING
├── shared/                  # 🤝 SHARED UTILITIES
├── types/                   # 📘 SHARED TYPESCRIPT TYPES
├── utils/                   # 🔧 UTILITY FUNCTIONS
├── compat/                  # 🔄 COMPATIBILITY SHIMS
├── terminal/                # 🖥  TERMINAL UTILITIES (tables, colors)
├── scripts/                 # 📜 INTERNAL SCRIPTS
├── docs/                    # 📄 EMBEDDED DOCS
├── test-helpers/            # 🧪 TEST HELPERS
└── test-utils/              # 🧪 TEST UTILITIES
```

---

## 6. The Gateway (Control Plane)

The Gateway is the **single most important component** in OpenClaw. It's the central hub that everything connects to.

### What is it?

The Gateway is a **WebSocket + HTTP server** that runs on your machine (default port `18789`). It acts as a "control plane" — meaning it coordinates everything but doesn't do the actual AI work itself. Think of it as an air traffic controller.

### What does it manage?

1. **Channel connections** — Maintains live connections to WhatsApp, Telegram, Slack, etc.
2. **Sessions** — Tracks conversation state for each chat/user/group
3. **Agent invocations** — When a message arrives, it triggers the AI agent
4. **Client connections** — macOS app, iOS/Android nodes, WebChat, CLI all connect via WebSocket
5. **Cron jobs** — Scheduled tasks (wake-ups, automations)
6. **Hooks** — Event hooks (before/after message, webhooks)
7. **Config** — Hot-reloads configuration changes
8. **Plugins** — Loads and manages extension plugins

### How does it work technically?

**Entry point:** `src/gateway/server.impl.ts` → `startGatewayServer()`

1. **HTTP server** starts (Hono framework) — serves the Control UI, health endpoints, webhook receivers, and the OpenAI-compatible API
2. **WebSocket server** starts (ws library) — listens for client connections
3. **Channel connectors** start — each channel (WhatsApp, Telegram, etc.) establishes its own connection to the respective service
4. **RPC method dispatch** — clients send JSON-RPC messages over WebSocket, the gateway routes them to handler functions

### Key WebSocket Methods (Protocol)

The protocol is defined in `src/gateway/protocol/`. Key methods include:

| Method | Direction | Purpose |
|--------|-----------|---------|
| `chat.send` | Client → Gateway | Send a message to the agent |
| `chat.abort` | Client → Gateway | Cancel current agent run |
| `sessions.list` | Client → Gateway | List active sessions |
| `sessions.patch` | Client → Gateway | Update session settings |
| `config.get` / `config.set` | Client → Gateway | Read/write configuration |
| `channels.status` | Client → Gateway | Get channel health status |
| `node.list` / `node.invoke` | Client → Gateway | Device node management |
| `chat.stream.*` | Gateway → Client | Stream agent responses back |

---

## 7. The Agent Runtime (Pi Embedded)

### What is "Pi"?

Pi is the **AI agent framework** that OpenClaw uses. It's an external library built by Mario Zechner (`@mariozechner/pi-agent-core`, `pi-ai`, `pi-coding-agent`). OpenClaw embeds Pi directly into its process — hence "Pi Embedded."

**Important:** OpenClaw does **NOT** use LangChain, LangGraph, CrewAI, or AutoGen. It uses the Pi framework, which is a custom, purpose-built agent runtime.

### How does the agent loop work?

The core agent loop lives in `src/agents/pi-embedded-runner.ts`:

```
1. User message arrives (from any channel)
2. Gateway resolves which session this belongs to
3. Gateway calls the Pi embedded runner
4. The runner:
   a. Builds the system prompt (src/agents/system-prompt.ts)
   b. Loads conversation history (session transcript)
   c. Resolves which AI model to use (model-selection.ts)
   d. Authenticates with the model provider (model-auth.ts, auth-profiles/)
   e. Sends the prompt + history to the LLM API
   f. Streams the response back
   g. If the LLM wants to use a tool → executes the tool → feeds result back → repeats
   h. Final text response is sent back to the channel
```

### Tools Available to the Agent

Tools are defined in `src/agents/pi-tools.ts`. The major ones:

| Tool | File | Purpose |
|------|------|---------|
| **bash** | `bash-tools.exec.ts` | Execute shell commands |
| **process** | `bash-tools.process.ts` | Manage running processes |
| **read** | `pi-tools.read.ts` | Read files |
| **write/edit** | (via pi-coding-agent) | Write/edit files |
| **browser** | `src/browser/` | Control a Chrome browser |
| **canvas** | `src/canvas-host/` | Push UI to a visual canvas |
| **cron** | `src/cron/` | Schedule tasks |
| **nodes** | `src/node-host/` | Invoke device actions (camera, screen, etc.) |
| **sessions_**** | `openclaw-tools.ts` | Cross-session communication |
| **discord/slack** | `channel-tools.ts` | Channel-specific actions |
| **memory_search** | `memory-search.ts` | Search agent memory |
| **skills** | `skills.ts` | Dynamic skill loading |

### Model Support & Failover

`src/agents/model-selection.ts` and `model-fallback.ts` handle:

- **Multi-provider support:** Anthropic, OpenAI, Google, Ollama, Bedrock, GitHub Copilot, Venice, and more
- **Auth profile rotation:** Multiple API keys/OAuth tokens, rotated on failure
- **Automatic failover:** If one model/provider fails, automatically try the next
- **Model aliases:** Shorthand names for model IDs

---

## 8. Channels — Multi-Platform Messaging

### Built-in Channels (in `src/`)

| Channel | Library Used | Source Path |
|---------|-------------|-------------|
| **WhatsApp** | `@whiskeysockets/baileys` (Web API) | `src/whatsapp/` |
| **Telegram** | `grammy` (Bot API) | `src/telegram/` |
| **Discord** | `@buape/carbon` (discord.js wrapper) | `src/discord/` |
| **Slack** | `@slack/bolt` (Bolt framework) | `src/slack/` |
| **Signal** | `signal-cli` (external binary) | `src/signal/` |
| **iMessage** (legacy) | `imsg` (macOS only) | `src/imessage/` |
| **WebChat** | Built-in (Gateway HTTP) | `src/web/` |

### Extension Channels (in `extensions/`)

| Channel | Extension Path |
|---------|---------------|
| **Microsoft Teams** | `extensions/msteams/` |
| **Google Chat** | `extensions/googlechat/` |
| **BlueBubbles** (iMessage recommended) | `extensions/bluebubbles/` |
| **Matrix** | `extensions/matrix/` |
| **Zalo** | `extensions/zalo/` |
| **Zalo Personal** | `extensions/zalouser/` |
| **Twitch** | `extensions/twitch/` |
| **Mattermost** | `extensions/mattermost/` |
| **LINE** | `extensions/line/` |
| **Feishu (Lark)** | `extensions/feishu/` |
| **Nostr** | `extensions/nostr/` |
| **Nextcloud Talk** | `extensions/nextcloud-talk/` |
| **Tlon** | `extensions/tlon/` |
| **Voice Call** | `extensions/voice-call/` |

### How Channels Connect

The channel lifecycle is managed by `src/channels/dock.ts`:

1. On Gateway startup, `dock.ts` reads the config to see which channels are enabled
2. For each enabled channel, it instantiates the channel connector
3. The connector authenticates with the service (e.g., WhatsApp QR code scan, Telegram bot token)
4. Inbound messages are received and passed to the routing layer
5. Outbound messages (agent replies) are sent back through the channel connector

---

## 9. Routing & Session Management

### Routing (`src/routing/`)

When a message arrives, the routing system determines:
- **Which agent** should handle it (multi-agent support)
- **Which session** the message belongs to
- **What permissions** apply (allowlists, pairing, activation mode)

The key file is `src/routing/resolve-route.ts` which evaluates:
1. Channel type + sender identity
2. Config-defined routing rules (channel → agent mappings)
3. Group vs DM rules
4. Allowlist/pairing checks

### Sessions (`src/sessions/` + `src/gateway/session-utils.ts`)

A **session** represents one ongoing conversation. Sessions are identified by a **session key** like:
- `main` — your direct personal chat
- `group:<group-id>` — a group conversation
- `agent:<agent-id>:main` — a specific agent's session
- `acp:<uuid>` — an IDE session

Each session tracks:
- Conversation transcript (stored as `.jsonl` files)
- Model settings (which LLM, thinking level, verbose mode)
- Send policy (which channels to reply on)
- Activation mode (groups: always respond vs mention-only)

---

## 10. Configuration System

### Config File Location
`~/.openclaw/openclaw.json` (JSON5 format, supports comments)

### Config Schema
The schema is massive — defined in `src/config/schema.ts` (~55KB, TypeBox) and `src/config/zod-schema.ts` (~20KB, Zod). It covers every possible setting.

### Key Config Sections

```json5
{
  agent: {
    model: "anthropic/claude-opus-4-6",  // Default AI model
    thinking: "medium",                    // Thinking level
  },
  agents: {
    defaults: {
      workspace: "~/.openclaw/workspace",
      sandbox: { mode: "off" },
    },
    // Multi-agent definitions
    agents: {
      "research": { model: "openai/gpt-5.2", workspace: "./research" },
    }
  },
  channels: {
    whatsapp: { allowFrom: ["+1234567890"] },
    telegram: { botToken: "123:ABC" },
    discord: { token: "xyz" },
    slack: { botToken: "xoxb-...", appToken: "xapp-..." },
  },
  gateway: {
    port: 18789,
    bind: "loopback",
    auth: { mode: "token", token: "secret" },
    tailscale: { mode: "off" },
  },
  browser: { enabled: true },
  cron: { jobs: [] },
  hooks: { /* event hooks */ },
}
```

### Config Features
- **Hot reload:** Config changes are picked up without restarting
- **Environment variable substitution:** `${ENV_VAR}` in config values
- **Config includes:** Merge multiple config files
- **Legacy migration:** Automatic migration of old config formats (3 migration phases!)
- **Validation:** Zod-based validation with helpful error messages

---

## 11. CLI — Command Line Interface

The CLI is built with **Commander.js** and lives in `src/cli/`. Entry point flow:

```
openclaw.mjs → src/entry.ts → src/cli/run-main.ts → src/cli/program.ts → command handlers
```

### Key Commands

| Command | Purpose |
|---------|---------|
| `openclaw gateway` | Start the Gateway server |
| `openclaw onboard` | Run the setup wizard |
| `openclaw agent` | Send a message to the agent directly |
| `openclaw message send` | Send a message to a channel |
| `openclaw channels login` | Authenticate with a channel |
| `openclaw channels status` | Check channel health |
| `openclaw config set` | Set configuration values |
| `openclaw models list` | List available AI models |
| `openclaw browser` | Manage browser instances |
| `openclaw skills` | Manage skills |
| `openclaw plugins` | Manage plugins |
| `openclaw nodes` | Manage device nodes |
| `openclaw doctor` | Diagnose issues |
| `openclaw update` | Update OpenClaw |
| `openclaw pairing` | Manage device pairing |
| `openclaw cron` | Manage cron jobs |
| `openclaw tui` | Launch Terminal UI |
| `openclaw acp` | Start ACP bridge (IDE integration) |

---

## 12. UI — Control Panel & WebChat

The UI lives in `ui/` and is a **Vite + Lit** web application.

| Technology | Purpose |
|-----------|---------|
| **Vite** | Build tool & dev server |
| **Lit** | Web Components framework (by Google) |
| **DOMPurify** | HTML sanitization |
| **marked** | Markdown rendering |
| **@noble/ed25519** | Cryptographic signatures |

The UI provides:
- **Control Panel** — Dashboard to monitor Gateway status, channels, sessions
- **WebChat** — Chat with the assistant directly in the browser
- **Settings** — Configure the assistant through a web interface

The built UI is served directly by the Gateway's HTTP server — no separate web server needed.

---

## 13. Browser Control

OpenClaw can **control a web browser** for the AI agent. This is powerful — the agent can browse the web, fill forms, take screenshots, and interact with web pages.

**Technology:** Playwright-core + Chrome DevTools Protocol (CDP)

**Key files in `src/browser/`:**
- `chrome.ts` — Finds/launches Chrome/Chromium
- `cdp.ts` — Chrome DevTools Protocol connection
- `pw-session.ts` — Playwright session management
- `pw-tools-core.*.ts` — Tool implementations (click, type, navigate, screenshot, etc.)
- `server-context.ts` — Tab and context management
- `extension-relay.ts` — Browser extension communication

---

## 14. Skills & Plugins (Extension System)

### Skills (`skills/`)

Skills are **tool bundles** that add capabilities to the agent. Each skill is a folder with a `SKILL.md` file that describes what tools it provides.

There are **53 bundled skills** including:

| Category | Skills |
|----------|--------|
| **Productivity** | 1Password, Apple Notes, Apple Reminders, Bear Notes, Notion, Obsidian, Things, Trello |
| **Communication** | Discord, Slack, BlueBubbles, iMessage, WhatsApp CLI |
| **Media** | OpenAI Image Gen, OpenAI Whisper, Video Frames, Peekaboo (camera), Songsee |
| **Development** | GitHub, Coding Agent, Skill Creator |
| **Smart Home** | OpenHue (Philips Hue), Sonos CLI |
| **Information** | Weather, Local Places, Go Places, Blog Watcher |
| **System** | Canvas, Health Check, Session Logs, Model Usage, Tmux |
| **AI** | Gemini, Oracle, Summarize |

### Plugins (Extensions)

Plugins are more heavyweight than skills. They live in `extensions/` and are full npm packages with their own `package.json`. They can:
- Add new messaging channels
- Add new authentication providers
- Add new features (memory, voice call, etc.)

Plugin loading is handled by `src/plugins/` and `src/plugin-sdk/`.

---

## 15. Companion Apps (macOS, iOS, Android)

### macOS App (`apps/macos/`)
- **Language:** Swift + SwiftUI
- **Features:** Menu bar control, Voice Wake, Push-to-Talk, WebChat, Debug tools
- **Runs as:** Menu bar app (always visible in system tray)
- **Node mode:** Can also run as a "node" exposing system.run, camera, screen recording

### iOS App (`apps/ios/`)
- **Language:** Swift
- **Build:** Xcodegen + Xcode
- **Features:** Canvas, Voice Wake, Talk Mode, Camera, Screen recording
- **Pairing:** Bonjour/mDNS discovery, pairs with Gateway

### Android App (`apps/android/`)
- **Language:** Kotlin
- **Build:** Gradle
- **Features:** Canvas, Talk Mode, Camera, Screen recording, optional SMS
- **Pairing:** Same Bridge + pairing flow as iOS

### Shared Code (`apps/shared/`)
- **OpenClawKit** — Shared Swift library used by both macOS and iOS apps

---

## 16. Deployment & Docker

### Deployment Options

| Method | Config File | Notes |
|--------|------------|-------|
| **Local (recommended)** | — | `openclaw gateway` runs on your machine |
| **Docker** | `Dockerfile` + `docker-compose.yml` | Containerized deployment |
| **Fly.io** | `fly.toml` | Cloud VM deployment |
| **Render** | `render.yaml` | Cloud deployment |
| **Nix** | External repo | Declarative config |

### Dockerfile Explained

```dockerfile
FROM node:22-bookworm         # Base: Debian with Node 22

# Install Bun (needed for build scripts)
RUN curl -fsSL https://bun.sh/install | bash

RUN corepack enable           # Enable pnpm

WORKDIR /app

# Copy dependency files first (Docker layer caching optimization)
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
COPY ui/package.json ./ui/package.json
COPY patches ./patches
COPY scripts ./scripts

RUN pnpm install --frozen-lockfile   # Install dependencies

COPY . .                             # Copy all source code
RUN pnpm build                       # Build TypeScript → dist/
RUN pnpm ui:build                    # Build the Control UI

ENV NODE_ENV=production

# Security: run as non-root user
USER node

# Start the gateway
CMD ["node", "dist/index.js", "gateway", "--allow-unconfigured"]
```

**Why is the Dockerfile complex?**
1. It installs both Node.js AND Bun (Bun is used for build scripts)
2. It does a multi-step copy (dependency files first, then source) for Docker layer caching
3. It builds both the TypeScript backend AND the UI frontend
4. It runs as a non-root user for security
5. It supports optional APT packages via build args

### Docker Compose (`docker-compose.yml`)

Two services:
1. **openclaw-gateway** — The main server (always running)
2. **openclaw-cli** — A companion container for running CLI commands

---

## 17. Testing Strategy

### Framework: Vitest

OpenClaw uses **Vitest** with multiple configuration profiles:

| Config | Purpose |
|--------|---------|
| `vitest.config.ts` | Main test suite |
| `vitest.unit.config.ts` | Unit tests only |
| `vitest.e2e.config.ts` | End-to-end tests |
| `vitest.live.config.ts` | Tests using real API keys |
| `vitest.extensions.config.ts` | Extension tests |
| `vitest.gateway.config.ts` | Gateway-specific tests |

### Coverage
- **V8 coverage provider**
- **70% threshold** for lines, branches, functions, and statements

### Test Organization
- Tests are **co-located** with source files: `foo.ts` → `foo.test.ts`
- E2E tests use the suffix `.e2e.test.ts`
- Live tests (requiring real API keys) use `.live.test.ts`

### Docker Tests
Extensive Docker-based E2E tests:
- `test:docker:live-models` — Test with real LLM models
- `test:docker:onboard` — Test onboarding flow
- `test:docker:gateway-network` — Test gateway networking
- `test:docker:plugins` — Test plugin system

---

## 18. Security Model

### DM Pairing (Default)
By default, unknown senders receive a **pairing code**. You must approve them via `openclaw pairing approve <channel> <code>`. This prevents random people from talking to your assistant.

### Sandbox Mode
For group/channel sessions, tool execution can run inside **Docker sandboxes**:
- Each non-main session gets its own container
- Bash commands run inside the container, not on the host
- Configurable allowlists/denylists for tools

### Gateway Auth
The Gateway supports:
- **Token auth** — Shared secret token
- **Password auth** — User/password
- **Tailscale identity** — When using Tailscale Serve

### Elevated Access
The `/elevated on|off` chat command toggles elevated host permissions per-session.

---

## 19. Complete Feature List

### Core Features
- ✅ Multi-channel messaging (14+ platforms)
- ✅ AI agent with tool use (bash, browser, files, etc.)
- ✅ Multi-model support (Anthropic, OpenAI, Google, Ollama, etc.)
- ✅ Model failover & auth profile rotation
- ✅ Session management with context compaction
- ✅ Multi-agent routing (different agents for different channels)
- ✅ Skills system (53 bundled skills)
- ✅ Plugin/extension architecture (31 extensions)
- ✅ Onboarding wizard
- ✅ Configuration hot-reload

### Communication Features
- ✅ DM and group chat support
- ✅ Mention gating (only respond when @mentioned in groups)
- ✅ Chat commands (/status, /reset, /compact, /think, etc.)
- ✅ Media pipeline (images, audio, video, PDF)
- ✅ Typing indicators
- ✅ Reactions/acknowledgments

### Automation Features
- ✅ Cron jobs & scheduled wakeups
- ✅ Webhooks (inbound HTTP triggers)
- ✅ Gmail Pub/Sub integration
- ✅ Browser automation

### Platform Features
- ✅ macOS menu bar app
- ✅ iOS app (Canvas, Voice Wake, Talk Mode)
- ✅ Android app (Canvas, Talk Mode)
- ✅ Voice Wake (always-on speech)
- ✅ Talk Mode (continuous conversation)
- ✅ Live Canvas (A2UI visual workspace)
- ✅ WebChat (browser-based chat)
- ✅ Control UI (web dashboard)
- ✅ Terminal UI (TUI)
- ✅ ACP bridge (IDE integration, e.g., Zed)

### Ops Features
- ✅ Docker deployment
- ✅ Fly.io / Render deployment
- ✅ Tailscale integration (Serve/Funnel)
- ✅ SSH tunnel support
- ✅ Health checks & diagnostics (`openclaw doctor`)
- ✅ Structured logging
- ✅ OpenAI-compatible HTTP API

---

## 20. How OpenClaw Differs From Other AI Assistants

| Feature | ChatGPT / Claude Web | Siri / Alexa | OpenClaw |
|---------|---------------------|-------------|----------|
| **Where it runs** | Cloud (their servers) | Cloud | **Your devices** (self-hosted) |
| **Data ownership** | Theirs | Theirs | **Yours** |
| **Messaging integration** | Separate app/website | Voice only | **14+ channels** (WhatsApp, Telegram, etc.) |
| **Tool execution** | Limited (sandboxed) | Limited | **Full system access** (bash, browser, files) |
| **Customization** | Minimal | Minimal | **Deep** (skills, plugins, multi-agent, prompt files) |
| **Multi-model** | Single provider | Fixed | **Any model** (Anthropic, OpenAI, Google, Ollama, etc.) |
| **Always-on** | No | Yes | **Yes** (daemon/service) |
| **Open source** | No | No | **Yes** (MIT License) |
| **Agent framework** | Proprietary | Proprietary | **Pi** (open agent framework) |
| **Browser control** | No (ChatGPT has limited) | No | **Full** (Playwright/CDP) |
| **Voice** | Limited | Core feature | **Voice Wake + Talk Mode** |
| **Visual workspace** | No | No | **Canvas (A2UI)** |
| **Cost** | Subscription | Free (limited) | **BYO API keys** (pay per use) |

**In short:** OpenClaw is unique because it's a **local-first, self-hosted, multi-channel AI assistant** that bridges all your messaging apps into one intelligent assistant. It has the tool capabilities of a coding agent, the reach of a chatbot, and the control of a self-hosted solution.

---

## 21. End-to-End Message Flow (Putting It All Together)

Here's what happens when you send "What's the weather in Tokyo?" to your OpenClaw assistant via WhatsApp:

```
1. 📱 YOU: Type "What's the weather in Tokyo?" in WhatsApp

2. 📡 WHATSAPP (Baileys):
   - src/whatsapp/ receives the message via Baileys WebSocket
   - Extracts sender, message text, media, group info

3. 📡 CHANNEL DOCK (dock.ts):
   - Validates sender against allowlist
   - Checks pairing status
   - Normalizes the message format

4. 🔀 ROUTING (resolve-route.ts):
   - Determines session key: "main" (your DM)
   - Resolves which agent handles this session
   - Checks activation rules

5. 🏗  GATEWAY (server-chat.ts):
   - Looks up or creates the session
   - Loads conversation history
   - Enqueues the message for agent processing
   - Shows typing indicator on WhatsApp

6. 🤖 PI AGENT (pi-embedded-runner.ts):
   a. system-prompt.ts builds the full system prompt:
      - Base identity (AGENTS.md, SOUL.md)
      - Tool descriptions
      - Skills context
      - Date/time, user info
   
   b. model-selection.ts picks the model:
      - e.g., "anthropic/claude-opus-4-6"
   
   c. model-auth.ts authenticates:
      - Loads API key or OAuth token
      - Applies auth profile rotation if needed
   
   d. Sends to LLM API (Anthropic):
      - System prompt + conversation history + new message
      - Streams response back
   
   e. LLM responds with tool call:
      - "I want to use the 'bash' tool with command: curl wttr.in/Tokyo"
   
   f. bash-tools.exec.ts executes the command:
      - Runs `curl wttr.in/Tokyo` in a pseudo-terminal
      - Captures output
   
   g. Tool result fed back to LLM
   
   h. LLM generates final response:
      - "The weather in Tokyo is currently 22°C and sunny..."

7. 🏗  GATEWAY:
   - Receives the streaming response
   - pi-embedded-subscribe.ts processes stream events
   - Chunks the response for WhatsApp (character limits)

8. 📡 WHATSAPP (Baileys):
   - Sends the reply message(s) back to WhatsApp
   - Clears typing indicator

9. 📱 YOU: See the weather response in WhatsApp! 🌤️
```

---

## Summary

OpenClaw is a **remarkably ambitious project** — a full-stack personal AI assistant with:
- **~50 source modules** in `src/`
- **31 channel extensions** in `extensions/`
- **53 skills** in `skills/`
- **3 native apps** (macOS, iOS, Android)
- **A web UI** built with Lit + Vite
- **Multiple deployment options** (local, Docker, Fly.io, Render)

The architecture is a **modular monolith** — one process, many internal modules with clean boundaries. The Gateway is the hub, the Pi agent is the brain, channels are the arms, and skills/plugins are the hands.

For a new developer, the best path to understanding is:
1. Start with `src/index.ts` → `src/entry.ts` → `src/cli/run-main.ts` (the boot sequence)
2. Then `src/gateway/server.impl.ts` (the Gateway)
3. Then `src/agents/pi-embedded-runner.ts` (the agent)
4. Then `src/channels/dock.ts` + a specific channel like `src/whatsapp/` (messaging)
5. Then `src/config/schema.ts` (configuration)

From there, you can explore any module based on what you're working on.

---

*Document generated on 2026-03-20. Based on OpenClaw version 2026.2.6.*
