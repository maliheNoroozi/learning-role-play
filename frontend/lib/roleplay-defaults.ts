import type { RoleplaySetup } from "@/lib/types";
import type { RoleplayFormValues } from "@/lib/roleplay-schema";

/** Example values users can optionally load into the setup form. */
export const EXAMPLE_ROLEPLAY: RoleplaySetup = {
  scenario:
    "You are at a car dealership negotiating the price of a used sedan.",
  learner_goals: ["Negotiate a fair price", "Ask about warranty options"],
  learner_role: "A first-time car buyer",
  ai_character_name: "Alex",
  ai_character_role: "Experienced car salesperson",
  ai_character_personality:
    "Friendly but persuasive, focused on closing the deal.",
};

export function toRoleplayFormValues(setup: RoleplaySetup): RoleplayFormValues {
  return {
    scenario: setup.scenario,
    learner_role: setup.learner_role,
    learner_goals: [...setup.learner_goals],
    ai_character_name: setup.ai_character_name,
    ai_character_role: setup.ai_character_role,
    ai_character_personality: setup.ai_character_personality,
  };
}
