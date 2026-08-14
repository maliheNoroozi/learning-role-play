export type EndingCondition =
  | "goals_achieved"
  | "profanity"
  | "conversation_exhausted"
  | "irrelevant"
  | "none";

export type ConversationMessage = {
  role: "learner" | "ai_character";
  content: string;
};

export type RoleplaySetup = {
  scenario: string;
  learner_role: string;
  learner_goals: string[];
  ai_character_name: string;
  ai_character_role: string;
  ai_character_personality: string;
};

export type CreateRoleplayRequest = RoleplaySetup;

export type CreateRoleplayResponse = {
  roleplay_id: string;
};

export type RoleplayChatRequest = {
  roleplay_id: string;
  learner_message: string;
};

export type RoleplayChatResponse = {
  roleplay_id: string;
  ai_response: string;
  should_end: boolean;
  ending_condition: EndingCondition;
  ending_rationale: string | null;
};

export type ChatMessage = {
  id: string;
  role: ConversationMessage["role"];
  content: string;
};
