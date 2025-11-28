from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.genai import types
from typing import Dict, Any, Optional

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    agent_name = callback_context.agent_name
    print(f'[INFO] Agent {agent_name} is thinking...')
    return None

def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    agent_name = callback_context.agent_name
    print(f'[INFO] Agent {agent_name} has finished thinking.')
    return None

def before_tool_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
    tool_name = tool.name
    agent_name = tool_context.agent_name
    print(f'[INFO] Agent {agent_name} is using tool {tool_name} with args {args}')
    return None

def after_tool_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict) -> Optional[Dict]:
    tool_name = tool.name
    agent_name = tool_context.agent_name
    print(f'[INFO] Agent {agent_name} has finished using tool {tool_name} with response {tool_response}')
    return None
    
