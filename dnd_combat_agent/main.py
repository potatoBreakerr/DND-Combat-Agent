import asyncio
import uuid

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from subagents.subagents import bg_initializer
from utils import call_agent, show_battle_ground, create_character

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

    bg_initializer_runner = Runner(
        app_name=APP_NAME,
        agent=bg_initializer,
        session_service=session_service,
    )


    response = await call_agent(
        runner=bg_initializer_runner,
        session_id=SESSION_ID,
        user_id=USER_ID,
        user_input="Generate a D&D combat theme."
    )

    updated_session = await session_service.get_session(
        user_id=USER_ID,
        app_name=APP_NAME,
        session_id=SESSION_ID,
    )

    battle_ground = updated_session.state['battleground']
    monster = updated_session.state['monster']

    print(f'Background story: {updated_session.state['theme']}')
    print(f'Battle ground design: {battle_ground}')
    print(f'Monster: {monster}')
    print(f'Response: {response}')

    print('==== Final Session State ====')
    for key, value in updated_session.state.items():
        print(f'{key}: {type(value)}')

    print('==== Battle Ground ====')
    show_battle_ground(battle_ground['size'], battle_ground['rectangle_position'], battle_ground['environment_emoji'], battle_ground['user_position'], battle_ground['monster_position'], monster['monster_emoji'])

    

if __name__ == "__main__":
    asyncio.run(main())