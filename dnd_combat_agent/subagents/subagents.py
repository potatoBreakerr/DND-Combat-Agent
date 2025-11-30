from google.adk.agents import Agent, SequentialAgent
from google.genai import types
from google.adk.models.google_llm import Gemini
from .output_schema import MonsterContent, BattlegroundContent
from .dm_agent import dm_agent
from .callbacks import (
    before_agent_callback,
    after_agent_callback,
)


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
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
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
    - Monster Emoji: The emoji to represent the monster. You can only use ONE emoji.
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
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
)

bg_design_agent = Agent(
    name='battleground_design_agent',
    description='An agent that sets the battle ground',
    model=Gemini(
        model='gemini-2.5-flash',
        retry_options=retry_config,
    ),
    instruction="""
    You are a Map Designer. Your task is to create an interesting battle ground for a D&D combat based on a given background story.
    The battle ground is a grid and you need to decide the size and place special terrain features.
    
    ## Terrain Generation
    Instead of boring rectangles, create INTERESTING terrain patterns:
    - **Walls/Barriers**: Create obstacles like walls, pillars, or barriers
    - **Scattered Hazards**: Place dangerous areas strategically (not in blocks)
    - **Paths/Corridors**: Create narrow passages or choke points
    - **Central Features**: A hazardous area in the middle, or blocked pillars
    
    ## Terrain Types
    You must choose ONE type:
    - **BLOCKED**: Impassable terrain (walls, pillars, large rocks, trees). Characters cannot move through these positions.
    - **DAMAGE**: Hazardous terrain (fire, acid, spikes, lava). Characters take 1d4 damage at end of turn if standing on it.
    
    ## Design Guidelines
    - Grid size: 7x7 to 9x9 (rows x cols)
    - Place 4-8 special terrain positions (not too many, not too few)
    - Make patterns interesting: L-shapes, scattered positions, cross patterns, etc.
    - Don't block direct path from user to monster completely
    - Leave enough open space for combat movement
    - User and monster should start 4-8 squares apart (Manhattan distance)
    
    ## Examples of Good Patterns
    
    **Example 1 - Central Pillar (BLOCKED)**:
    Size: [7,7], Positions: [[3,3], [3,4], [4,3], [4,4]]
    A 2x2 blocked area in center that players must navigate around
    
    **Example 2 - Scattered Fire (DAMAGE)**:
    Size: [8,8], Positions: [[2,2], [2,5], [5,2], [5,5], [4,4]]
    Fire pits scattered across the battlefield
    
    **Example 3 - Wall Barrier (BLOCKED)**:
    Size: [7,8], Positions: [[2,3], [3,3], [4,3], [5,3]]
    A vertical wall dividing the battlefield
    
    **Example 4 - L-Shape Hazard (DAMAGE)**:
    Size: [8,7], Positions: [[3,2], [3,3], [3,4], [4,4], [5,4]]
    An L-shaped dangerous area
    
    Background story: {theme}
    
    IMPORTANT: Your response MUST be valid JSON matching this structure:
    {{
    "size": [rows, cols],
    "rectangle_position": [[r1, c1], [r2, c2], ...],
    "environment": "BLOCKED or DAMAGE",
    "environment_emoji": "Single emoji for the terrain",
    "user_position": [row, col],
    "monster_position": [row, col]
    }}
    
    The "rectangle_position" field should contain a LIST of individual positions, NOT a rectangle definition.
    Each position is [row, col]. Include 4-8 positions total.
    Choose positions that create an interesting pattern based on the background story!
    """,
    output_key='battleground',
    output_schema=BattlegroundContent,
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
)

bg_initializer = SequentialAgent(
    name='battle_ground_initializer',
    description='A pipeline to initialize a battle ground.',
    sub_agents=[theme_agent, monster_generator, bg_design_agent],
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
)

# Root routing agent that delegates to appropriate subagent
root_agent = Agent(
    name='root_agent',
    description='Root agent that routes requests to initialization or combat agents.',
    model=Gemini(
        model='gemini-2.5-flash-lite',
        retry_options=retry_config,
    ),
    instruction="""
    You are the Root Agent for a D&D combat game. Your job is to intelligently route user requests to the appropriate subagent.
    
    ## Available Subagents
    
    1. **battle_ground_initializer**: Initializes a new battle
       - Creates the background story/theme
       - Generates the monster
       - Designs the battleground
       - Use this when: User wants to start a new game, generate a scenario, or initialize combat
    
    2. **dm_agent**: Manages ongoing combat
       - Processes user combat actions (move, attack, etc.)
       - Controls monster AI
       - Manages turn-based combat
       - Applies terrain effects
       - Checks win/loss conditions
       - Use this when: User is taking actions in an active battle
    
    ## Routing Logic
    
    **Route to battle_ground_initializer when:**
    - User asks to "start", "begin", "initialize", or "create" a new battle/game
    - User requests a "new scenario", "new theme", or "generate combat"
    - The request is about setting up or generating the initial state
    - Example phrases: "Generate a D&D combat theme", "Start a new battle", "Create a new scenario"
    
    **Route to dm_agent when:**
    - User is performing a combat action: move, attack, defend, retreat
    - User asks about battle status or wants to check information
    - The request is about an ongoing battle/turn
    - Example phrases: "move north", "attack the monster", "I attack", "check status"
    
    ## Decision Process
    
    1. **Analyze** the user's request carefully
    2. **Determine** which subagent is appropriate
    3. **Delegate** to that subagent by calling it
    4. **Return** the subagent's response to the user
    
    ## Important Rules
    
    - If the request is ambiguous, default to dm_agent (assume combat is ongoing)
    - Always delegate - never try to handle requests yourself
    - Pass the user's request directly to the chosen subagent
    - Let the subagents do their specialized work
    
    ## Response Format
    
    Simply pass through whatever the chosen subagent returns. Do not add your own commentary or explanations.
    The subagent's response is the final response to the user.
    """,
    sub_agents=[bg_initializer, dm_agent],
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
)