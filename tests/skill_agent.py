"""Enable Agent Skills for the Qwen model.

Since Qwen supports function calling,
you can implement Agent Skills by passing the MCP tools
registered by the AgentSkills MCP service to the tools parameter.
"""

import json
import datetime
from typing import Dict
from loguru import logger
from jinja2 import Template
from skill_agent_prompt import SYSTEM_PROMPT, SYSTEM_PROMPT_ZH

from flowllm.core.enumeration import Role
from flowllm.core.llm import OpenAICompatibleLLM
from flowllm.core.schema import Message, ToolCall
from flowllm.core.utils import load_env, FastMcpClient


load_env()


class SkillAgent:
    """A simple ReAct-style agent that does skill-based reasoning.

    It loads skill metadata from a specified directory and makes those skills available
    as tools during the agent's reasoning process. The agent can automatically
    select and use relevant skills based on the user's query.

    The agent:
    1. Loads skill metadata from the specified skill directory
    2. Includes available skills into the agent's context
    3. Uses the React (Reasoning and Acting) pattern to iteratively reason
       and call tools (including skills)

    Attributes:
        model_name: The language model to use (default: "qwen3_30b_instruct")
        max_steps: Maximum number of reasoning steps (default: 50)
        prompt_path (str): Path used for prompt loading

    Note:
        - The skill_dir must contain SKILL.md files with valid metadata
        - Skills metadatas are always loaded via LoadSkillMetadataOp before the agent starts
    """

    def __init__(
        self,
        model_name: str = "qwen3_30b_instruct",
        max_steps: int = 50,
        language: str = "",
    ):
        """Initialize the skill agent with configuration.

        Args:
            llm: The language model identifier to use for reasoning.
                Default is "qwen3_max_instruct".
            max_steps: Maximum number of reasoning steps the agent can take.
                Default is 5. Note: This is passed as max_retries to the parent.
            prompt_path: Path to the prompt file. Default is "skill_agent_prompt.yaml".
        """
        self.llm = OpenAICompatibleLLM(model_name=model_name)
        self.max_steps = max_steps
        self.language = language
        if self.language == "zh":
            self.prompt = Template(SYSTEM_PROMPT_ZH.lstrip())
        else:
            self.prompt = Template(SYSTEM_PROMPT.lstrip())

    async def run(self, query: str):
        """Run the skill agent with the given query.

        Args:
            query: The user's query.

        Returns:
            A string containing the agent's response.
        """
        # Prepare all available tools from the MCP server.
        tool_dict: Dict[str, ToolCall] = {}
        async with FastMcpClient(
            name="agentskills_mcp_client",
            config={
                "type": "sse",
                "url": "http://0.0.0.0:8001/sse",
            },
        ) as mcp_client:
            tool_calls = await mcp_client.list_tool_calls()
            for tool_call in tool_calls:
                tool_dict[tool_call.name] = tool_call

                # Log the tool call schema in Qwen3-compatible format for debugging.
                # (This is the standard "tool" format for Qwen3 / BaiLian.)
                tool_call_str = json.dumps(tool_call.simple_input_dump(), ensure_ascii=False, indent=2)
                logger.info(f"tool_call {tool_call.name} {tool_call_str}")

            logger.info(f"SkillAgent processing query: {query}")

            # Get current time for the system prompt
            now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Build the initial conversation messages
            messages = [
                Message(
                    role=Role.SYSTEM,
                    content=self.prompt.render(
                        {
                            "time": now_time,
                        },
                    ),
                ),
                Message(role=Role.USER, content=query),
            ]

            # Main ReAct loop.
            for i in range(self.max_steps):
                # Ask the LLM what to do next.
                # You can plug in your own tool-calling strategy here.
                assistant_message: Message = await self.llm.achat(
                    messages=messages,
                    tools=[
                        tool_dict["load_skill_metadata"],
                        tool_dict["load_skill"],
                        tool_dict["read_reference_file"],
                        tool_dict["run_shell_command"],
                    ],
                )

                messages.append(assistant_message)
                print(i)
                print(assistant_message.content)
                if assistant_message.content == "task_complete":
                    break

                if assistant_message.tool_calls:
                    for j, tool_call in enumerate(assistant_message.tool_calls):
                        if tool_call.name not in tool_dict:
                            logger.exception(f"unknown tool_call.name={tool_call.name}")
                            continue

                        logger.info(
                            f"round{i + 1}.{j} submit tool_calls={tool_call.name} "
                            f"argument={tool_call.argument_dict}",
                        )

                        # Execute the tool via MCP and parse the result.
                        result = await mcp_client.call_tool(
                            tool_call.name,
                            arguments=tool_call.argument_dict,
                            parse_result=True,
                        )

                        # Attach the tool result as a TOOL-role message so the LLM
                        # can see and reason about it in the next step.
                        messages.append(
                            Message(
                                role=Role.TOOL,
                                tool_call_id=tool_call.id,
                                content=result,
                            ),
                        )
                        print(result)
