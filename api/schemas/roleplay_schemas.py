from pydantic import BaseModel, Field
from typing import Literal


class ConversationTurn(BaseModel):
    role: Literal['learner', 'ai_character'] = Field(
        ...,
        description="Speaker role: 'learner' or 'ai_character'.",
    )
    content: str = Field(..., description="Message content for this turn.")


class RoleplayRequest(BaseModel):
    scenario: str = Field(
        ...,
        description="The roleplay scenario and setting.",
        examples=["You are at a car dealership negotiating the price of a used sedan."],
    )
    learner_goals: list[str] = Field(
        ...,
        min_length=1,
        description="Goals the learner should practice during the roleplay.",
        examples=[["Negotiate a fair price", "Ask about warranty options"]],
    )
    learner_role: str = Field(
        ...,
        description="The role the learner is playing.",
        examples=["A first-time car buyer"],
    )
    learner_message: str = Field(
        ...,
        description="The learner's latest message in the conversation.",
        examples=["Hi, I'm interested in this car. What's your best price?"],
    )
    ai_character_name: str = Field(
        ...,
        description="Name of the AI character.",
        examples=["Alex"],
    )
    ai_character_role: str = Field(
        ...,
        description="Role the AI character is playing.",
        examples=["Experienced car salesperson"],
    )
    ai_character_personality: str = Field(
        ...,
        description="Personality traits and tone for the AI character.",
        examples=["Friendly but persuasive, focused on closing the deal."],
    )
    conversation_history: list[ConversationTurn] = Field(
        default_factory=list,
        description="Prior turns in the conversation, oldest first.",
    )


class RoleplayResponse(BaseModel):
    ai_character_name: str = Field(
        ...,
        description="Name of the AI character that responded.",
    )
    ai_response: str = Field(
        ...,
        description="The AI character's reply to the learner's message.",
    )
