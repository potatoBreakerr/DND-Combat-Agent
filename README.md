# D&D Combat Agent 🎲⚔️

A sophisticated turn-based combat simulator powered by AI agents, bringing Dungeons & Dragons 5th Edition combat mechanics to life through intelligent agent orchestration.

## Problem Statement

Traditional D&D combat simulators are either:
- **Too simplistic**: Single-action turns, basic mechanics
- **Too complex**: Require manual tracking of multiple resources
- **Not intelligent**: Monster AI follows rigid patterns
- **Poor UX**: Limited feedback on action results

**Key Challenges**:
1. Managing complex turn-based action economy (movement, action, bonus action)
2. Coordinating multiple AI agents for different responsibilities
3. Maintaining persistent state across turn cycles
4. Providing clear, informative feedback for each action
5. Balancing realism with playability

## Solution

An **AI agent-based architecture** that:

✅ **Complex Action Economy**: Full D&D 5e turn structure with movement, action, and bonus action  
✅ **Intelligent AI**: DM agent orchestrates combat with context-aware responses  
✅ **Multi-Class System**: Fighter (melee) and Wizard (spellcasting) classes  
✅ **Dynamic Terrain**: Procedurally generated battlegrounds with obstacles and hazards  
✅ **Spell System**: Full spell slot management with 3 spells (Magic Missile, Fireball, Heal)  
✅ **Rich Feedback**: Detailed action results with HP changes, spell slots, and tactical info

---

## Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         USER INPUT                          │
│                    (commands, actions)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      ROOT AGENT                              │
│              (Routes to appropriate agent)                   │
└──────────┬────────────────────────────┬─────────────────────┘
           │                            │
           ▼                            ▼
┌──────────────────────┐    ┌──────────────────────────────────┐
│  BATTLE INITIALIZER  │    │         DM AGENT                 │
│                      │    │  (Combat Orchestration)          │
│  ┌────────────────┐ │    │                                  │
│  │ Theme Agent    │ │    │  ┌────────────────────────────┐  │
│  └────────────────┘ │    │  │ Combat Tools (20+)         │  │
│  ┌────────────────┐ │    │  │ - Movement tracking        │  │
│  │ Monster Gen    │ │    │  │ - Attack resolution        │  │
│  └────────────────┘ │    │  │ - Spell casting            │  │
│  ┌────────────────┐ │    │  │ - Terrain effects          │  │
│  │ Battleground   │ │    │  │ - Turn management          │  │
│  │ Designer       │ │    │  └────────────────────────────┘  │
│  └────────────────┘ │    └──────────────────────────────────┘
└──────────────────────┘                      │
                                             │
                                             ▼
                              ┌──────────────────────────────┐
                              │    SESSION STATE             │
                              │  - User attributes           │
                              │  - Monster stats             │
                              │  - Battleground grid         │
                              │  - Turn tracker              │
                              │  - Combat status             │
                              └──────────────────────────────┘
```

### Agent Responsibilities

#### 1. **Root Agent**
- Routes user input to appropriate sub-agent
- Battle initialization → `battle_ground_initializer`
- Combat actions → `dm_agent`

#### 2. **Battle Ground Initializer**
Coordinates three sub-agents to create the scenario:
- **Theme Agent**: Generates background story
- **Monster Generator**: Creates monster with stats and emoji
- **Battleground Designer**: Generates varied terrain patterns

#### 3. **DM Agent** (Dungeon Master)
The core combat orchestrator that:
- Processes user actions (move, attack, cast spell)
- Manages turn economy (tracks movement, action, bonus action)
- Controls monster AI behavior
- Applies terrain effects
- Checks victory/defeat conditions
- Provides detailed feedback with numbers and results

### State Management

```
SESSION STATE
├── user_attributes
│   ├── class: "fighter" | "wizard"
│   ├── hp / max_hp
│   ├── ac, speed, damage
│   └── spell_slots (wizards)
│       ├── level_1: 3
│       └── level_2: 2
├── monster
│   ├── name, emoji
│   ├── hp, ac, damage, speed
│   └── position: [row, col]
├── battleground
│   ├── size: [rows, cols]
│   ├── rectangle_position: [[r,c], ...]  # Terrain positions
│   ├── environment: "BLOCKED" | "DAMAGE"
│   ├── user_position: [r, c]
│   └── monster_position: [r, c]
└── turn_tracker
    ├── current_turn: "user" | "monster"
    ├── movement_used: 0-2
    ├── action_used: bool
    └── bonus_action_used: bool
```

---

## Features

### 🎭 **Class System**

| Class   | HP   | AC | Speed | Damage  | Special Abilities              |
|---------|------|----|----|---------|--------------------------------|
| Fighter | 15-25| 13 | 2  | 7-10    | High HP, strong melee attacks  |
| Wizard  | 10-18| 11 | 2  | 4-7     | 3 spells, spell slot management|

### ⚡ **Action Economy**

Each turn, players can:
- **Movement**: Up to speed (2 squares), cumulative tracking
- **Action**: Attack OR cast damage spell (once per turn)
- **Bonus Action**: Cast Heal spell (wizards only)

**Example Turn**:
```
> move south
> move south  
> cast fireball    (uses action)
> cast heal        (uses bonus action)
> end turn         (monster acts)
```

### 🔮 **Spell System** (Wizard)

| Spell         | Level | Type   | Damage/Heal | Slots | Action Type  |
|---------------|-------|--------|-------------|-------|--------------|
| Magic Missile | 1     | Damage | 6-10        | 3     | Action       |
| Fireball      | 2     | Damage | 12-24       | 2     | Action       |
| Heal          | 1     | Heal   | 6-10 HP     | 3     | Bonus Action |

### 🗺️ **Terrain System**

**BLOCKED Terrain** 🌳:
- Impassable (walls, pillars, trees)
- Prevents movement through positions
- Generated as varied patterns (not rectangles!)

**DAMAGE Terrain** 🔥:
- Hazardous (fire, lava, acid)
- Deals 1d4 damage at end of turn

**Pattern Examples**:
- Central pillar (2x2 blocked area)
- Scattered fire pits
- L-shaped hazards
- Vertical wall dividers

---

## Installation & Setup

### Prerequisites

- **Python**: 3.10+
- **Google AI SDK**: For Gemini models
- **API Key**: Google AI/Vertex AI credentials

### 1. Clone Repository

```bash
git clone <repository-url>
cd dndcombatagent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages**:
```
google-adk
google-generativeai
python-dotenv
pydantic
```

### 3. Configure API Key

Create `.env` file in project root:

```bash
GOOGLE_API_KEY=your_api_key_here
```

Or set environment variable:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

### 4. Run the Game

```bash
cd dnd_combat_agent
python3 main.py
```

---

## Usage Guide

### Starting a Game

```
$ python3 main.py

🎮 D&D COMBAT AGENT
Choose your class:
  1. Fighter - High HP, strong attacks
  2. Wizard - Spell casting, ranged attacks

Choose your class (fighter/wizard or 1/2): 2

⚔️ You have chosen: WIZARD!
```

### During Combat

**Combat Display**:
```
------------------------------------------------------------
COMBAT STATUS
------------------------------------------------------------
🧙 YOU (WIZARD)
   HP: 15/18 | AC: 11 | Position: [0, 3]
   Spell Slots: Lv1: 3/3 | Lv2: 2/2

🐺 WINTER WOLF
   HP: 40 | AC: 14 | Position: [7, 4]

Distance: 8 squares | Terrain: ❄️ DAMAGE
------------------------------------------------------------
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `move <direction>` | Move in direction | `move south` |
| `attack` | Melee attack (adjacent) | `attack` |
| `cast <spell>` | Cast spell | `cast fireball` |
| `status` | Show combat status | `status` |
| `end turn` | End your turn | `end turn` |
| `quit` | Exit combat | `quit` |

**Directions**: north, south, east, west, northeast, northwest, southeast, southwest

### Wizard Spells

```bash
# Damage spells (use action)
> cast magic_missile
> cast fireball

# Healing (uses bonus action)
> cast heal

# Check remaining slots
> check spells
```

### Example Combat Flow

```
🧙 Your action: move south
You move south to [1,3]. Movement: 1/2 used.

🧙 Your action: cast fireball
You cast Fireball! Deals 18 damage to Winter Wolf!
HP: 40 → 22. Spell slots: Lv2: 1/2

🧙 Your action: cast heal
You cast Heal! Restore 8 HP!
HP: 15 → 18. Spell slots: Lv1: 2/3

🧙 Your action: end turn

Monster Turn:
Winter Wolf moves and attacks for 6 damage!
HP: 18 → 12

Your turn begins. All actions refreshed.
```

---

## Project Structure

```
dndcombatagent/
├── dnd_combat_agent/
│   ├── main.py                 # Entry point, game loop
│   ├── utils.py                # Helper functions
│   └── subagents/
│       ├── subagents.py        # All agent definitions
│       ├── dm_agent.py         # DM agent (combat orchestrator)
│       ├── tools.py            # Combat tools (20+ functions)
│       ├── callbacks.py        # Agent callbacks (emoji cleanup)
│       └── output_schema.py    # Pydantic schemas
├── .env                        # API keys (not in repo)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## Technical Details

### Tool Architecture

The DM agent has access to 16+ tools:

**Information Tools**:
- `check_user_info`: View player stats
- `check_monster_info`: View monster stats
- `check_battleground_info`: View grid and terrain
- `get_distance`: Calculate Manhattan distance
- `check_in_range`: Check if in attack range

**Action Tools**:
- `move_character`: Move with validation
- `attack`: D20 attack rolls with AC checks
- `cast_spell`: Spell execution with slot management
- `apply_terrain_effects`: Environmental damage

**Turn Management**:
- `reset_turn`: Start new turn
- `check_turn_status`: View available actions
- `end_user_turn`: Switch to monster turn

**Spell Tools** (Wizard):
- `cast_spell`: Spell casting engine
- `check_spell_slots`: View remaining slots

### AI Agent Models

- **Root Agent**: Gemini 2.5 Flash
- **DM Agent**: Gemini 2.5 Flash
- **Theme Agent**: Gemini 2.5 Flash
- **Monster Generator**: Gemini 2.5 Flash  
- **Battleground Designer**: Gemini 2.5 Flash

---

## Design Decisions

### Why Agent-Based Architecture?

1. **Separation of Concerns**: Each agent has a specific role
2. **Flexibility**: Easy to add new agents or modify existing ones
3. **Intelligent Behavior**: AI makes context-aware decisions
4. **Natural Language**: Users can express intent naturally
5. **Scalability**: Easy to extend with more classes, spells, monsters

### Action Economy Design

Follows D&D 5e rules:
- **Movement**: Cumulative up to speed (can move 1, then 1 more)
- **Action**: One per turn (attack OR spell)
- **Bonus Action**: Separate resource (heal spell)
- **No auto-end**: User explicitly ends turn

This prevents the "move-attack-done" rigidity of simpler systems.

### State Immutability

Tools create copies before modifying:
```python
monster_copy = dict(monster)
monster_copy['hp'] = new_hp
tool_context.state['monster'] = monster_copy
```

This ensures session service detects changes.

---

## Future Enhancements

- [ ] More character classes (Rogue, Cleric, Paladin)
- [ ] Additional spells and abilities
- [ ] Multi-enemy encounters
- [ ] Saving throws and conditions (stunned, poisoned)
- [ ] Cover and line of sight
- [ ] Inventory and equipment system
- [ ] Campaign mode with XP progression
- [ ] Visual web interface

---

## Contributing

Contributions welcome! Areas for improvement:
- Additional D&D mechanics
- More intelligent monster AI
- Better terrain generation algorithms
- UI/UX enhancements
- Performance optimizations


---

## Acknowledgments

Built with:
- **Google ADK**: Agent orchestration framework
- **Google Gemini**: AI models powering agent intelligence
- **D&D 5e**: Combat mechanics and inspiration

---

## Support

For issues or questions:
1. Check existing documentation
2. Review code comments
3. Open an issue on GitHub
4. Contact: haozhu301@gmail.com

---

**Happy adventuring! 🐉⚔️**
