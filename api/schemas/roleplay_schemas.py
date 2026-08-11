from typing import Literal

from pydantic import BaseModel, Field

EndingCondition = Literal[
    "goals_achieved",
    "profanity",
    "conversation_exhausted",
    "irrelevant",
    "none",
]


class ConversationMessage(BaseModel):
    """One turn in the roleplay conversation."""

    role: Literal["learner", "ai_character"] = Field(
        ...,
        description="Speaker role: 'learner' or 'ai_character'.",
    )
    content: str = Field(..., description="Message content for this turn.")


class RoleplaySetup(BaseModel):
    """Fixed config for one practice session (scenario, roles, goals)."""

    scenario: str = Field(
        ...,
        description="The roleplay scenario and setting.",
        examples=["You are at a car dealership negotiating the price of a used sedan."],
    )
    learner_role: str = Field(
        ...,
        description="The role the learner is playing.",
        examples=["A first-time car buyer"],
    )
    learner_goals: list[str] = Field(
        ...,
        min_length=1,
        description="Goals the learner should practice during the roleplay.",
        examples=[["Negotiate a fair price", "Ask about warranty options"]],
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


class CreateRoleplayRequest(RoleplaySetup):
    """Start a new practice session: send setup only."""


class RoleplayChatRequest(BaseModel):
    """Continue a session: send only the session id and the new learner message."""

    roleplay_id: str = Field(..., description="Id of the roleplay session in cache.")
    learner_message: str = Field(
        ...,
        description="The learner's latest message in the conversation.",
        examples=["Hi, I'm interested in this car. What's your best price?"],
    )


class RoleplaySession(RoleplaySetup):
    """Server-side session state stored in Redis (setup + live chat state)."""

    roleplay_id: str = Field(..., description="Unique id for this roleplay session.")
    conversation_history: list[ConversationMessage] = Field(
        default_factory=list,
        description="Conversation turns so far, oldest first.",
    )
    irrelevant_message_count: int = Field(
        default=0,
        ge=0,
        description="How many irrelevant learner messages have been counted so far.",
    )
    should_end: bool = Field(
        default=False,
        description="True if the roleplay has already ended.",
    )


class CreateRoleplayResponse(BaseModel):
    """Returned after a session is created."""

    roleplay_id: str = Field(..., description="Id of the newly created roleplay session.")


class EndingDecision(BaseModel):
    """Whether/why the roleplay should stop (shared by eval + chat response)."""

    should_end: bool = Field(
        ...,
        description="True if the roleplay should end based on any ending condition.",
    )
    ending_condition: EndingCondition = Field(
        ...,
        description="Primary ending condition, or 'none' if the conversation should continue.",
    )


class GoalStatus(BaseModel):
    """Status of a single learner goal."""

    goal: str = Field(..., description="The learner goal being evaluated.")
    achieved: bool = Field(
        ...,
        description="True if this goal has been clearly achieved based on learner messages.",
    )
    evidence: str = Field(
        ...,
        description="Short evidence from learner messages, or why it is not yet achieved.",
    )


class RawGoalsEvaluation(BaseModel):
    """Goals signals produced by the LLM (before app adds all_goals_achieved)."""

    goal_statuses: list[GoalStatus] = Field(
        ...,
        description="Per-goal achievement status based on learner messages.",
    )
    rationale: str = Field(
        ...,
        description="Brief summary of the goals evaluation.",
    )


class GoalsEvaluation(RawGoalsEvaluation):
    """Goals evaluation plus the app-computed all-goals flag."""

    all_goals_achieved: bool = Field(
        ...,
        description="True only if every learner goal has been achieved.",
    )


class RawEndingEvaluation(BaseModel):
    """Ending signals produced by the LLM (before app decides should_end)."""

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
        description="Brief explanation of the non-goal ending-condition evaluation.",
    )


class EndingEvaluation(RawEndingEvaluation, EndingDecision):
    """Ending evaluation plus app-computed should_end and ending_condition."""


class RoleplayChatResponse(EndingDecision):
    """API response for one chat turn."""

    roleplay_id: str = Field(..., description="Id of the roleplay session.")
    ai_response: str = Field(
        ...,
        description="The AI character's reply to the learner's message.",
    )
    ending_rationale: str | None = Field(
        default=None,
        description="Why the roleplay ended. Set only when should_end is true.",
    )
