from google.genai import types
import random

async def call_agent(runner, user_id, session_id, user_input, session_service):
    """
    Calls an agent and returns both the response and the final session state.
    
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
        
        # After all events have been processed, get the fresh session state
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
    Prints the battleground to the terminal using emoji and special characters.
    
    Args:
        size: [rows, cols]
        rectangle_position: [[r1, c1], [r2, c2]] (Top-Left, Bottom-Right)
        environment_emoji: environment emoji
        user_position: [r, c]
        monster_position: [r, c]
        monster_emoji: monster emoji
    """
    rows, cols = size
    # Initialize grid with dots for normal ground
    grid = [[' .' for _ in range(cols)] for _ in range(rows)]
    
    # Unpack special area coordinates
    if rectangle_position and len(rectangle_position) == 2:
        top_left = rectangle_position[0]
        bottom_right = rectangle_position[1]
        
        # Fill special area
        # Ensure indices are within bounds
        r_start = max(0, top_left[0])
        r_end = min(rows - 1, bottom_right[0])
        c_start = max(0, top_left[1])
        c_end = min(cols - 1, bottom_right[1])

        for r in range(r_start, r_end + 1):
            for c in range(c_start, c_end + 1):
                grid[r][c] = environment_emoji

    # Place Entities (Last so they appear on top of environment)
    # Monster
    if 0 <= monster_position[0] < rows and 0 <= monster_position[1] < cols:
        grid[monster_position[0]][monster_position[1]] = monster_emoji
        
    # User 🧙‍♂️
    if 0 <= user_position[0] < rows and 0 <= user_position[1] < cols:
        grid[user_position[0]][user_position[1]] = '🧙'

    # Print to terminal with coordinate frame
    header_nums = "  " + " ".join([str(i) for i in range(cols)])
    print("\n " + header_nums)
    print("  +" + "--" * cols + "+")
    for r in range(rows):
        row_str = "".join(grid[r])
        print(f" {r}|{row_str}|")
    print("  +" + "--" * cols + "+")

def create_character(_class: str):
    if _class == 'fighter':
        user_attributes = {
            'hp': random.randint(9, 17),
            'ac': 13,
            'speed': 2,
            'damage': [4, 7],
        }
        return user_attributes
    else:
        print('Error in create_character: Unsupported class!')

def display_combat_state(user_attributes: dict, monster: dict, battleground: dict):
    """
    Displays the current combat state including HP, positions, and terrain info.
    
    Args:
        user_attributes: User's attributes dictionary
        monster: Monster's attributes dictionary  
        battleground: Battleground state dictionary
    """
    print("\n" + "="*50)
    print("⚔️  COMBAT STATUS")
    print("="*50)
    
    # User status
    user_hp = user_attributes.get('hp', 0)
    user_ac = user_attributes.get('ac', 0)
    user_pos = battleground.get('user_position', [0, 0])
    print(f"🧙 YOU        | HP: {user_hp:>3} | AC: {user_ac:>2} | Position: {user_pos}")
    
    # Monster status
    monster_hp = monster.get('hp', 0)
    monster_ac = monster.get('ac', 0)
    monster_name = monster.get('name', 'Monster')
    monster_emoji = monster.get('monster_emoji', '👾')
    monster_pos = battleground.get('monster_position', [0, 0])
    print(f"{monster_emoji} {monster_name:<10} | HP: {monster_hp:>3} | AC: {monster_ac:>2} | Position: {monster_pos}")
    
    # Distance
    distance = abs(user_pos[0] - monster_pos[0]) + abs(user_pos[1] - monster_pos[1])
    print(f"\n📏 Distance: {distance} squares")
    
    # Terrain info
    environment = battleground.get('environment', 'None')
    environment_emoji = battleground.get('environment_emoji', '')
    if environment:
        print(f"🌍 Special Terrain: {environment_emoji} {environment}")
    
    print("="*50 + "\n")

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
