from pydantic import BaseModel, Field

class MonsterContent(BaseModel):
    name: str = Field(description="The name of the monster.")
    monster_emoji: str = Field(description="The emoji to represent the monster.")
    hp: int = Field(description="The hit points of the monster.")
    ac: int = Field(description="The armor class of the monster.")
    damage: list[int] = Field(description="The attack damage range of the monster.")
    speed: int = Field(description="The speed of the monster.")

class BattlegroundContent(BaseModel):
    size: list[int] = Field(description="The size of the battle ground grid.")
    rectangle_position: list[list[int]] = Field(description="The top-left and bottom-right positions of the rectangle area.")
    environment: str = Field(description="The environment type of the rectangle area.")
    environment_emoji: str = Field(description="The emoji to represent the environment.")
    user_position: list[int] = Field(description="The start position of the user.")
    monster_position: list[int] = Field(description="The start position of the monster.")
