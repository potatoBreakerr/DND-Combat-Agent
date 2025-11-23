from google.genai import types
import random

async def call_agent(runner, user_id, session_id, user_input):
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
        return response
    except Exception as e:
        print(f'Error due to agent call: {e}')

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
