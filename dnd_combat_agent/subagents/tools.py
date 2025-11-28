from google.adk.tools import ToolContext, FunctionTool
import random

def check_battleground_info(tool_context: ToolContext) -> dict:
    """
    Retrieves the current battleground information.

    Returns:
        dict: A dictionary containing the battleground information.
    """
    battle_ground = tool_context.state.get('battleground', {})
    return battle_ground

check_battleground_info_tool = FunctionTool(check_battleground_info)
    

def check_monster_info(tool_context: ToolContext) -> dict:
    """
    Retrieves the current monster information.

    Returns:
        dict: A dictionary containing the monster information.
    """
    monster = tool_context.state.get('monster', {})
    return monster

check_monster_info_tool = FunctionTool(check_monster_info)

def check_user_info(tool_context: ToolContext) -> dict:
    """
    Retrieves the current user information.

    Returns:
        dict: A dictionary containing the user information.
    """
    user = tool_context.state.get('user_attributes', {})
    return user

check_user_info_tool = FunctionTool(check_user_info)

def get_distance(coordinate1: list[int], coordinate2: list[int]) -> dict:
    """
    Calculates the distance between two coordinates using Manhattan distance.

    Args:
        coordinate1: [row, col]
        coordinate2: [row, col]

    Returns:
        dict: A dictionary containing a 'distance' key with the calculated distance.
    """
    distance = abs(coordinate1[0] - coordinate2[0]) + abs(coordinate1[1] - coordinate2[1])
    return {
        'distance': distance,
    }

get_distance_tool = FunctionTool(get_distance)

def check_in_range(source: str, target: str, attack_range: int, tool_context: ToolContext) -> dict:
    """
    Checks if a target is within attack range of the source.

    Args:
        source: 'user' or 'monster'
        target: 'user' or 'monster'
        attack_range: The attack range (typically 1 for melee)

    Returns:
        dict: Contains 'in_range' (bool) and 'distance' (int)
    """
    battleground = tool_context.state.get('battleground', {})
    
    if 'user' in source.lower():
        source_pos = battleground.get('user_position', [0, 0])
        target_pos = battleground.get('monster_position', [0, 0])
    else:
        source_pos = battleground.get('monster_position', [0, 0])
        target_pos = battleground.get('user_position', [0, 0])
    
    distance = abs(source_pos[0] - target_pos[0]) + abs(source_pos[1] - target_pos[1])
    
    return {
        'in_range': distance <= attack_range,
        'distance': distance,
    }

check_in_range_tool = FunctionTool(check_in_range)

def attack(source: str, target: str, tool_context: ToolContext) -> dict:
    """
    Performs an attack from source to target using D&D 5e mechanics.

    Args:
        source: 'user' or 'monster'
        target: 'user' or 'monster'

    Returns:
        dict: Contains attack results including hit/miss, damage dealt, and combat log
    """
    # Get source and target attributes
    if 'user' in source.lower():
        source_attributes = tool_context.state.get('user_attributes', {})
        target_attributes = tool_context.state.get('monster', {})
        source_name = "You"
        target_name = target_attributes.get('name', 'Monster')
    else:
        source_attributes = tool_context.state.get('monster', {})
        target_attributes = tool_context.state.get('user_attributes', {})
        source_name = source_attributes.get('name', 'Monster')
        target_name = "You"
    
    # Check if in range (melee range = 1)
    range_check = check_in_range(source, target, 1, tool_context)
    if not range_check['in_range']:
        return {
            'success': False,
            'hit': False,
            'damage': 0,
            'message': f"Attack failed! {source_name} is too far from {target_name} (distance: {range_check['distance']})",
        }
    
    # Roll d20 for attack
    attack_roll = random.randint(1, 20)
    target_ac = target_attributes.get('ac', 10)
    
    # Check if hit
    hit = attack_roll >= target_ac
    
    if not hit:
        return {
            'success': True,
            'hit': False,
            'damage': 0,
            'attack_roll': attack_roll,
            'target_ac': target_ac,
            'message': f"{source_name} attacks {target_name}! Rolled {attack_roll} vs AC {target_ac}. Miss!",
        }
    
    # Calculate damage
    damage_range = source_attributes.get('damage', [1, 6])
    damage = random.randint(damage_range[0], damage_range[1])
    
    # Update target HP
    current_hp = target_attributes.get('hp', 0)
    new_hp = max(0, current_hp - damage)
    
    # Update state - replace entire dict to ensure change is detected
    if 'user' in target.lower():
        user_attrs_copy = dict(target_attributes)
        user_attrs_copy['hp'] = new_hp
        tool_context.state['user_attributes'] = user_attrs_copy
    else:
        monster_copy = dict(target_attributes)
        monster_copy['hp'] = new_hp
        tool_context.state['monster'] = monster_copy
    
    critical = attack_roll == 20
    message = f"{source_name} attacks {target_name}! Rolled {attack_roll} vs AC {target_ac}. "
    if critical:
        message += f"CRITICAL HIT! Deals {damage} damage! "
    else:
        message += f"Hit! Deals {damage} damage! "
    message += f"{target_name}'s HP: {current_hp} → {new_hp}"
    
    return {
        'success': True,
        'hit': True,
        'damage': damage,
        'attack_roll': attack_roll,
        'target_ac': target_ac,
        'critical': critical,
        'new_hp': new_hp,
        'message': message,
    }

attack_tool = FunctionTool(attack)

def move_character(character: str, direction: str, tool_context: ToolContext) -> dict:
    """
    Moves a character on the battlefield.

    Args:
        character: 'user' or 'monster'
        direction: 'north', 'south', 'east', 'west', 'northeast', 'northwest', 'southeast', 'southwest'

    Returns:
        dict: Contains success status and message
    """
    battleground = tool_context.state.get('battleground', {})
    
    # Get character attributes and position
    if 'user' in character.lower():
        char_attributes = tool_context.state.get('user_attributes', {})
        current_pos = battleground.get('user_position', [0, 0])
        char_name = "You"
    else:
        char_attributes = tool_context.state.get('monster', {})
        current_pos = battleground.get('monster_position', [0, 0])
        char_name = char_attributes.get('name', 'Monster')
    
    # Calculate new position based on direction
    direction_map = {
        'north': [-1, 0],
        'south': [1, 0],
        'east': [0, 1],
        'west': [0, -1],
        'northeast': [-1, 1],
        'northwest': [-1, -1],
        'southeast': [1, 1],
        'southwest': [1, -1],
    }
    
    if direction.lower() not in direction_map:
        return {
            'success': False,
            'message': f"Invalid direction: {direction}. Use: north, south, east, west, northeast, northwest, southeast, southwest",
        }
    
    delta = direction_map[direction.lower()]
    new_pos = [current_pos[0] + delta[0], current_pos[1] + delta[1]]
    
    # Check bounds
    size = battleground.get('size', [5, 5])
    if new_pos[0] < 0 or new_pos[0] >= size[0] or new_pos[1] < 0 or new_pos[1] >= size[1]:
        return {
            'success': False,
            'message': f"{char_name} cannot move {direction} - out of bounds!",
        }
    
    # Check speed (movement distance)
    distance = abs(delta[0]) + abs(delta[1])
    speed = char_attributes.get('speed', 1)
    
    if distance > speed:
        return {
            'success': False,
            'message': f"{char_name} cannot move that far! Speed: {speed}, Distance: {distance}",
        }
    
    # Update position - replace the entire battleground to ensure change is detected
    battleground_copy = dict(battleground)  # Shallow copy is fine for top-level dict
    if 'user' in character.lower():
        battleground_copy['user_position'] = new_pos
    else:
        battleground_copy['monster_position'] = new_pos
    
    tool_context.state['battleground'] = battleground_copy
    
    return {
        'success': True,
        'old_position': current_pos,
        'new_position': new_pos,
        'message': f"{char_name} moves {direction} from {current_pos} to {new_pos}",
    }

move_character_tool = FunctionTool(move_character)

def apply_terrain_effects(character: str, tool_context: ToolContext) -> dict:
    """
    Applies terrain effects to a character based on their position.

    Args:
        character: 'user' or 'monster'

    Returns:
        dict: Contains effects applied and message
    """
    battleground = tool_context.state.get('battleground', {})
    
    # Get character position
    if 'user' in character.lower():
        char_pos = battleground.get('user_position', [0, 0])
        char_attributes = tool_context.state.get('user_attributes', {})
        char_name = "You"
    else:
        char_pos = battleground.get('monster_position', [0, 0])
        char_attributes = tool_context.state.get('monster', {})
        char_name = char_attributes.get('name', 'Monster')
    
    # Check if in special terrain
    rect_pos = battleground.get('rectangle_position', [[0, 0], [0, 0]])
    top_left = rect_pos[0]
    bottom_right = rect_pos[1]
    
    in_terrain = (top_left[0] <= char_pos[0] <= bottom_right[0] and 
                  top_left[1] <= char_pos[1] <= bottom_right[1])
    
    if not in_terrain:
        return {
            'in_terrain': False,
            'effects': [],
            'message': f"{char_name} is on normal ground - no terrain effects",
        }
    
    environment = battleground.get('environment', '')
    environment_emoji = battleground.get('environment_emoji', '')
    effects = []
    
    if environment == 'DAMAGE':
        damage = random.randint(1, 4)
        current_hp = char_attributes.get('hp', 0)
        new_hp = max(0, current_hp - damage)
        
        # Update state - replace entire dict to ensure change is detected
        if 'user' in character.lower():
            user_attrs_copy = dict(char_attributes)
            user_attrs_copy['hp'] = new_hp
            tool_context.state['user_attributes'] = user_attrs_copy
        else:
            monster_copy = dict(char_attributes)
            monster_copy['hp'] = new_hp
            tool_context.state['monster'] = monster_copy
        
        effects.append(f"DAMAGE: {damage} damage from terrain")
        message = f"{char_name} takes {damage} damage from {environment_emoji} terrain! HP: {current_hp} → {new_hp}"
    
    elif environment == 'SLOW':
        effects.append("SLOW: Movement reduced")
        message = f"{char_name} is slowed by {environment_emoji} terrain! Movement may be hindered next turn"
    
    else:
        message = f"{char_name} is in special terrain {environment_emoji}"
    
    return {
        'in_terrain': True,
        'environment': environment,
        'effects': effects,
        'message': message,
    }
    
apply_terrain_effects_tool = FunctionTool(apply_terrain_effects)

def check_combat_status(tool_context: ToolContext) -> dict:
    """
    Checks if combat should continue or has ended.

    Returns:
        dict: Contains battle status (ongoing, user_won, monster_won) and message
    """
    user_attributes = tool_context.state.get('user_attributes', {})
    monster = tool_context.state.get('monster', {})
    
    user_hp = user_attributes.get('hp', 0)
    monster_hp = monster.get('hp', 0)
    monster_name = monster.get('name', 'Monster')
    
    if user_hp <= 0:
        return {
            'status': 'monster_won',
            'winner': 'monster',
            'message': f"💀 You have been defeated by {monster_name}! Game Over!",
        }
    
    if monster_hp <= 0:
        return {
            'status': 'user_won',
            'winner': 'user',
            'message': f"🎉 Victory! You have defeated {monster_name}!",
        }
    
    return {
        'status': 'ongoing',
        'winner': None,
        'user_hp': user_hp,
        'monster_hp': monster_hp,
        'message': f"Battle continues! Your HP: {user_hp}, {monster_name}'s HP: {monster_hp}",
    }

check_combat_status_tool = FunctionTool(check_combat_status)

def get_available_actions(character: str, tool_context: ToolContext) -> dict:
    """
    Gets available actions for a character.

    Args:
        character: 'user' or 'monster'

    Returns:
        dict: Contains list of available actions
    """
    battleground = tool_context.state.get('battleground', {})
    
    if 'user' in character.lower():
        char_pos = battleground.get('user_position', [0, 0])
        char_attributes = tool_context.state.get('user_attributes', {})
        target_pos = battleground.get('monster_position', [0, 0])
    else:
        char_pos = battleground.get('monster_position', [0, 0])
        char_attributes = tool_context.state.get('monster', {})
        target_pos = battleground.get('user_position', [0, 0])
    
    speed = char_attributes.get('speed', 1)
    size = battleground.get('size', [5, 5])
    distance_to_target = abs(char_pos[0] - target_pos[0]) + abs(char_pos[1] - target_pos[1])
    
    actions = []
    
    # Check possible movements
    directions = ['north', 'south', 'east', 'west']
    if speed >= 2:
        directions.extend(['northeast', 'northwest', 'southeast', 'southwest'])
    
    available_moves = []
    for direction in directions:
        direction_map = {
            'north': [-1, 0], 'south': [1, 0], 'east': [0, 1], 'west': [0, -1],
            'northeast': [-1, 1], 'northwest': [-1, -1], 
            'southeast': [1, 1], 'southwest': [1, -1],
        }
        delta = direction_map[direction]
        new_pos = [char_pos[0] + delta[0], char_pos[1] + delta[1]]
        
        if 0 <= new_pos[0] < size[0] and 0 <= new_pos[1] < size[1]:
            available_moves.append(direction)
    
    actions.append({
        'action': 'move',
        'options': available_moves,
    })
    
    # Check if can attack
    if distance_to_target <= 1:
        actions.append({
            'action': 'attack',
            'in_range': True,
        })
    else:
        actions.append({
            'action': 'attack',
            'in_range': False,
            'distance': distance_to_target,
        })
    
    return {
        'actions': actions,
        'distance_to_target': distance_to_target,
    }

get_available_actions_tool = FunctionTool(get_available_actions)