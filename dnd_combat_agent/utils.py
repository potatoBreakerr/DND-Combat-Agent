"""
D&D Combat Agent - Utility Functions

Provides helper functions for:
- Agent communication and session management
- Battleground grid display
- Character creation
- Combat status display
"""

from google.genai import types
import random

async def call_agent(runner, user_id, session_id, user_input, session_service):
    """
    Calls an agent and returns both the response and updated session state.
    
    Args:
        runner: Agent runner instance
        user_id: User identifier
        session_id: Session identifier  
        user_input: User's command or message
        session_service: Session state manager
    
    Returns:
        tuple: (response_list, final_state_dict)
    """
    new_message = types.Content(
        role='user', parts=[types.Part(text=user_input)]
    )
    try:
        response = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response.append(event.content.parts[0].text)
        
        # After all events, get the fresh session state
        updated_session = await session_service.get_session(
            user_id=user_id,
            app_name=runner.app_name,
            session_id=session_id,
        )
        
        return response, updated_session.state
    except Exception as e:
        print(f'Error due to agent call: {e}')
        import traceback
        traceback.print_exc()
        return [], None
def show_battle_ground(size: list[int], rectangle_position: list[list[int]], environment_emoji: str, user_position: list[int], monster_position: list[int], monster_emoji: str):
    """
    Prints the battleground to the terminal using emoji with 2-char width.
    
    Args:
        size: [rows, cols]
        rectangle_position: List of [row, col] positions with special terrain
        environment_emoji: environment emoji
        user_position: [r, c]
        monster_position: [r, c]
        monster_emoji: monster emoji
    """
    rows, cols = size
    # Initialize grid with dots for normal ground
    grid = [[' .' for _ in range(cols)] for _ in range(rows)]
    
    # Fill special terrain positions (now supports list of positions)
    if rectangle_position:
        # Check if it's a list of positions or old rectangle format
        if len(rectangle_position) == 2 and isinstance(rectangle_position[0], list) and len(rectangle_position[0]) == 2 and len(rectangle_position) == 2:
            # Old rectangle format: [[r1, c1], [r2, c2]]
            # Check if it looks like a rectangle (second position is bottom-right)
            if rectangle_position[1][0] >= rectangle_position[0][0] and rectangle_position[1][1] >= rectangle_position[0][1]:
                # Treat as rectangle
                top_left = rectangle_position[0]
                bottom_right = rectangle_position[1]
                
                r_start = max(0, top_left[0])
                r_end = min(rows - 1, bottom_right[0])
                c_start = max(0, top_left[1])
                c_end = min(cols - 1, bottom_right[1])

                for r in range(r_start, r_end + 1):
                    for c in range(c_start, c_end + 1):
                        grid[r][c] = environment_emoji
            else:
                # Treat as list of two positions
                for pos in rectangle_position:
                    r, c = pos
                    if 0 <= r < rows and 0 <= c < cols:
                        grid[r][c] = environment_emoji
        else:
            # New format: list of individual positions
            for pos in rectangle_position:
                if isinstance(pos, list) and len(pos) == 2:
                    r, c = pos
                    if 0 <= r < rows and 0 <= c < cols:
                        grid[r][c] = environment_emoji

    # Place Monster (overwrites terrain)
    if 0 <= monster_position[0] < rows and 0 <= monster_position[1] < cols:
        grid[monster_position[0]][monster_position[1]] = monster_emoji
        
    # Place User (overwrites everything)
    if 0 <= user_position[0] < rows and 0 <= user_position[1] < cols:
        grid[user_position[0]][user_position[1]] = '🧙'

    # Print to terminal with coordinate frame
    header_nums = "  " + " ".join([str(i) for i in range(cols)])
    print("\n " + header_nums)
    print("  +" + "--" * cols + "+")
    for r in range(rows):
        row_str = "".join(grid[r])
        print(f" {r}|{row_str}|")
    print("  +" + "--" * cols + "+\n")


def create_character(_class: str):
    """
    Creates character attributes based on class.
    
    Args:
        _class: 'fighter' or 'wizard'
    
    Returns:
        dict: Character attributes including hp, ac, speed, damage, and spell slots for wizard
    """
    if _class.lower() == 'fighter':
        hp = random.randint(15, 25)
        user_attributes = {
            'class': 'fighter',
            'hp': hp,
            'max_hp': hp,  # Store max HP
            'ac': 13,
            'speed': 2,
            'damage': [7, 10],
        }
    elif _class.lower() == 'wizard':
        hp = random.randint(10, 18)
        user_attributes = {
            'class': 'wizard',
            'hp': hp,
            'max_hp': hp,  # Store max HP
            'ac': 11,  # Lower AC (no armor)
            'speed': 2,
            'damage': [4, 7],  # Lower melee damage
            'spell_slots': {
                'level_1': 3,  # 3 level 1 spell slots
                'level_2': 2,  # 2 level 2 spell slots
            },
            'max_spell_slots': {  # Store max for display
                'level_1': 3,
                'level_2': 2,
            },
            'spells_known': ['magic_missile', 'fireball', 'heal']
        }
    else:
        # Default to fighter
        hp = random.randint(15, 25)
        user_attributes = {
            'class': 'fighter',
            'hp': hp,
            'max_hp': hp,
            'ac': 13,
            'speed': 2,
            'damage': [7, 10],
        }
    
    return user_attributes

def display_combat_state(user_attributes: dict, monster: dict, battleground: dict):
    """
    Displays the current combat state including HP, positions, spell slots, and terrain info.
    """
    # Get positions
    user_pos = battleground.get('user_position', [0, 0])
    monster_pos = battleground.get('monster_position', [0, 0])
    
    # Calculate distance
    distance = abs(user_pos[0] - monster_pos[0]) + abs(user_pos[1] - monster_pos[1])
    
    # Get terrain info
    environment = battleground.get('environment', 'Normal')
    environment_emoji = battleground.get('environment_emoji', '')
    
    # Get user class
    user_class = user_attributes.get('class', 'fighter')
    
    print()
    print("-" * 60)
    print("COMBAT STATUS")
    print("-" * 60)
    
    # User status with max HP
    user_hp = user_attributes.get('hp', 0)
    user_max_hp = user_attributes.get('max_hp', user_hp)
    print(f"🧙 YOU ({user_class.upper()})")
    print(f"   HP: {user_hp}/{user_max_hp} | AC: {user_attributes.get('ac', 0)} | Position: {user_pos}")
    
    # Show spell slots for wizard
    if user_class == 'wizard':
        spell_slots = user_attributes.get('spell_slots', {})
        max_slots = user_attributes.get('max_spell_slots', spell_slots)
        lv1 = spell_slots.get('level_1', 0)
        lv1_max = max_slots.get('level_1', 3)
        lv2 = spell_slots.get('level_2', 0)
        lv2_max = max_slots.get('level_2', 2)
        print(f"   Spell Slots: Lv1: {lv1}/{lv1_max} | Lv2: {lv2}/{lv2_max}")
    
    print()
    
    # Monster status
    monster_name = monster.get('name', 'Monster')
    monster_emoji = monster.get('monster_emoji', '👾')
    print(f"{monster_emoji} {monster_name.upper()}")
    print(f"   HP: {monster.get('hp', 0)} | AC: {monster.get('ac', 0)} | Position: {monster_pos}")
    
    print()
    print(f"Distance: {distance} squares | Terrain: {environment_emoji} {environment}")
    print("-" * 60)
    print()


def roll_dice(num_dice: int, dice_sides: int) -> int:
    """
    Rolls dice and returns the total.
    
    Args:
        num_dice: Number of dice to roll
        dice_sides: Number of sides on each die
        
    Returns:
        int: Total of all dice rolled
    """
    return sum(random.randint(1, dice_sides) for _ in range(num_dice))
