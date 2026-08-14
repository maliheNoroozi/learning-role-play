import { z } from "zod";
import type { RoleplaySetup } from "@/lib/types";

const requiredText = (label: string) =>
  z
    .string()
    .trim()
    .min(1, `${label} is required.`);

export const roleplayFormSchema = z.object({
  scenario: requiredText("Scenario"),
  learner_role: requiredText("Your role"),
  learner_goals: z
    .array(requiredText("Goal"))
    .min(1, "Add at least one learner goal."),
  ai_character_name: requiredText("AI character name"),
  ai_character_role: requiredText("AI character role"),
  ai_character_personality: requiredText("AI character personality"),
});

export type RoleplayFormValues = z.infer<typeof roleplayFormSchema>;

export const EMPTY_ROLEPLAY_FORM_VALUES: RoleplayFormValues = {
  scenario: "",
  learner_role: "",
  learner_goals: [],
  ai_character_name: "",
  ai_character_role: "",
  ai_character_personality: "",
};

export type RoleplayFormState = {
  errors?: Partial<Record<keyof RoleplayFormValues, string[]>>;
  message?: string;
  roleplayId?: string;
  setup?: RoleplaySetup;
};

export const INITIAL_ROLEPLAY_FORM_STATE: RoleplayFormState = {};
