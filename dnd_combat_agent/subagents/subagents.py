from google.adk.agents import Agent, SequentialAgent
from google.genai import types
from google.adk.models.google_llm import Gemini
from .output_schema import MonsterContent, BattlegroundContent


retry_config=types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504], # Retry on these HTTP errors
)

theme_agent = Agent(
    name='theme_agent',
    description="A storyteller agent that generates the battle's theme.",
    model= Gemini(
        model='gemini-2.5-flash',
        retry_options=retry_config,
    ),
    instruction="""
    You are a Fantasy Author. Your task is to generate a creative 2-sentences background hook for a D&D combat.
    - The background hook will be used for a battle between ONE person and ONE monster. 
    - Do NOT invent a name for the protagonist. Always refer to them as "you".
    - The setting must be FLAT terrain (e.g., swamp, forest floor, frozen lake, magma river). Do NOT use towers, cliffs, stairs, or rooftops
    
    IMPORTANT: Only output the background hook. DO NOT include any other text.
    """,
    output_key='theme',
)

monster_generator = Agent(
    name='Monster_generator',
    model=Gemini(
        model='gemini-2.5-flash',
        retry_options=retry_config,
    ),
    description='An agent that generates a monster for a D&D combat.',
    instruction="""
    You are a Game Designer. Your task is to design a monster for a D&D combat based on a given background story.
    You need to decide the following attributes of a monster:
    - Name: The name of the monster, based on the background story.
    - Monster Emoji: The emoji to represent the monster.
    - HP: The hit points of the monster. From 15 to 50.
    - AC: The armor class of the monster. From 1 to 20.
    - Damage: The attack damage range of the monster. It should be provided as a list of two integers. You can pick any interval in [1, 15].
    - Speed: The speed of the monster. From 1 to 5.
    Note: you need to make a balance! A monster that has high ac and hp usually has low damage and speed.

    background story: {theme}

    IMPORTANT: You response MUST be valid JSON matching this structure:
    {
    "name": "the monster's name",
    "monster_emoji": "the emoji to represent the monster",
    "hp": 20,
    "ac": 10,
    "damage": [5, 10],
    "speed": 3
    }
    """,
    output_key='monster',
    output_schema=MonsterContent,
)

bg_design_agent = Agent(
    name='battleground_design_agent',
    description='An agent that sets the battle ground',
    model=Gemini(
        model='gemini-2.5-flash',
        retry_options=retry_config,
    ),
    instruction="""
    You are a Map Designer. Your task is to decide the size and environment of the battle ground for a D&D combat based on a given background story.
    The battle ground is a grid and you need to decide the length and width of the grid.
    Inside the battle ground, you need to pick a rectangle area with a special environment.
    The environment has two types: 'SLOW' and 'DAMAGE'. You need to decide it based on the background story.
    For example, a magma river is 'DAMAGE', but an ice/sand surface is 'SLOW'.
    And you need to choose an emoji to represent that environment.
    You also need to decide the start position of the user and the monster. You need to decide their positions based on the background story.
    The top-left position of grid is (0, 0).

    Things to do:
    - Decide the length and width of the grid as a list, e.g [5, 5]
    - Decide the top-left and bottom-right positions of the rectangle area, e.g [0, 1], [2, 3]
    - Decide the environment type of the rectangle area, it should be EXACTLY 'SLOW' or 'DAMAGE'
    - Decide the emoji to represent the environment, e.g 🔥 for fire, 🌊 for wave/water, etc.
    - Decide the start position of the user, e.g [0, 2]
    - Decide the start position of the monster, e.g [3, 4]

    background story: {theme}

    IMPORTANT: You response MUST be valid JSON matching this structure:
    {
    "size": [row, col],
    "rectangle_position": [[r1, c1], [r2, c2]],
    "environment": "The environment type of the rectangle area.",
    "environment_emoji": "The emoji to represent the environment.",
    "user_position": [row, col],
    "monster_position": [row, col]
    }
    """,
    output_key='battleground',
    output_schema=BattlegroundContent,
)

bg_initializer = SequentialAgent(
    name='battle_ground_initializer',
    description='A pipeline to initialize a battle ground.',
    sub_agents=[theme_agent, monster_generator, bg_design_agent],
)