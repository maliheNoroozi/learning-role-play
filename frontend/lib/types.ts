import type { components } from "@/lib/openapi.generated";

export type ConversationMessage = components["schemas"]["ConversationMessage"];
export type RoleplayRequest = components["schemas"]["RoleplayRequest"];
export type RoleplayResponse = components["schemas"]["RoleplayResponse"];
export type EndingCondition = RoleplayResponse["ending_condition"];

export type ChatMessage = {
  id: string;
  role: ConversationMessage["role"];
  content: string;
};
