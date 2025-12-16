"""Integration test for the skill-based react pipeline."""

import asyncio

from loguru import logger
from skill_agent import SkillAgent


async def main():
    """Run the skill-based react flow for a simple PDF filling task."""
    model_name = "qwen3-max"
    agent = SkillAgent(model_name=model_name, max_steps=50)

    # Run the ReAct loop with Agent Skills.
    query = (
        "Fill /abosulte/path/to/Sample-Fillable-PDF.pdf with: name='Alice Johnson'select first choice from dropdown, "
        "check options 1 and 3, dependent name='Bob Johnson', age='12'. Save as filled-sample.pdf"
    )
    messages = await agent.run(query)

    logger.info(f"result: {messages}")


if __name__ == "__main__":
    asyncio.run(main())
