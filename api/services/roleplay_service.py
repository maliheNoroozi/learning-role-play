import os
from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from api.schemas.roleplay_schemas import ConversationTurn, RoleplayRequest, RoleplayResponse
from api.services.config import CHATGPT_MODEL, CHATGPT_TEMPERATURE
from api.services.prompts import ROLEPLAY_SYSTEM_PROMPT


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

    def get_chain(self, prompt: str, model: str):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", prompt),
                MessagesPlaceholder(variable_name="conversation_history"),
                ("human", "{learner_message}"),
            ],
            template_format="jinja2",
        )
        llm = self.llm if model == CHATGPT_MODEL else ChatOpenAI(
            model=model,
            temperature=CHATGPT_TEMPERATURE,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        return prompt_template | llm

    def generate_response(self, request: RoleplayRequest) -> RoleplayResponse:
        goals = "\n".join(f"- {goal}" for goal in request.learner_goals)
        chain = self.get_chain(ROLEPLAY_SYSTEM_PROMPT, CHATGPT_MODEL)

        response = chain.invoke(
            {
                "ai_character_name": request.ai_character_name,
                "ai_character_role": request.ai_character_role,
                "ai_character_personality": request.ai_character_personality,
                "scenario": request.scenario,
                "learner_role": request.learner_role,
                "goals": goals,
                "conversation_history": self._to_langchain_messages(
                    request.conversation_history
                ),
                "learner_message": request.learner_message,
            }
        )

        ai_response = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )

        return RoleplayResponse(
            ai_character_name=request.ai_character_name,
            ai_response=ai_response,
        )

    @staticmethod
    def _to_langchain_messages(history: list[ConversationTurn]) -> list[HumanMessage | AIMessage]:
        messages: list[HumanMessage | AIMessage] = []
        for turn in history:
            if turn.role == "learner":
                messages.append(HumanMessage(content=turn.content))
            else:
                messages.append(AIMessage(content=turn.content))
        return messages
