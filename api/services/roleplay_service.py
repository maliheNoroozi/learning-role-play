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
    EndingCondition,
    EndingEvaluation,
    GoalsEvaluation,
    LLMEndingEvaluation,
    LLMGoalsEvaluation,
    RoleplayRequest,
    RoleplayResponse,
)
from api.services.config import CHATGPT_MODEL, CHATGPT_TEMPERATURE, IRRELEVANT_MESSAGE_LIMIT
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
    irrelevant_message_count: int
    goals_evaluation: NotRequired[GoalsEvaluation]
    llm_ending_evaluation: NotRequired[LLMEndingEvaluation]
    ending_evaluation: NotRequired[EndingEvaluation]
    normal_response: NotRequired[str]
    ending_response: NotRequired[str]


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
            LLMEndingEvaluation,
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
            """Evaluate profanity, exhaustion, and irrelevant-message ending conditions."""
            prompt = PromptTemplate.from_template(
                ENDING_EVALUATION_PROMPT,
                template_format="jinja2",
            ).format(
                scenario=state["scenario"],
                learner_role=state["learner_role"],
                ai_character_name=state["ai_character_name"],
                ai_character_role=state["ai_character_role"],
                conversation=self._format_conversation(state["messages"]),
            )
            evaluation = self.ending_evaluator_llm.invoke(
                [SystemMessage(content=prompt)]
            )
            previous_count_of_irrelevant_messages = state.get("irrelevant_message_count", 0)
            irrelevant_message_count = previous_count_of_irrelevant_messages + (
                1 if evaluation.learner_message_irrelevant else 0
            )
            return {
                "llm_ending_evaluation": evaluation,
                "irrelevant_message_count": irrelevant_message_count,
            }

        def generate_normal_response(state: State):
            """Generate a normal in-character reply."""
            system_prompt = self._build_normal_system_prompt(state)
            response = self.llm.invoke(
                [SystemMessage(content=system_prompt), *state["messages"]]
            )
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            return {"normal_response": content}

        def generate_ending_response(state: State):
            """Generate a closing reply based on resolved ending evaluation."""
            ending = self._resolve_ending_evaluation(state)
            system_prompt = self._build_ending_system_prompt(state, ending)
            response = self.llm.invoke(
                [SystemMessage(content=system_prompt), *state["messages"]]
            )
            content = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            return {
                "ending_response": content,
                "ending_evaluation": ending,
            }

        def route_after_goals(state: State) -> str:
            """Route to generate an ending response if all goals are achieved."""
            goals_evaluation = state.get("goals_evaluation")
            if goals_evaluation and goals_evaluation.all_goals_achieved:
                return "generate_ending_response"
            return "generate_normal_response"

        def route_after_ending(state: State) -> str:
            """Route to ending response for profanity, exhaustion, or repeated irrelevance."""
            ending_evaluation = state.get("llm_ending_evaluation")
            irrelevant_limit_reached = (
                state.get("irrelevant_message_count", 0) >= IRRELEVANT_MESSAGE_LIMIT
            )
            if ending_evaluation and (
                ending_evaluation.learner_used_profanity
                or ending_evaluation.conversation_exhausted
                or irrelevant_limit_reached
            ):
                return "generate_ending_response"
            return "generate_normal_response"

        builder = StateGraph(State)
        builder.add_node("evaluate_goals", evaluate_goals)
        builder.add_node("evaluate_ending", evaluate_ending)
        builder.add_node("generate_normal_response", generate_normal_response)
        builder.add_node("generate_ending_response", generate_ending_response)

        builder.add_edge(START, "evaluate_goals")
        builder.add_edge(START, "evaluate_ending")
        builder.add_conditional_edges(
            "evaluate_goals",
            route_after_goals,
            ["generate_ending_response", "generate_normal_response"],
        )
        builder.add_conditional_edges(
            "evaluate_ending",
            route_after_ending,
            ["generate_ending_response", "generate_normal_response"],
        )
        builder.add_edge("generate_normal_response", END)
        builder.add_edge("generate_ending_response", END)
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
                "irrelevant_message_count": 0,
            }
        )

        evaluation = result.get("ending_evaluation")
        if not isinstance(evaluation, EndingEvaluation):
            evaluation = self._resolve_ending_evaluation(result)

        if evaluation.should_end:
            ai_response = result.get("ending_response") or result.get("normal_response", "")
        else:
            ai_response = result.get("normal_response") or result.get("ending_response", "")

        return RoleplayResponse(
            ai_character_name=request.ai_character_name,
            ai_response=ai_response,
            should_end=evaluation.should_end,
            ending_condition=evaluation.ending_condition,
            ending_rationale=evaluation.rationale,
        )

    @staticmethod
    def _resolve_ending_evaluation(state: State) -> EndingEvaluation:
        goals = state.get("goals_evaluation")
        ending = state.get("llm_ending_evaluation")
        goals_achieved = bool(goals and goals.all_goals_achieved)
        learner_used_profanity = bool(ending and ending.learner_used_profanity)
        conversation_exhausted = bool(ending and ending.conversation_exhausted)
        learner_message_irrelevant = bool(
            ending and ending.learner_message_irrelevant
        )
        irrelevant_limit_reached = (
            state.get("irrelevant_message_count", 0) >= IRRELEVANT_MESSAGE_LIMIT
        )
        should_end = (
            goals_achieved
            or learner_used_profanity
            or conversation_exhausted
            or irrelevant_limit_reached
        )

        ending_condition: EndingCondition = "none"
        if learner_used_profanity:
            ending_condition = "profanity"
        elif goals_achieved:
            ending_condition = "goals_achieved"
        elif irrelevant_limit_reached:
            ending_condition = "irrelevant"
        elif conversation_exhausted:
            ending_condition = "conversation_exhausted"

        rationale_parts: list[str] = []
        if ending and ending.rationale:
            rationale_parts.append(ending.rationale)
        if goals and goals.rationale:
            rationale_parts.append(goals.rationale)
        if irrelevant_limit_reached:
            rationale_parts.append(
                f"Learner sent {IRRELEVANT_MESSAGE_LIMIT} irrelevant messages."
            )

        return EndingEvaluation(
            goals_achieved=goals_achieved,
            learner_used_profanity=learner_used_profanity,
            conversation_exhausted=conversation_exhausted,
            learner_message_irrelevant=learner_message_irrelevant,
            should_end=should_end,
            ending_condition=ending_condition,
            rationale=" ".join(rationale_parts),
        )

    @staticmethod
    def _shared_prompt_args(state: State) -> dict[str, str]:
        return {
            "ai_character_name": state["ai_character_name"],
            "ai_character_role": state["ai_character_role"],
            "ai_character_personality": state["ai_character_personality"],
            "scenario": state["scenario"],
            "learner_role": state["learner_role"],
            "goals": RoleplayService._format_goals(learner_goals=state["learner_goals"]),
        }

    @classmethod
    def _build_normal_system_prompt(cls, state: State) -> str:
        return PromptTemplate.from_template(
            ROLEPLAY_SYSTEM_PROMPT,
            template_format="jinja2",
        ).format(**cls._shared_prompt_args(state))

    @classmethod
    def _build_ending_system_prompt(cls, state: State, ending: EndingEvaluation) -> str:
        return PromptTemplate.from_template(
            ROLEPLAY_ENDING_SYSTEM_PROMPT,
            template_format="jinja2",
        ).format(
            **cls._shared_prompt_args(state),
            ending_condition=ending.ending_condition,
            ending_rationale=ending.rationale,
        )

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
