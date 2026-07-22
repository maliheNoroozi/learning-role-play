export type ConversationTurn = {
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
  conversation_history: ConversationTurn[];
};

export type RoleplayResponse = {
  ai_character_name: string;
  ai_response: string;
};

export type ChatMessage = {
  id: string;
  role: "learner" | "ai_character";
  content: string;
};
