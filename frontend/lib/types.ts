export type ConversationMessage = {
  role: "learner" | "ai_character";
  content: string;
};

export type RoleplayRequest = {
  scenario: string;
  learner_goals: string[];
  learner_role: string;
  learner_message: string;
  ai_character_name: string;
  ai_character_role: string;
  ai_character_personality: string;
  conversation_history: ConversationMessage[];
};

export type EndingCondition =
  | "goals_achieved"
  | "profanity"
  | "conversation_exhausted"
  | "none";

export type RoleplayResponse = {
  ai_character_name: string;
  ai_response: string;
  should_end: boolean;
  ending_condition: EndingCondition;
  ending_rationale: string;
};

export type ChatMessage = {
  id: string;
  role: "learner" | "ai_character";
  content: string;
};
