# in agents_setup.py or similar
from tools.playwright_tool import playwright_web_read 
from prompts.agent_prompts import final_summarizer_prompt
from agents import Agent
from dotenv import load_dotenv
import os

load_dotenv(override=True)
default_model_name = os.environ.get('DEFAULT_MODEL_NAME')

final_report_agent = Agent(
    name="Final Report Agent",
    instructions=final_summarizer_prompt,
    tools=[playwright_web_read],   # so it can open a few URLs if needed
    model=default_model_name
)