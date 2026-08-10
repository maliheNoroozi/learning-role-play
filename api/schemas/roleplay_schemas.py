from pydantic import BaseModel, Field
from typing import Literal

EndingCondition = Literal[
    "goals_achieved",
    "profanity",
    "conversation_exhausted",
    'irrelevant',
    "none",
]

class ConversationMessage(BaseModel):
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
    conversation_history: list[ConversationMessage] = Field(
        default_factory=list,
        description="Prior turns in the conversation, oldest first.",
    )


class GoalStatus(BaseModel):
    goal: str = Field(..., description="The learner goal being evaluated.")
    achieved: bool = Field(
        ...,
        description="True if this goal has been clearly achieved based on learner messages.",
    )
    evidence: str = Field(
        ...,
        description="Short evidence from learner messages, or why it is not yet achieved.",
    )


class LLMGoalsEvaluation(BaseModel):
    goal_statuses: list[GoalStatus] = Field(
        ...,
        description="Per-goal achievement status based on learner messages.",
    )
    rationale: str = Field(
        ...,
        description="Brief summary of the goals evaluation.",
    )


class GoalsEvaluation(LLMGoalsEvaluation):
    all_goals_achieved: bool = Field(
        ...,
        description="True only if every learner goal has been achieved.",
    )


class LLMEndingEvaluation(BaseModel):
    learner_used_profanity: bool = Field(
        ...,
        description="True if the learner used swear words or other profane/offensive language.",
    )
    conversation_exhausted: bool = Field(
        ...,
        description="True if the conversation is stuck, looping, or naturally concluded.",
    )
    learner_message_irrelevant: bool = Field(
        ...,
        description=(
            "True if the learner's latest message is clearly irrelevant or "
            "off-topic for the scenario and roleplay goals."
        ),
    )
    rationale: str = Field(
        ...,
        description="Brief explanation of the ending-condition evaluation.",
    )


class EndingEvaluation(LLMEndingEvaluation):
    goals_achieved: bool = Field(
        ...,
        description="True if all learner goals were achieved (from the goals evaluator).",
    )
    should_end: bool = Field(
        ...,
        description="True if the roleplay should end based on any ending condition.",
    )
    ending_condition: EndingCondition = Field(
        ...,
        description="Primary ending condition, or 'none' if the conversation should continue.",
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
    should_end: bool = Field(
        ...,
        description="Whether the roleplay conversation should end.",
    )
    ending_condition: EndingCondition = Field(
        ...,
        description="Primary reason the conversation should end, or 'none'.",
    )
    ending_rationale: str = Field(
        ...,
        description="Brief explanation of the ending evaluation.",
    )
