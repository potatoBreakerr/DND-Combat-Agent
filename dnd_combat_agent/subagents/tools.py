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
    Rolls a d20 for attack, compares to AC, rolls damage if hit.
    For user attacks, checks and marks action as used.
    
    Args:
        source: 'user' or 'monster'
        target: 'user' or 'monster'
    
    Returns:
        dict: Attack result with hit/miss, damage, and updated HP
    """
    # For user attacks, check if action is available
    if 'user' in source.lower():
        tracker = tool_context.state.get('turn_tracker', {})
        action_used = tracker.get('action_used', False)
        
        if action_used:
            return {
                'success': False,
                'message': 'You have already used your action this turn!',
            }
    
    # Get source attributes
    if 'user' in source.lower():
        source_attributes = tool_context.state.get('user_attributes', {})
        source_name = "You"
    else:
        source_attributes = tool_context.state.get('monster', {})
        source_name = source_attributes.get('name', 'Monster')
    
    # Get target attributes
    if 'user' in target.lower():
        target_attributes = tool_context.state.get('user_attributes', {})
        target_name = "You"
    else:
        target_attributes = tool_context.state.get('monster', {})
        target_name = target_attributes.get('name', 'Monster')
    
    # Get attack stats
    damage_range = source_attributes.get('damage', [1, 6])
    
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
    
    damage = 0
    new_hp = target_attributes.get('hp', 0)
    current_hp = target_attributes.get('hp', 0)

    if hit:
        # Calculate damage
        damage = random.randint(damage_range[0], damage_range[1])
        
        # Update target HP
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
    
    if hit:
        message += f"Hit! Deals {damage} damage! {target_name}'s HP: {current_hp} → {new_hp}"
    else:
        message += "Miss!"
    
    # Mark action as used for user attacks
    if 'user' in source.lower():
        tracker_copy = dict(tool_context.state.get('turn_tracker', {}))
        tracker_copy['action_used'] = True
        tool_context.state['turn_tracker'] = tracker_copy
    
    return {
        'success': True,
        'hit': hit,
        'damage': damage if hit else 0,
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
    
    # Check if target position is BLOCKED terrain
    environment = battleground.get('environment', '')
    if environment == 'BLOCKED':
        terrain_positions = battleground.get('rectangle_position', [])
        # Check both old rectangle format and new list format
        is_blocked = False
        
        if terrain_positions:
            # Check if new_pos is in blocked terrain
            if len(terrain_positions) == 2 and isinstance(terrain_positions[0], list):
                # Could be old rectangle format or new list format
                if (len(terrain_positions) == 2 and 
                    terrain_positions[1][0] >= terrain_positions[0][0] and 
                    terrain_positions[1][1] >= terrain_positions[0][1]):
                    # Rectangle format
                    top_left = terrain_positions[0]
                    bottom_right = terrain_positions[1]
                    if (top_left[0] <= new_pos[0] <= bottom_right[0] and 
                        top_left[1] <= new_pos[1] <= bottom_right[1]):
                        is_blocked = True
                else:
                    # List of positions
                    if new_pos in terrain_positions:
                        is_blocked = True
            else:
                # New list format
                if new_pos in terrain_positions:
                    is_blocked = True
        
        if is_blocked:
            return {
                'success': False,
                'message': f"{char_name} cannot move there - blocked by terrain!",
            }
    
    # Check speed (movement distance)
    distance = abs(delta[0]) + abs(delta[1])
    speed = char_attributes.get('speed', 1)
    
    # For user movement, check turn tracker
    if 'user' in character.lower():
        tracker = tool_context.state.get('turn_tracker', {})
        movement_used = tracker.get('movement_used', 0)
        movement_remaining = speed - movement_used
        
        if distance > movement_remaining:
            return {
                'success': False,
                'message': f"{char_name} cannot move {distance} squares! Only {movement_remaining} movement remaining this turn (used {movement_used}/{speed})",
            }
    else:
        # Monster movement - just check against speed
        if distance > speed:
            return {
                'success': False,
                'message': f"{char_name} cannot move that far! Speed: {speed}, Distance: {distance}",
            }
    
    # Update position - replace the entire battleground to ensure change is detected
    battleground_copy = dict(battleground)  # Shallow copy is fine for top-level dict
    if 'user' in character.lower():
        battleground_copy['user_position'] = new_pos
        
        # Update movement tracker for user
        tracker_copy = dict(tool_context.state.get('turn_tracker', {}))
        tracker_copy['movement_used'] = tracker_copy.get('movement_used', 0) + distance
        tool_context.state['turn_tracker'] = tracker_copy
    else:
        battleground_copy['monster_position'] = new_pos
    
    tool_context.state['battleground'] = battleground_copy
    
    return {
        'success': True,
        'old_position': current_pos,
        'new_position': new_pos,
        'distance_moved': distance,
        'message': f"{char_name} moves {direction} from {current_pos} to {new_pos}",
    }

move_character_tool = FunctionTool(move_character)

def apply_terrain_effects(character: str, tool_context: ToolContext) -> dict:
    """
    Applies terrain effects to a character if they're standing on special terrain.
    Only applies to DAMAGE terrain (e.g., fire, lava, acid).
    BLOCKED terrain prevents movement but doesn't deal damage.
    
    Args:
        character: 'user' or 'monster'
    
    Returns:
        dict: Effects applied and updated HP if any
    """
    battleground = tool_context.state.get('battleground', {})
    environment = battleground.get('environment', '')
    
    # Get character position
    if 'user' in character.lower():
        char_pos = battleground.get('user_position', [0, 0])
        char_attributes = tool_context.state.get('user_attributes', {})
        char_name = "You"
    else:
        char_pos = battleground.get('monster_position', [0, 0])
        char_attributes = tool_context.state.get('monster', {})
        char_name = char_attributes.get('name', 'Monster')
    
    # Check if character is on special terrain
    terrain_positions = battleground.get('rectangle_position', [])
    is_on_terrain = False
    
    if terrain_positions:
        # Check both old rectangle format and new list format
        if len(terrain_positions) == 2 and isinstance(terrain_positions[0], list):
            # Could be rectangle or list
            if (terrain_positions[1][0] >= terrain_positions[0][0] and 
                terrain_positions[1][1] >= terrain_positions[0][1]):
                # Rectangle format
                top_left = terrain_positions[0]
                bottom_right = terrain_positions[1]
                if (top_left[0] <= char_pos[0] <= bottom_right[0] and 
                    top_left[1] <= char_pos[1] <= bottom_right[1]):
                    is_on_terrain = True
            else:
                # List of positions
                if char_pos in terrain_positions:
                    is_on_terrain = True
        else:
            # New list format
            if char_pos in terrain_positions:
                is_on_terrain = True
    
    if not is_on_terrain:
        return {
            'in_terrain': False,
            'effects': [],
            'message': f'{char_name} is on normal ground - no terrain effects'
        }
    
    # Apply effects based on terrain type
    effects = []
    environment_emoji = battleground.get('environment_emoji', '')
    
    if environment == 'BLOCKED':
        # BLOCKED terrain doesn't deal damage, just blocks movement
        return {
            'in_terrain': True,
            'environment': 'BLOCKED',
            'effects': [],
            'message': f'{char_name} is on blocked terrain (no damage)'
        }
    
    elif environment == 'DAMAGE':
        # Roll 1d4 damage
        damage = random.randint(1, 4)
        current_hp = char_attributes.get('hp', 0)
        new_hp = max(0, current_hp - damage)
        
        # Update HP - replace entire dict to ensure change is detected
        if 'user' in character.lower():
            user_attrs_copy = dict(char_attributes)
            user_attrs_copy['hp'] = new_hp
            tool_context.state['user_attributes'] = user_attrs_copy
        else:
            monster_copy = dict(char_attributes)
            monster_copy['hp'] = new_hp
            tool_context.state['monster'] = monster_copy
        
        effects.append(f'DAMAGE: {damage} damage from terrain')
        
        return {
            'in_terrain': True,
            'environment': 'DAMAGE',
            'effects': effects,
            'message': f'{char_name} takes {damage} damage from {environment_emoji} terrain! HP: {current_hp} → {new_hp}'
        }
    
    else:
        return {
            'in_terrain': True,
            'environment': environment,
            'effects': [],
            'message': f'{char_name} is on {environment} terrain'
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


# ============================================================
# TURN TRACKING TOOLS - Action Economy System
# ============================================================

def reset_turn(tool_context: ToolContext) -> dict:
    """
    Reset action tracking at the start of the user's turn.
    Clears movement used, action used, and bonus action used.
    
    Returns:
        dict: Confirmation message
    """
    # Initialize turn tracker if it doesn't exist
    if 'turn_tracker' not in tool_context.state:
        tool_context.state['turn_tracker'] = {}
    
    # Reset all action tracking
    tracker_copy = dict(tool_context.state.get('turn_tracker', {}))
    tracker_copy['current_turn'] = 'user'
    tracker_copy['movement_used'] = 0
    tracker_copy['action_used'] = False
    tracker_copy['bonus_action_used'] = False
    
    tool_context.state['turn_tracker'] = tracker_copy
    
    return {
        'success': True,
        'message': 'User turn started. All actions reset.',
        'turn_tracker': tracker_copy
    }

reset_turn_tool = FunctionTool(reset_turn)


def check_turn_status(tool_context: ToolContext) -> dict:
    """
    Check what actions are still available in the current turn.
    
    Returns:
        dict: Available movement, action, and bonus action status
    """
    tracker = tool_context.state.get('turn_tracker', {})
    user_attributes = tool_context.state.get('user_attributes', {})
    
    movement_used = tracker.get('movement_used', 0)
    action_used = tracker.get('action_used', False)
    bonus_action_used = tracker.get('bonus_action_used', False)
    
    max_movement = user_attributes.get('speed', 2)
    movement_remaining = max(0, max_movement - movement_used)
    
    return {
        'current_turn': tracker.get('current_turn', 'user'),
        'movement_remaining': movement_remaining,
        'movement_used': movement_used,
        'max_movement': max_movement,
        'action_available': not action_used,
        'bonus_action_available': not bonus_action_used,
        'message': f"Movement: {movement_remaining}/{max_movement} | Action: {'Available' if not action_used else 'Used'} | Bonus: {'Available' if not bonus_action_used else 'Used'}"
    }

check_turn_status_tool = FunctionTool(check_turn_status)


def end_user_turn(tool_context: ToolContext) -> dict:
    """
    Mark the user's turn as complete and switch to monster turn.
    This indicates the monster should now take its full turn.
    
    Returns:
        dict: Confirmation that turn has ended
    """
    tracker_copy = dict(tool_context.state.get('turn_tracker', {}))
    tracker_copy['current_turn'] = 'monster'
    
    tool_context.state['turn_tracker'] = tracker_copy
    
    return {
        'success': True,
        'turn_switched': True,
        'message': 'User turn ended. Monster turn begins.'
    }

end_user_turn_tool = FunctionTool(end_user_turn)


# ============================================================
# SPELL CASTING TOOLS
# ============================================================

def cast_spell(spell_name: str, target: str, tool_context: ToolContext) -> dict:
    """
    Cast a spell. Available spells: magic_missile (level 1), fireball (level 2), heal (level 1 bonus action).
    
    Args:
        spell_name: Name of spell ('magic_missile', 'fireball', 'heal')
        target: 'user' or 'monster' (heal targets user, damage spells target monster)
    
    Returns:
        dict: Spell result including damage/healing and spell slot usage
    """
    user_attributes = tool_context.state.get('user_attributes', {})
    
    # Check if user is a wizard
    if user_attributes.get('class') != 'wizard':
        return {
            'success': False,
            'message': 'Only wizards can cast spells!'
        }
    
    spell_name = spell_name.lower()
    
    # Check if spell is known
    spells_known = user_attributes.get('spells_known', [])
    if spell_name not in spells_known:
        return {
            'success': False,
            'message': f'Spell "{spell_name}" is not known!'
        }
    
    # Define spell properties
    spell_data = {
        'magic_missile': {
            'level': 1,
            'type': 'damage',
            'damage': [6, 10],  # 2d4+2 ≈ 6-10 damage
            'action_type': 'action',
            'description': 'Three glowing darts of magical force'
        },
        'fireball': {
            'level': 2,
            'type': 'damage',
            'damage': [12, 24],  # 8d6 ≈ 12-24 damage
            'action_type': 'action',
            'description': 'A bright streak flashes to a point and blossoms into an explosion of flame'
        },
        'heal': {
            'level': 1,
            'type': 'heal',
            'healing': [6, 10],  # 2d4+2
            'action_type': 'bonus_action',
            'description': 'Healing energy radiates from your hands'
        }
    }
    
    if spell_name not in spell_data:
        return {
            'success': False,
            'message': f'Unknown spell: {spell_name}'
        }
    
    spell = spell_data[spell_name]
    spell_level = spell['level']
    
    # Check spell slots
    spell_slots = user_attributes.get('spell_slots', {})
    slot_key = f'level_{spell_level}'
    slots_remaining = spell_slots.get(slot_key, 0)
    
    if slots_remaining <= 0:
        return {
            'success': False,
            'message': f'No level {spell_level} spell slots remaining!'
        }
    
    # Check action economy
    tracker = tool_context.state.get('turn_tracker', {})
    
    if spell['action_type'] == 'action':
        if tracker.get('action_used', False):
            return {
                'success': False,
                'message': 'You have already used your action this turn!'
            }
    elif spell['action_type'] == 'bonus_action':
        if tracker.get('bonus_action_used', False):
            return {
                'success': False,
                'message': 'You have already used your bonus action this turn!'
            }
    
    # Cast the spell!
    result_message = ""
    
    if spell['type'] == 'damage':
        # Damage spell
        monster = tool_context.state.get('monster', {})
        damage = random.randint(spell['damage'][0], spell['damage'][1])
        current_hp = monster.get('hp', 0)
        new_hp = max(0, current_hp - damage)
        
        # Update monster HP
        monster_copy = dict(monster)
        monster_copy['hp'] = new_hp
        tool_context.state['monster'] = monster_copy
        
        monster_name = monster.get('name', 'Monster')
        result_message = f"You cast {spell_name.replace('_', ' ').title()}! {spell['description']}. Deals {damage} damage to {monster_name}! HP: {current_hp} → {new_hp}"
        
    elif spell['type'] == 'heal':
        # Healing spell
        healing = random.randint(spell['healing'][0], spell['healing'][1])
        current_hp = user_attributes.get('hp', 0)
        max_hp = user_attributes.get('max_hp', current_hp + 10)  # Estimate max HP
        new_hp = min(max_hp, current_hp + healing)
        actual_healing = new_hp - current_hp
        
        # Update user HP
        user_attrs_copy = dict(user_attributes)
        user_attrs_copy['hp'] = new_hp
        tool_context.state['user_attributes'] = user_attrs_copy
        
        result_message = f"You cast Heal! {spell['description']}.  You heal {actual_healing} HP! HP: {current_hp} → {new_hp}"
    
    # Use spell slot
    user_attrs_copy = dict(tool_context.state.get('user_attributes', {}))
    spell_slots_copy = dict(user_attrs_copy.get('spell_slots', {}))
    spell_slots_copy[slot_key] = slots_remaining - 1
    user_attrs_copy['spell_slots'] = spell_slots_copy
    tool_context.state['user_attributes'] = user_attrs_copy
    
    # Mark action/bonus action as used
    tracker_copy = dict(tracker)
    if spell['action_type'] == 'action':
        tracker_copy['action_used'] = True
    elif spell['action_type'] == 'bonus_action':
        tracker_copy['bonus_action_used'] = True
    tool_context.state['turn_tracker'] = tracker_copy
    
    return {
        'success': True,
        'spell_name': spell_name,
        'spell_level': spell_level,
        'action_type': spell['action_type'],
        'slots_remaining': slots_remaining - 1,
        'message': result_message
    }

cast_spell_tool = FunctionTool(cast_spell)


def check_spell_slots(tool_context: ToolContext) -> dict:
    """
    Check remaining spell slots for wizard.
    
    Returns:
        dict: Spell slots remaining
    """
    user_attributes = tool_context.state.get('user_attributes', {})
    
    if user_attributes.get('class') != 'wizard':
        return {
            'is_wizard': False,
            'message': 'Not a wizard - no spell slots'
        }
    
    spell_slots = user_attributes.get('spell_slots', {})
    spells_known = user_attributes.get('spells_known', [])
    
    return {
        'is_wizard': True,
        'spell_slots': spell_slots,
        'spells_known': spells_known,
        'message': f"Spell slots: Level 1: {spell_slots.get('level_1', 0)}, Level 2: {spell_slots.get('level_2', 0)}"
    }

check_spell_slots_tool = FunctionTool(check_spell_slots)