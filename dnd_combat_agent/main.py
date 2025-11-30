"""
D&D Combat Agent - Main Entry Point

This is the main game loop for a D&D-style turn-based combat simulator.
Players can choose between Fighter and Wizard classes and battle against
AI-controlled monsters in tactical grid-based combat.

Features:
- Turn-based action economy (movement, action, bonus action)
- Spell casting system for wizards
- Terrain effects (BLOCKED/DAMAGE)
- AI-controlled monsters
"""

import asyncio
import uuid

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from subagents.subagents import root_agent
from utils import call_agent, show_battle_ground, create_character, display_combat_state

load_dotenv()


async def main():
    """
    Main game function that handles:
    1. Class selection (Fighter/Wizard)
    2. Character creation
    3. Battle scenario generation
    4. Turn-based combat loop
    """
    
    # ===== WELCOME AND CLASS SELECTION =====
    print("\n" + "="*70)
    print("🎮 D&D COMBAT AGENT")
    print("="*70)
    
    print("\n🎲 Welcome to the D&D Combat Arena!")
    print("Let's start by choosing your character class...\n")
    
    # Display available classes
    print("Available classes:")
    print("  1. Fighter - High HP, strong attacks, heavy armor")
    print("  2. Wizard - Spell casting, ranged attacks, lower HP\n")
    
    # Get user class choice
    user_class = ''
    while user_class not in ['fighter', 'wizard', '1', '2']:
        choice = input("Choose your class (fighter/wizard or 1/2): ").strip().lower()
        if choice in ['1', 'fighter']:
            user_class = 'fighter'
        elif choice in ['2', 'wizard']:
            user_class = 'wizard'
        else:
            print("Invalid choice. Please enter 'fighter', 'wizard', '1', or '2'")
    
    print(f"\n⚔️ You have chosen: {user_class.upper()}!")
    
    # Create character with class-specific stats
    user_attributes = create_character(user_class)
    
    print("Generating your battle scenario...\n")


    # ===== SESSION SETUP =====
    # Create an in-memory session service to manage game state
    session_service = InMemorySessionService()

    # Initialize game state with user character
    initial_state = {
        'user:user_name': 'abc',
        'user:strategy': '',
        'user_attributes': user_attributes,  # Character stats (HP, AC, spells, etc.)
    }

    # Create unique session identifiers
    USER_ID = 'abc123'
    APP_NAME = 'dnd_app'
    SESSION_ID = str(uuid.uuid4())

    # Create new session with initial state
    session = await session_service.create_session(
        user_id=USER_ID,
        app_name=APP_NAME,
        session_id=SESSION_ID,
        state=initial_state,
    )
    print(f'New session created with id: {SESSION_ID}')

    # ===== AGENT RUNNER SETUP =====
    # Create root agent runner that will coordinate all subagents
    root_runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,  # Root agent handles routing to bg_initializer or dm_agent
        session_service=session_service,
    )

    # ===== BATTLE SCENARIO GENERATION =====
    # Call root agent to generate theme, monster, and battleground
    response, initial_state = await call_agent(
        runner=root_runner,
        session_id=SESSION_ID,
        user_id=USER_ID,
        user_input="Generate a D&D combat theme.",
        session_service=session_service,
    )

    # Extract generated battle components
    theme = initial_state.get('theme', '')  # Background story
    monster = initial_state.get('monster', {})  # Monster stats and emoji
    battle_ground = initial_state.get('battleground', {})  # Grid, terrain, positions

    # Validate that battle was generated successfully
    if not theme or not monster or not battle_ground:
        print("Error: Failed to generate battle scenario")
        return

    # Display the generated background story
    print(f'\n🎭 Background Story:\n{theme}\n')
    print('\n' + '='*70)
    print('⚔️  BATTLE BEGINS!')
    print('='*70)
    
    # ===== DISPLAY INITIAL BATTLEGROUND =====
    # Show the grid with character/monster positions and terrain
    show_battle_ground(
        battle_ground['size'], 
        battle_ground['rectangle_position'],  # List of terrain positions
        battle_ground['environment_emoji'],  # Terrain emoji (🔥, 🌳, etc.)
        battle_ground['user_position'], 
        battle_ground['monster_position'], 
        monster['monster_emoji']
    )
    
    # ===== TURN TRACKER INITIALIZATION =====
    # Initialize turn tracker for action economy if not already present
    if not initial_state:
        # Fallback: fetch from session if state wasn't returned
        updated_session = await session_service.get_session(
            user_id=USER_ID,
            app_name=APP_NAME,
            session_id=SESSION_ID,
        )
        initial_state = updated_session.state
    
    # Create turn tracker to manage movement, action, and bonus action per turn
    if 'turn_tracker' not in initial_state:
        initial_state['turn_tracker'] = {
            'current_turn': 'user',  # Whose turn it is
            'movement_used': 0,  # How many squares moved this turn
            'action_used': False,  # Whether main action was used
            'bonus_action_used': False,  # Whether bonus action was used
        }
    
    # ===== DISPLAY COMBAT STATUS =====
    # Show HP, AC, positions, and spell slots
    display_combat_state(
        initial_state.get('user_attributes', {}),
        initial_state.get('monster', {}),
        initial_state.get('battleground', {})
    )
    
    # ===== COMBAT INSTRUCTIONS =====
    # Display available commands based on character class
    print("\n📖 Turn-Based Combat Instructions:")
    print("  ⚡ YOU CAN TAKE MULTIPLE ACTIONS PER TURN!")
    print("  ")
    print("  Actions available each turn:")
    print("    - Movement: up to your speed (2 squares)")
    print("    - Action: attack or cast spell (once per turn)")
    
    # Show class-specific actions
    if user_class == 'wizard':
        print("    - Bonus Action: cast heal spell")
    else:
        print("    - Bonus Action: (coming soon)")
    
    print("  ")
    print("  Commands:")
    print("    • 'move north/south/east/west' - Move in a direction")
    print("    • 'attack' - Attack if adjacent to monster")
    
    # Show wizard-specific commands
    if user_class == 'wizard':
        print("    • 'cast magic_missile' - Cast Magic Missile (level 1 spell)")
        print("    • 'cast fireball' - Cast Fireball (level 2 spell)")
        print("    • 'cast heal' - Heal yourself (bonus action)")
        print("    • 'check spells' - View spell slots")
    
    print("    • 'end turn' - Finish your turn (monster will act)")
    print("    • 'status' - Check current battle state")
    print("    • 'quit' - Exit combat")
    print("  ")
    
    # Show class-specific tips
    if user_class == 'wizard':
        print("  💡 TIP: Use heal as a bonus action after attacking!")
        print("      Example: 'cast fireball' → 'cast heal' → 'end turn'")
    else:
        print("  💡 TIP: You can move AND attack in the same turn!")
        print("      Example: 'move north' → 'attack' → 'end turn'")
    
    print("\n" + "="*70 + "\n")
    
    # ===== MAIN COMBAT LOOP =====
    # Loop continues until combat ends (victory, defeat, or quit)
    combat_active = True
    current_state = initial_state  # Track current state across turns
    
    while combat_active:
        # Get user input for their action
        user_action = input("🧙 Your action: ").strip()
        
        # Handle quit command
        if user_action.lower() in ['quit', 'exit']:
            print("\n👋 Exiting combat. Thanks for playing!")
            break
        
        # Validate input
        if not user_action:
            print("⚠️  Please enter an action!")
            continue
        
        # ===== PROCESS USER ACTION =====
        # Send action to DM agent which will:
        # 1. Execute user's action (move/attack/cast spell)
        # 2. Update game state
        # 3. Execute monster turn if user ended their turn
        # 4. Return updated state
        response, current_state = await call_agent(
            runner=root_runner,
            session_id=SESSION_ID,
            user_id=USER_ID,
            user_input=user_action,
            session_service=session_service,
        )
        
        # Display DM's response (what happened, results, etc.)
        print(f"\n{'='*70}")
        print(response)
        print(f"{'='*70}\n")
        
        # ===== STATUS CHECK HANDLING =====
        # If user requested status, show current combat state
        if 'status' in user_action.lower():
            # Debug: Show positions
            print(f"[DEBUG] Current state - User: {current_state.get('battleground', {}).get('user_position')}, Monster: {current_state.get('battleground', {}).get('monster_position')}")
            
            # Redisplay battleground
            show_battle_ground(
                current_state.get('battleground', {}).get('size', [8, 8]),
                current_state.get('battleground', {}).get('rectangle_position', []),
                current_state.get('battleground', {}).get('environment_emoji', ''),
                current_state.get('battleground', {}).get('user_position', [0, 0]),
                current_state.get('battleground', {}).get('monster_position', [0, 0]),
                current_state.get('monster', {}).get('monster_emoji', '👾')
            )
            
            # Display combat status (HP, spell slots, etc.)
            display_combat_state(
                current_state.get('user_attributes', {}),
                current_state.get('monster', {}),
                current_state.get('battleground', {})
            )
        
        # ===== CHECK FOR COMBAT END =====
        # Check if combat has ended (victory or defeat)
        combat_status = current_state.get('combat_status', 'ongoing')
        
        if combat_status == 'user_won':
            # User won - display victory message
            monster_name = current_state.get('monster', {}).get('name', 'the monster')
            print(f"\n🎉 Congratulations! You have defeated {monster_name}!")
            print("=" * 70)
            break
        elif combat_status == 'monster_won':
            # User defeated - display defeat message
            print("\n💀 You have been defeated!")
            print("=" * 70)
            break

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())