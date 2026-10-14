# Lux in Tenebris — AI dispatches · October 14, 2026

> A daily dark-broadsheet recap of the most disruptive AI news from the last 24 hours.
> Issue No. 111 · https://luxintenebris.news/

## Lead Argon goes global: Google DeepMind releases Gemini 4 Argon worldwide

Google DeepMind launched Gemini 4 Argon, a frontier model for end-to-end coding, enterprise workflows and cyber defense, now available via the Gemini app, Gemini API, AI Studio and Antigravity. DeepMind claims a 15% hallucination rate on AA-Omniscience (versus 51% for GPT-6 Astra) and the top rank on the Vals Index.

Source: [GoogleDeepMind](https://x.com/GoogleDeepMind/status/2110039274922131792)

## Top stories

### Anthropic replaces Git as agent-driven merges explode past 30,000 a day

Daily merges at Anthropic grew from roughly 2,500 in May to over 30,000 in September as AI agents scaled coding, forcing the lab to build an in-house source control system and migrate its monorepo off Git in five months.

Source: [AnthropicAI](https://x.com/AnthropicAI/status/2110047081414987957)

### Astribot raises $149.4M at a $2.1B valuation to scale humanoids and embodied AI

The Shenzhen-based maker of cable-driven humanoids and Lumo embodied AI models closed its fourth round in six months, led by Shenzhen Investment Holdings-linked capital with Hongtai Fund and Shanheng Capital participating.

Source: [Tech Startups](https://techstartups.com/2026/10/13/startup-funding-news-today-october-13-2026-astribot-carbonfarm-ubitium-epyr-more/)

### Nvidia to announce $2 billion in new European AI investments

Jensen Huang said in Paris that Nvidia will unveil $2 billion in European AI investments within a week, on top of roughly $8 billion already deployed across the continent over the past year.

Source: [Semafor](https://www.semafor.com/article/10/13/2026/nvidia-to-announce-2b-in-european-investments)

## Research & Papers

- **[DeepMind's Evo2 co-evolves agent harnesses and model weights](https://x.com/omarsar0/status/2110006902331769049)** — Evo2 treats harness edits and their outcomes as training data (SFT plus interleaved GRPO), lifting SWE-bench Verified to 48.3% from a 41% baseline and raising a GPT-5-mini agent from 24.4% to 48.3% with the evolved harness alone. *(omarsar0)*
- **[Proximal KL regularization fixes biased token-wise importance sampling in off-policy RLVR](https://arxiv.org/abs/2610.18738)** — The paper proves that token-wise importance weighting in off-policy RL with verifiable rewards is generally biased, and introduces a proximal KL regularizer that provably corrects it — enabling safe off-policy RLVR from asynchronous generation and response reuse. *(arXiv)*
- **[SEAR: frontier LLM agents that write, test and retain robot control code](https://arxiv.org/abs/2610.18792)** — SEAR is a framework and benchmark where agents write robot control code, test it, and keep what works as skills and memories — probing whether the agent genuinely learns versus merely appearing to improve. *(arXiv)*
- **[DoubtLess: training-free contrastive decoding that stops overlong chains of thought](https://arxiv.org/abs/2610.18862)** — A training-free decoding method that adaptively identifies when a model's intermediate reasoning is sufficient, cutting overlong reasoning without extra training, steering vectors or decoding heuristics. *(arXiv)*
- **[Hybrid Reasoning Agents reason in latent space but act in text](https://arxiv.org/abs/2610.18861)** — The architecture bridges latent reasoning's efficiency with the native tool access and transparency of text-based LLM agents, reasoning in a latent space while acting and using tools through text. *(arXiv)*

## Open Source & Models

- **[Fish Audio releases Drama 3, an open-weight TTS with per-word emotion control](https://x.com/omarsar0/status/2110043016094212546)** — The open-weight text-to-speech model offers per-word tone and emotion control, mid-sentence voice shifts and plain-language delivery direction; demos have gone viral. *(omarsar0)*
- **[LongHarness: a model-agnostic harness for 100M+ token contexts](https://x.com/omarsar0/status/2110083302728323346)** — LongHarness keeps evidence and open conclusions as explicit state instead of chat history, jumping GLM-5.3-Flash from 4.4% to 61.1% exact match on OfficeQA Pro V2 and outperforming Claude Code and Codex variants. *(omarsar0)*
- **[ScaleDown unveils constrained decoding models claiming 200x faster inference](https://x.com/omarsar0/status/2109984234018332879)** — The models handle 1M-token multimodal inputs for classification, extraction and summarization, reading input once and pointing to answers without token-by-token generation — claimed ~200x faster and 467x cheaper than frontier LLM APIs. *(omarsar0)*
- **[Nous Research pushes local, self-hosted agents after third-party agent failures](https://x.com/NousResearch/status/2110087888721596425)** — Following incidents with cloud agents leaking API keys into logs, Nous argues for local, self-hosted custom agents as the privacy-preserving alternative to closed agent stacks. *(NousResearch)*

## Hardware & Robotics

- **[Gemini 4 Argon teaches robots from video via self-generated simulation](https://x.com/GoogleDeepMind/status/2110078384617464201)** — Gemini 4 Argon watched video, mapped the underlying physics, generated its own simulation and taught Apptronik's Apollo humanoid new tasks — Apollo sank 7 cornhole throws in a row. Google says the approach compresses weeks of manual modeling into hours. *(GoogleDeepMind)*
- **[Promise Robotics partners with D.R. Horton on physical AI for homebuilding](https://www.therobotreport.com/promise-robotics-partners-d-r-horton-physical-ai-homebuilding/)** — A multi-year agreement brings Promise's AI-powered robotic Factory-as-a-Service platform to US housing production, supporting more than 1,250 homes for America's largest homebuilder by volume. *(The Robot Report)*
- **[Science Corporation implants its vision-restoring chip in its first Stargardt patient](https://techcrunch.com/2026/10/13/science-corporation-implants-its-vision-restoring-chip-in-its-first-stargardt-disease-patient/)** — Max Hodak announced the PRIMA vision-restoring chip's first implant in a patient with Stargardt disease, extending the neural implant platform beyond its initial macular degeneration trials. *(TechCrunch)*

## Tools & Startups

- **[Pulse Local brings private, on-device AI budgeting to Mac](https://pulseos.finance)** — A Mac budgeting app whose AI models run entirely on the user's machine, launched on Show HN and quickly climbing to 98 points; currently in beta for Apple Silicon. *(Pulse Local)*
- **[Parsimony: an open-source benchmark measuring how much code AI models add](https://parsimony.lasu.dev/)** — The benchmark quantifies AI-generated code bloat, a growing concern as coding agents proliferate; it reached 64 points on Show HN within a day. *(Parsimony)*
- **[Jevcrawl: a web crawler for AI agents with no LLM in the crawl loop](https://github.com/RayenMlayeh/jevcrawl)** — A web crawler purpose-built for AI agents that deliberately excludes the LLM from the crawl loop, keeping large-scale crawling fast and cheap. Open source on GitHub. *(GitHub)*
- **[GenClass: a 10 MB in-browser model that catches bugs that never throw](https://www.npmjs.com/package/@genclass/runtime)** — A compact machine-learning runtime that runs in the browser via npm and flags silent logic bugs that never surface as exceptions. *(npm)*
- **[AgentGate: a fast authorization gateway for AI agent tools](https://github.com/mohitdebian/AgentGate)** — An open-source gateway that lets developers control which tools an AI agent can invoke, aimed at production agent deployments needing fine-grained tool permissions. *(GitHub)*

## Money & Markets

- **[Pluto Security raises $42M to secure enterprise AI tool and agent usage](https://techcrunch.com/2026/10/13/pluto-security-raises-42m-as-ai-gives-enterprise-security-teams-a-new-headache/)** — The Israeli-US startup, emerging from stealth with $34M Series A led by Jump Capital plus an $8.5M seed, monitors how employees use AI tools, skills, MCP servers and homegrown agents — already at $2M ARR with 30+ enterprise customers including Oscar Health and Workato. *(TechCrunch)*
- **[Ubitium raises $14M seed extension for processors combining sensing, AI inference and real-time control](https://techstartups.com/2026/10/13/startup-funding-news-today-october-13-2026-astribot-carbonfarm-ubitium-epyr-more/)** — The Düsseldorf semiconductor startup's unified processor architecture for autonomous machines is demonstrated in its UB108 chip (256 processing elements, Samsung 8nm), with a 4,096-element UB410 targeted for 2027. *(Tech Startups)*
- **[Clueso raises $10M Series A for AI agents that automate enterprise video production](https://techstartups.com/2026/10/13/startup-funding-news-today-october-13-2026-astribot-carbonfarm-ubitium-epyr-more/)** — The California-Bengaluru startup uses AI agents to create and maintain product tutorials, training and marketing videos that stay accurate as software changes; 1,000+ customers including Atlassian and Zendesk. *(Tech Startups)*
- **[Brellium raises $23M for AI medical billing error and audit protection](https://techstartups.com/2026/10/13/brellium-raises-23m-to-catch-medical-billing-errors-with-ai-and-protect-healthcare-providers-from-costly-audits/)** — The round, led by Left Lane Capital and First Round Capital, was announced alongside CortexLM, an AI system that reviews patient records for documentation errors and compliance risks before claims reach insurers. *(Tech Startups)*
- **[Jinghua Confidential Computing raises ~$14M Pre-A for secure AI infrastructure](https://techstartups.com/2026/10/13/startup-funding-news-today-october-13-2026-astribot-carbonfarm-ubitium-epyr-more/)** — The Beijing startup, founded in 2024, builds encrypted AI model services and an agent-development platform running on Huawei Ascend and Hygon platforms — its third round in six months. *(Tech Startups)*
