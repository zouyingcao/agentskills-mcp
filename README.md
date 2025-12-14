# <img src="docs/figure/agentskills-logo.png" alt="Agent Skills MCP Logo" width="5%" style="vertical-align: middle;"> AgentSkills MCP: Bringing Anthropic's Agent Skills to Any MCP-compatible Agent

<p align="center">
  <strong></strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/mcp-agentskills/"><img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python Version"></a>
  <a href="https://pypi.org/project/mcp-agentskills/"><img src="https://img.shields.io/pypi/v/mcp-agentskills.svg?logo=pypi" alt="PyPI Version"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-black" alt="License"></a>
  <a href="https://github.com/zouyingcao/agentskills-mcp"><img src="https://img.shields.io/github/stars/zouyingcao/agentskills-mcp?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="./README_ZH.md">简体中文</a> | English
</p>


## 📖 Project Overview

**Agent Skills** is a new function recently introduced by Anthropic. By packaging specialized skills into modular resources, it allows Claude to transform on demand into a “tailored expert” suited to any scenario.
**AgentSkills MCP**, built on the [FlowLLM](https://github.com/flowllm-ai/flowllm) framework, unlocks Claude’s proprietary Agent Skills for any MCP-compatible agent.
It implements the **Progressive Disclosure** architecture proposed in Anthropic’s official [Agent Skills engineering blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills), enabling agents to load necessary skills as needed, thereby efficiently utilizing limited context windows.

### 💡 Why Choose AgentSkills MCP?

- ✅ **Zero-Code Configuration**: one-command install (`pip install mcp-agentskills`)
- ✅ **Out-of-the-Box**: uses official Skill format and fully compatible with [Anthropic’s Agent Skills](https://github.com/anthropics/skills)
- ✅ **MCP Support**: multiple transports (stdio/SSE/HTTP), works with any MCP-compatible agent<!-- - ✅ **Progressive Disclosure**: smart context loading, minimal overhead until skills are needed -->
- ✅ **Flexible Skill Path**: custom skill directories with automatic detection, parsing, and loading

## 🔥 Latest Updates

- [2025-12] 🎉 Released mcp-agentskills v0.1.1

## 🚀 Quick Start

### Installation

Install AgentSkills MCP with pip:

```bash
pip install mcp-agentskills
```

Or with uv:

```bash
uv pip install mcp-agentskills
```

<details>
<summary><strong>For Development (if you want to modify the code):</strong></summary>

```bash
git clone https://github.com/zouyingcao/agentskills-mcp.git
cd agentskills-mcp

conda create -n agentskills-mcp python==3.10
conda activate agentskills-mcp
pip install -e .
```
</details>

---
### Load Skills

1. Create a directory to store Skills, like:

```bash
mkdir skills
```

2. Clone from open-source GitHub repositories, e.g.,

```bash
https://github.com/anthropics/skills
https://github.com/ComposioHQ/awesome-claude-skills
```

3. Add the collected Skills into the directory created in step 1. Each Skill is a folder containing a SKILL.md file.

---

### Run

<details>
<summary><strong>Local process communication (stdio)</strong></summary>

<p align="left">
  <sub>This mode runs AgentSkills MCP via <code>uvx</code> and communicates through stdin/stdout, suitable for local MCP clients.</sub>
</p>

```json
{
  "mcpServers": {
    "agentskills-mcp": {
      "command": "uvx",
      "args": [
        "agentskills-mcp",
        "config=default",
        "mcp.transport=stdio",
        "metadata.skill_dir=\"./skills\""
      ],
      "env": {
        "FLOW_LLM_API_KEY": "xxx",
        "FLOW_LLM_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1"
      }
    }
  }
}
```
</details>

<details>
<summary><strong>Remote communication (SSE/HTTP Server)</strong></summary>

<p align="left">
  <sub>This mode runs AgentSkills MCP as a standalone SSE/HTTP server that can be accessed remotely.</sub>
</p>

**- Step 1:** Configure Environment Variables

Copy `example.env` to `.env` and fill in your API key:

```bash
cp example.env .env
# Edit the .env file and fill in your API key
```

**- Step 2:** Start the Server

Start the AgentSkills MCP server with SSE transport:

```bash
agentskills-mcp \
  config=default \
  mcp.transport=sse \
  mcp.host=0.0.0.0 \
  mcp.port=8001 \
  metadata.skill_dir="./skills"
```

The service will be available at: `http://0.0.0.0:8001/sse`

**- Step 3:** Connect from MCP Client

  - Add this configuration to your MCP client (Cursor, Gemini Code, Cline, etc.) to connect to the remote SSE server:

```json
{
  "mcpServers": {
    "agentskills-mcp": {
      "type": "sse",
      "url": "http://0.0.0.0:8001/sse"
    }
  }
}
```

  - You can also use the [FastMCP](https://gofastmcp.com/getting-started/welcome) Python client to directly access the server:

```python
import asyncio
from fastmcp import Client


async def main():
    async with Client("http://0.0.0.0:8001/sse") as client:
        tools = await client.list_tools()
        for tool in tools:
            print(tool)

        result = await client.call_tool(
            name="load_skill",
            arguments={
              "skill_name"="pdf"
            }
        )
        print(result)


asyncio.run(main())
```

#### One-Command Test

<p align="left">
  <sub>This command will start the server, connect via FastMCP client, and test all available tools automatically.</sub>
</p>

```bash
python tests/run_project_sse.py <path/to/skills>
or
python tests/run_project_http.py <path/to/skills>
```

</details>

### Demo

After starting the AgentSkills MCP server with the SSE transport, you can run the demo:

```bash
# Enable Agent Skills for the Qwen model.
# Since Qwen supports function calling, you can implement Agent Skills by passing the MCP tools registered by the AgentSkills MCP service to the tools parameter.
cd tests
python run_skill_agent.py
```

---
## 🔧 MCP Tools

This service provides four tools to support Agent Skills:
- **load_skill_metadata_op** — Loads the names and descriptions of all Skills into the agent context at startup (always called)
- **load_skill_op** — When a specific skill is needed, loads the SKILL.md content by skill name (invoked when triggering the Skill)
- **read_reference_file_op** — Reads specific files from a skill, such as scripts or reference documents (on demand)
- **run_shell_command_op** — Executes shell commands to run executable scripts included in the skill (on demand)

For detailed parameters and usage examples, see the [documentation](docs/tools.md).

## ⚙️ Server Configuration Parameters

| Parameter               | Description                                                                                                                                                  | Example                                 |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|
| `config`               | Configuration files to load (comma-separated). Default: `default` (core workflow)                                                                           | `config=default`                        |
| `mcp.transport`        | Transport mode: `stdio` (stdin/stdout, good for local), `sse` (Server-Sent Events, good for online apps), `http` (RESTful, good for lightweight remote calls) | `mcp.transport=stdio`                   |
| `mcp.host`             | Host address (for sse/http transport only)                                                                                                                             | `mcp.host=0.0.0.0`                      |
| `mcp.port`             | Port number (for sse/http transport only)                                                                                                                                     | `mcp.port=8001`                         |
| `metadata.skill_dir`   | Skills Directory (required)                                                                                                                       | `metadata.dir=./skills`                 |
<!-- | `llm.default.model_name` | Default LLM model name (overrides settings in config files)                                                                                             | `llm.default.model_name=qwen3-30b-a3b-thinking-2507` | -->

For the full set of available options and defaults, refer to [default.yaml](./agentskills_mcp/config/default.yaml).

#### Environment Variables

| Variable Name                  | Required | Description                                  |
|----------------------|----------|----------------------------------------------|
| `FLOW_LLM_API_KEY`   | ✅ Yes   | API key for OpenAI-compatible LLM Service       |
| `FLOW_LLM_BASE_URL`  | ✅ Yes   | Base URL for OpenAI-compatible LLM Service    |

---

## 🤝 Contributing

We welcome community contributions! To get started:

1. Install the package in development mode:
```bash
pip install -e .
```

2. Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit run --all-files
```

3. Submit a pull request with your changes.

---

## 📚 Learn More

- [Anthropic Agent Skills Documentation](https://code.claude.com/docs/zh-CN/skills)
- [Anthropic Engineering Blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [FlowLLM Documentation](https://flowllm-ai.github.io/flowllm/)
- [MCP Documentation](https://modelcontextprotocol.io/docs/getting-started/intro)

## ⚖️ License

This project is licensed under the Apache License 2.0 — see [LICENSE](./LICENSE) for details.

---

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=zouyingcao/agentskills-mcp&type=Date)](https://www.star-history.com/#zouyingcao/agentskills-mcp&Date)