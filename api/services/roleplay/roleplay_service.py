import os
from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated
from uuid import uuid4

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict

from api.schemas.roleplay_schemas import (
    ConversationMessage,
    CreateRoleplayRequest,
    CreateRoleplayResponse,
    EndingCondition,
    EndingEvaluation,
    RawEndingEvaluation,
    RawGoalsEvaluation,
    RoleplayChatRequest,
    RoleplayChatResponse,
    RoleplaySession,
)
from api.services.roleplay.roleplay_store import get_roleplay_store
from api.services.config import (
    CHATGPT_MODEL,
    CHATGPT_TEMPERATURE,
    IRRELEVANT_MESSAGE_LIMIT,
)
from api.services.prompts import (
    ENDING_EVALUATION_PROMPT,
    GOALS_EVALUATION_PROMPT,
    ROLEPLAY_ENDING_SYSTEM_PROMPT,
    ROLEPLAY_SYSTEM_PROMPT,
)


class RoleplayEndedError(RuntimeError):
    """Raised when a learner tries to chat in an already-ended session."""


GENERATE_NODES = frozenset(
    {"generate_normal_response", "generate_ending_response"}
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
    all_goals_achieved: bool
    ending_evaluation: NotRequired[EndingEvaluation]
    ai_response: NotRequired[str]


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
        ).with_config({"tags": ["nostream"]})
        self.goals_evaluator_llm = evaluator_base.with_structured_output(
            RawGoalsEvaluation,
            method="json_schema",
            strict=True,
        )
        self.ending_evaluator_llm = evaluator_base.with_structured_output(
            RawEndingEvaluation,
            method="json_schema",
            strict=True,
        )
        self.graph = self._build_graph()
        self.store = get_roleplay_store()

    def create_roleplay(self, request: CreateRoleplayRequest) -> CreateRoleplayResponse:
        session = RoleplaySession(
            roleplay_id=str(uuid4()),
            **request.model_dump(),
        )
        self.store.save_session(session)
        return CreateRoleplayResponse(roleplay_id=session.roleplay_id)

    def evaluate_goals(self, state: State):
        """Ask the LLM whether learner goals are achieved; store all_goals_achieved."""
        prompt = PromptTemplate.from_template(
            GOALS_EVALUATION_PROMPT,
            template_format="jinja2",
        ).format(
            scenario=state["scenario"],
            learner_role=state["learner_role"],
            learner_goals=RoleplayService._format_goals(state["learner_goals"]),
            learner_messages=self._format_learner_messages(state["messages"]),
        )
        llm_evaluation = self.goals_evaluator_llm.invoke(
            [SystemMessage(content=prompt)]
        )
        all_goals_achieved = all(
            status.achieved for status in llm_evaluation.goal_statuses
        )
        return {"all_goals_achieved": all_goals_achieved}

    def evaluate_ending(self, state: State):
        """Evaluate non-goal ending conditions (profanity, exhaustion, irrelevance)."""
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
        llm_evaluation = self.ending_evaluator_llm.invoke(
            [SystemMessage(content=prompt)]
        )
        previous_count = state.get("irrelevant_message_count", 0)
        irrelevant_message_count = previous_count + (
            1 if llm_evaluation.learner_message_irrelevant else 0
        )
        ending_evaluation = RoleplayService._ending_from_non_goal(
            llm_evaluation,
            irrelevant_message_count=irrelevant_message_count,
        )
        return {
            "irrelevant_message_count": irrelevant_message_count,
            "ending_evaluation": ending_evaluation,
        }

    def resolve_evaluations(self, state: State):
        """Goals achieved takes priority — override ending_evaluation if all goals met."""
        if state.get("all_goals_achieved"):
            return {
                "ending_evaluation": RoleplayService._ending_from_goals(),
            }
        return {}

    def generate_normal_response(self, state: State):
        """Generate a normal in-character reply."""
        system_prompt = PromptTemplate.from_template(
            ROLEPLAY_SYSTEM_PROMPT,
            template_format="jinja2",
        ).format(**RoleplayService._shared_prompt_args(state))
        response = self.llm.invoke(
            [SystemMessage(content=system_prompt), *state["messages"]]
        )
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        return {"ai_response": content}

    def generate_ending_response(self, state: State):
        """Generate a closing reply for whatever ending reason triggered this node."""
        ending_evaluation = state["ending_evaluation"]
        system_prompt = PromptTemplate.from_template(
            ROLEPLAY_ENDING_SYSTEM_PROMPT,
            template_format="jinja2",
        ).format(
            **RoleplayService._shared_prompt_args(state),
            ending_condition=ending_evaluation.ending_condition,
            ending_rationale=ending_evaluation.rationale,
        )
        response = self.llm.invoke(
            [SystemMessage(content=system_prompt), *state["messages"]]
        )
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        return {"ai_response": content}

    def route_after_evaluation(self, state: State) -> str:
        ending_evaluation = state.get("ending_evaluation")
        if ending_evaluation and ending_evaluation.should_end:
            return "generate_ending_response"
        return "generate_normal_response"

    def _build_graph(self):
        builder = StateGraph(State)
        builder.add_node("evaluate_goals", self.evaluate_goals)
        builder.add_node("evaluate_ending", self.evaluate_ending)
        builder.add_node("resolve_evaluations", self.resolve_evaluations)
        builder.add_node("generate_normal_response", self.generate_normal_response)
        builder.add_node("generate_ending_response", self.generate_ending_response)

        builder.add_edge(START, "evaluate_goals")
        builder.add_edge(START, "evaluate_ending")
        builder.add_edge("evaluate_goals", "resolve_evaluations")
        builder.add_edge("evaluate_ending", "resolve_evaluations")
        builder.add_conditional_edges(
            "resolve_evaluations",
            self.route_after_evaluation,
            ["generate_ending_response", "generate_normal_response"],
        )
        builder.add_edge("generate_normal_response", END)
        builder.add_edge("generate_ending_response", END)
        return builder.compile()

    def generate_response_stream(
        self, request: RoleplayChatRequest
    ) -> Iterator[tuple[str, dict]]:
        """Stream AI tokens via LangGraph `messages` mode, then emit done."""
        with self.store.lock(request.roleplay_id):
            session = self.store.get_session(request.roleplay_id)
            if session.should_end:
                raise RoleplayEndedError(request.roleplay_id)

            messages = self._messages_for_turn(session, request.learner_message)
            ai_parts: list[str] = []
            final_state: State | dict | None = None

            for chunk in self.graph.stream(
                self._graph_input(session, messages),
                stream_mode=["messages", "values"],
                version="v2",
            ):
                if chunk["type"] == "messages":
                    message_chunk, metadata = chunk["data"]
                    if metadata.get("langgraph_node") not in GENERATE_NODES:
                        continue
                    text = RoleplayService._chunk_text(message_chunk)
                    if text:
                        ai_parts.append(text)
                        yield ("token", {"text": text})
                elif chunk["type"] == "values":
                    final_state = chunk["data"]

            if final_state is None:
                raise RuntimeError("Graph stream completed without a final state.")

            ai_response = "".join(ai_parts) or str(final_state.get("ai_response", ""))
            response = self._persist_turn(
                session,
                learner_message=request.learner_message,
                ai_response=ai_response,
                result=final_state,
            )
            yield ("done", response.model_dump())

    @staticmethod
    def _chunk_text(message_chunk: object) -> str:
        content = getattr(message_chunk, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                else:
                    text = getattr(block, "text", None)
                    if isinstance(text, str):
                        parts.append(text)
            return "".join(parts)
        return str(content) if content else ""

    @staticmethod
    def _messages_for_turn(
        session: RoleplaySession, learner_message: str
    ) -> list[HumanMessage | AIMessage]:
        messages = RoleplayService._to_langchain_messages(session.conversation_history)
        messages.append(HumanMessage(content=learner_message))
        return messages

    @staticmethod
    def _graph_input(
        session: RoleplaySession, messages: list[AnyMessage]
    ) -> State:
        return {
            "messages": messages,
            "scenario": session.scenario,
            "learner_role": session.learner_role,
            "learner_goals": session.learner_goals,
            "ai_character_name": session.ai_character_name,
            "ai_character_role": session.ai_character_role,
            "ai_character_personality": session.ai_character_personality,
            "irrelevant_message_count": session.irrelevant_message_count,
            "all_goals_achieved": False,
        }

    @staticmethod
    def _coerce_ending_evaluation(value: object) -> EndingEvaluation:
        if isinstance(value, EndingEvaluation):
            return value
        return EndingEvaluation(
            learner_used_profanity=False,
            conversation_exhausted=False,
            learner_message_irrelevant=False,
            rationale="",
            should_end=False,
            ending_condition="none",
        )

    def _persist_turn(
        self,
        session: RoleplaySession,
        *,
        learner_message: str,
        ai_response: str,
        result: State | dict,
    ) -> RoleplayChatResponse:
        ending_evaluation = self._coerce_ending_evaluation(
            result.get("ending_evaluation")
        )

        session.conversation_history.extend(
            [
                ConversationMessage(
                    role="learner",
                    content=learner_message,
                ),
                ConversationMessage(
                    role="ai_character",
                    content=ai_response,
                ),
            ]
        )
        session.irrelevant_message_count = int(
            result.get("irrelevant_message_count", session.irrelevant_message_count)
        )
        session.should_end = ending_evaluation.should_end
        self.store.save_session(session)

        return RoleplayChatResponse(
            roleplay_id=session.roleplay_id,
            ai_response=ai_response,
            should_end=ending_evaluation.should_end,
            ending_condition=ending_evaluation.ending_condition,
            ending_rationale=(
                ending_evaluation.rationale if ending_evaluation.should_end else None
            ),
        )

    @staticmethod
    def _ending_from_goals() -> EndingEvaluation:
        """Build an ending evaluation when all learner goals are achieved."""
        return EndingEvaluation(
            learner_used_profanity=False,
            conversation_exhausted=False,
            learner_message_irrelevant=False,
            rationale="All learner goals have been achieved.",
            should_end=True,
            ending_condition="goals_achieved",
        )

    @staticmethod
    def _ending_from_non_goal(
        raw: RawEndingEvaluation,
        *,
        irrelevant_message_count: int,
    ) -> EndingEvaluation:
        """Turn non-goal LLM signals into a should_end decision (goals not involved)."""
        irrelevant_limit_reached = irrelevant_message_count >= IRRELEVANT_MESSAGE_LIMIT
        should_end = (
            raw.learner_used_profanity
            or raw.conversation_exhausted
            or irrelevant_limit_reached
        )

        ending_condition: EndingCondition = "none"
        rationale = ""
        if raw.learner_used_profanity:
            ending_condition = "profanity"
            rationale = "Learner used profane or offensive language."
        elif irrelevant_limit_reached:
            ending_condition = "irrelevant"
            rationale = f"Learner sent {IRRELEVANT_MESSAGE_LIMIT} irrelevant messages."
        elif raw.conversation_exhausted:
            ending_condition = "conversation_exhausted"
            rationale = "The conversation has been exhausted."

        return EndingEvaluation(
            learner_used_profanity=raw.learner_used_profanity,
            conversation_exhausted=raw.conversation_exhausted,
            learner_message_irrelevant=raw.learner_message_irrelevant,
            rationale=rationale,
            should_end=should_end,
            ending_condition=ending_condition,
        )

    @staticmethod
    def _shared_prompt_args(state: State) -> dict[str, str]:
        return {
            "ai_character_name": state["ai_character_name"],
            "ai_character_role": state["ai_character_role"],
            "ai_character_personality": state["ai_character_personality"],
            "scenario": state["scenario"],
            "learner_role": state["learner_role"],
            "goals": RoleplayService._format_goals(state["learner_goals"]),
        }

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


@lru_cache
def get_roleplay_service() -> RoleplayService:
    return RoleplayService()