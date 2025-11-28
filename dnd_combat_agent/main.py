import asyncio
import uuid

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from subagents.subagents import root_agent
from utils import call_agent, show_battle_ground, create_character, display_combat_state

load_dotenv()


async def main():
    user_class = 'fighter'
    user_attributes = create_character(user_class)

    session_service = InMemorySessionService()

    initial_state = {
        'user:user_name': 'abc',
        'user:strategy': '',
        'user_attributes': user_attributes,
    }

    USER_ID = 'abc123'
    APP_NAME = 'dnd_app'
    SESSION_ID = str(uuid.uuid4())

    # create new session
    session = await session_service.create_session(
        user_id=USER_ID,
        app_name=APP_NAME,
        session_id=SESSION_ID,
        state=initial_state,
    )
    print(f'New session created with id: {SESSION_ID}')

    # Create root agent runner
    root_runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
    )

    print('\n' + '='*70)
    print('🎮 D&D COMBAT AGENT')
    print('='*70)
    print('\n🎲 Welcome to the D&D Combat Arena!')
    print('Let\'s start by generating your battle scenario...\n')

    # Initialize battle using root agent
    response, initial_state = await call_agent(
        runner=root_runner,
        session_id=SESSION_ID,
        user_id=USER_ID,
        user_input="Generate a D&D combat theme and initialize a new battle.",
        session_service=session_service
    )

    # Use the returned state directly instead of fetching
    if not initial_state:
        # Fallback to get_session if state wasn't returned
        updated_session = await session_service.get_session(
            user_id=USER_ID,
            app_name=APP_NAME,
            session_id=SESSION_ID,
        )
        initial_state = updated_session.state

    battle_ground = initial_state.get('battleground')
    monster = initial_state.get('monster')
    theme = initial_state.get('theme')

    if not battle_ground or not monster:
        print("⚠️  Failed to initialize battle. Please try again.")
        return

    print(f'\n🎭 Background Story:\n{theme}\n')
    print('\n' + '='*70)
    print('⚔️  BATTLE BEGINS!')
    print('='*70)
    
    # Show initial battleground
    show_battle_ground(
        battle_ground['size'], 
        battle_ground['rectangle_position'], 
        battle_ground['environment_emoji'], 
        battle_ground['user_position'], 
        battle_ground['monster_position'], 
        monster['monster_emoji']
    )
    
    # Display initial combat state
    display_combat_state(
        initial_state.get('user_attributes', {}),
        initial_state.get('monster', {}),
        initial_state.get('battleground', {})
    )
    
    print("\n📖 Combat Instructions:")
    print("  - Move: 'move north/south/east/west' or diagonal 'move northeast/northwest/southeast/southwest'")
    print("  - Attack: 'attack' (you must be adjacent to the monster)")
    print("  - Status: 'status' (check current battle state)")
    print("  - Quit: 'quit' or 'exit'\n")
    
    # Combat loop - now using root agent for all interactions
    combat_active = True
    current_state = initial_state  # Track current state
    
    while combat_active:
        # Get user input
        user_action = input("🧙 Your action: ").strip()
        
        if user_action.lower() in ['quit', 'exit']:
            print("\n👋 Exiting combat. Thanks for playing!")
            break
        
        if not user_action:
            print("⚠️  Please enter an action!")
            continue
        
        # Call root agent - it will route to dm_agent automatically for combat actions
        response, updated_state = await call_agent(
            runner=root_runner,
            session_id=SESSION_ID,
            user_id=USER_ID,
            user_input=user_action,
            session_service=session_service
        )
        
        # Use the returned state directly
        if updated_state:
            current_state = updated_state
        
        # Display agent's response
        print("\n" + "="*70)
        if response:
            for response_text in response:
                print(response_text)
        print("="*70)
        
        # Show updated battleground using the state returned from call_agent
        battle_ground = current_state.get('battleground', {})
        monster = current_state.get('monster', {})
        print(f"\n[DEBUG] Current state - User: {battle_ground.get('user_position')}, Monster: {battle_ground.get('monster_position')}")
        
        if battle_ground and monster:
            show_battle_ground(
                battle_ground.get('size', [5, 5]),
                battle_ground.get('rectangle_position', [[0, 0], [0, 0]]),
                battle_ground.get('environment_emoji', ''),
                battle_ground.get('user_position', [0, 0]),
                battle_ground.get('monster_position', [0, 0]),
                monster.get('monster_emoji', '👾')
            )
            
            # Display combat state
            display_combat_state(
                current_state.get('user_attributes', {}),
                current_state.get('monster', {}),
                current_state.get('battleground', {})
            )
        
        # Check if combat ended
        user_hp = current_state.get('user_attributes', {}).get('hp', 0)
        monster_hp = current_state.get('monster', {}).get('hp', 0)
        
        if user_hp <= 0:
            print("\n💀 DEFEAT! You have been slain in battle!")
            combat_active = False
        elif monster_hp <= 0:
            monster_name = updated_session.state.get('monster', {}).get('name', 'the monster')
            print(f"\n🎉 VICTORY! You have defeated {monster_name}!")
            combat_active = False

    

if __name__ == "__main__":
    asyncio.run(main())