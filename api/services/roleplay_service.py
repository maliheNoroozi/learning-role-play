import os
from functools import lru_cache
from typing import Annotated

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict

from api.schemas.roleplay_schemas import (
    ConversationMessage,
    EndingEvaluation,
    GoalsEvaluation,
    LLMGoalsEvaluation,
    RoleplayRequest,
    RoleplayResponse,
)
from api.services.config import CHATGPT_MODEL, CHATGPT_TEMPERATURE
from api.services.prompts import (
    ENDING_EVALUATION_PROMPT,
    GOALS_EVALUATION_PROMPT,
    ROLEPLAY_ENDING_SYSTEM_PROMPT,
    ROLEPLAY_SYSTEM_PROMPT,
)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    scenario: str
    learner_role: str
    learner_goals: list[str]
    ai_character_name: str
    ai_character_role: str
    ai_character_personality: str
    goals_evaluation: NotRequired[GoalsEvaluation]
    ending_evaluation: NotRequired[EndingEvaluation]


@lru_cache
def get_roleplay_service() -> "RoleplayService":
    return RoleplayService()


class RoleplayService:
    def __init__(
        self, model: str = CHATGPT_MODEL, temperature: float = CHATGPT_TEMPERATURE
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise KeyError("OPENAI_API_KEY")

        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
        )

        evaluator_base = ChatOpenAI(
            model=model,
            temperature=0,
            api_key=api_key,
        )
        self.goals_evaluator_llm = evaluator_base.with_structured_output(
            LLMGoalsEvaluation,
            method="json_schema",
            strict=True,
        )
        self.ending_evaluator_llm = evaluator_base.with_structured_output(
            EndingEvaluation,
            method="json_schema",
            strict=True,
        )
        self.graph = self._build_graph()

    def _build_graph(self):
        def evaluate_goals(state: State):
            """Evaluate goal achievement from learner messages."""
            prompt = PromptTemplate.from_template(
                GOALS_EVALUATION_PROMPT,
                template_format="jinja2",
            ).format(
                scenario=state["scenario"],
                learner_role=state["learner_role"],
                goals=RoleplayService._format_goals(learner_goals=state["learner_goals"]),
                learner_messages=self._format_learner_messages(state["messages"]),
                conversation=self._format_conversation(state["messages"]),
            )
            llm_evaluation = self.goals_evaluator_llm.invoke(
                [SystemMessage(content=prompt)]
            )
            evaluation = GoalsEvaluation(
                **llm_evaluation.model_dump(),
                all_goals_achieved=all(
                    status.achieved for status in llm_evaluation.goal_statuses
                ),
            )
            return {"goals_evaluation": evaluation}

        def evaluate_ending(state: State):
            """Decide whether the conversation should end, using goals evaluation."""
            prompt = PromptTemplate.from_template(
                ENDING_EVALUATION_PROMPT,
                template_format="jinja2",
            ).format(
                scenario=state["scenario"],
                learner_role=state["learner_role"],
                ai_character_name=state["ai_character_name"],
                ai_character_role=state["ai_character_role"],
                goals_evaluation=state["goals_evaluation"].model_dump_json(indent=2),
                conversation=self._format_conversation(state["messages"]),
            )
            evaluation = self.ending_evaluator_llm.invoke(
                [SystemMessage(content=prompt)]
            )
            return {"ending_evaluation": evaluation}

        def generate_response(state: State):
            """Generate a normal or ending reply based on ending evaluation."""
            system_prompt = self._build_system_prompt(state)
            response = self.llm.invoke(
                [SystemMessage(content=system_prompt), *state["messages"]]
            )
            return {"messages": [response]}

        builder = StateGraph(State)
        builder.add_node("evaluate_goals", evaluate_goals)
        builder.add_node("evaluate_ending", evaluate_ending)
        builder.add_node("generate_response", generate_response)
        builder.add_edge(START, "evaluate_goals")
        builder.add_edge("evaluate_goals", "evaluate_ending")
        builder.add_edge("evaluate_ending", "generate_response")
        builder.add_edge("generate_response", END)
        return builder.compile()

    def generate_response(self, request: RoleplayRequest) -> RoleplayResponse:
        messages = self._to_langchain_messages(request.conversation_history)
        messages.append(HumanMessage(content=request.learner_message))

        result = self.graph.invoke(
            {
                "messages": messages,
                "scenario": request.scenario,
                "learner_role": request.learner_role,
                "learner_goals": request.learner_goals,
                "ai_character_name": request.ai_character_name,
                "ai_character_role": request.ai_character_role,
                "ai_character_personality": request.ai_character_personality,
            }
        )


        ai_message = result["messages"][-1]
        ai_response = (
            ai_message.content
            if isinstance(ai_message.content, str)
            else str(ai_message.content)
        )

        evaluation = result.get("ending_evaluation")
        if not isinstance(evaluation, EndingEvaluation):
            evaluation = EndingEvaluation(
                goals_achieved=False,
                learner_used_profanity=False,
                conversation_exhausted=False,
                should_end=False,
                ending_condition="none",
                rationale="",
            )

        return RoleplayResponse(
            ai_character_name=request.ai_character_name,
            ai_response=ai_response,
            should_end=evaluation.should_end,
            ending_condition=evaluation.ending_condition,
            ending_rationale=evaluation.rationale,
        )

    @staticmethod
    def _build_system_prompt(
        state: State
    ) -> str:
        ending = state["ending_evaluation"]
        shared_prompt_args = {
            "ai_character_name": state["ai_character_name"],
            "ai_character_role": state["ai_character_role"],
            "ai_character_personality": state["ai_character_personality"],
            "scenario": state["scenario"],
            "learner_role": state["learner_role"],
            "goals": RoleplayService._format_goals(learner_goals=state["learner_goals"]),
        }

        if ending.should_end:
            return PromptTemplate.from_template(
                ROLEPLAY_ENDING_SYSTEM_PROMPT,
                template_format="jinja2",
            ).format(
                **shared_prompt_args,
                ending_condition=ending.ending_condition,
                ending_rationale=ending.rationale,
            )

        return PromptTemplate.from_template(
            ROLEPLAY_SYSTEM_PROMPT,
            template_format="jinja2",
        ).format(**shared_prompt_args)

    @staticmethod
    def _format_goals(learner_goals: list[str]) -> str:
        return "\n".join(f"- {goal}" for goal in learner_goals)

    @staticmethod
    def _message_content(message: AnyMessage) -> str:
        return (
            message.content
            if isinstance(message.content, str)
            else str(message.content)
        )

    @classmethod
    def _format_learner_messages(cls, messages: list[AnyMessage]) -> str:
        lines = [
            f"- {cls._message_content(message)}"
            for message in messages
            if isinstance(message, HumanMessage)
        ]
        return "\n".join(lines) if lines else "(no learner messages)"

    @classmethod
    def _format_conversation(cls, messages: list[AnyMessage]) -> str:
        lines: list[str] = []
        for message in messages:
            if isinstance(message, HumanMessage):
                role = "Learner"
            elif isinstance(message, AIMessage):
                role = "AI character"
            else:
                continue
            lines.append(f"{role}: {cls._message_content(message)}")
        return "\n".join(lines) if lines else "(no messages)"

    @staticmethod
    def _to_langchain_messages(
        history: list[ConversationMessage],
    ) -> list[HumanMessage | AIMessage]:
        messages: list[HumanMessage | AIMessage] = []
        for message in history:
            if message.role == "learner":
                messages.append(HumanMessage(content=message.content))
            else:
                messages.append(AIMessage(content=message.content))
        return messages
