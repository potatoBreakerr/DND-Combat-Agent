from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.genai import types
from typing import Dict, Any, Optional
import re

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    agent_name = callback_context.agent_name
    print(f'[INFO] Agent {agent_name} is thinking...')
    return None

def _extract_first_emoji(text: str) -> str:
    """
    Extract the first emoji from a string.
    Emojis are typically in the Unicode ranges U+1F300–U+1F9FF
    """
    if not text:
        return '👾'  # Default emoji if none found
    
    # Find all emoji-like characters
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F9FF"  # Most common emoji range
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F680-\U0001F6FF"  # Transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # Flags
        "]+", 
        flags=re.UNICODE
    )
    
    emojis = emoji_pattern.findall(text)
    if emojis:
        # Return only the first character of the first emoji match
        return emojis[0][0] if len(emojis[0]) > 0 else '👾'
    
    # If no emoji found, return default
    return '👾'

def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    agent_name = callback_context.agent_name
    
    # Special handling for Monster_generator to ensure single emoji
    if agent_name == 'Monster_generator':
        state = callback_context.state
        if state and 'monster' in state:
            monster = state.get('monster', {})
            if isinstance(monster, dict) and 'monster_emoji' in monster:
                original_emoji = monster.get('monster_emoji', '👾')
                # Ensure only one emoji character
                clean_emoji = _extract_first_emoji(original_emoji)
                
                if clean_emoji != original_emoji:
                    print(f'[INFO] Cleaned monster emoji: "{original_emoji}" -> "{clean_emoji}"')
                    # Update the state with cleaned emoji
                    monster_copy = dict(monster)
                    monster_copy['monster_emoji'] = clean_emoji
                    state['monster'] = monster_copy
    
    # Special handling for battleground_design_agent to ensure single environment emoji
    if agent_name == 'battleground_design_agent':
        state = callback_context.state
        if state and 'battleground' in state:
            battleground = state.get('battleground', {})
            if isinstance(battleground, dict) and 'environment_emoji' in battleground:
                original_emoji = battleground.get('environment_emoji', '⚡')
                # Ensure only one emoji character
                clean_emoji = _extract_first_emoji(original_emoji)
                
                if clean_emoji != original_emoji:
                    print(f'[INFO] Cleaned environment emoji: "{original_emoji}" -> "{clean_emoji}"')
                    # Update the state with cleaned emoji
                    battleground_copy = dict(battleground)
                    battleground_copy['environment_emoji'] = clean_emoji
                    state['battleground'] = battleground_copy
    
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
    
