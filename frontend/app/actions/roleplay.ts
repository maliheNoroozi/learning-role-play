"use server";

import { createRoleplay } from "@/lib/api";
import {
  roleplayFormSchema,
  type RoleplayFormState,
} from "@/lib/roleplay-schema";

export async function createRoleplayAction(
  _prevState: RoleplayFormState,
  formData: FormData,
): Promise<RoleplayFormState> {
  const validatedFields = roleplayFormSchema.safeParse({
    scenario: formData.get("scenario"),
    learner_role: formData.get("learner_role"),
    learner_goals: formData.getAll("learner_goals"),
    ai_character_name: formData.get("ai_character_name"),
    ai_character_role: formData.get("ai_character_role"),
    ai_character_personality: formData.get("ai_character_personality"),
  });

  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
    };
  }

  try {
    const newRoleplay = await createRoleplay(validatedFields.data);
    return {
      roleplayId: newRoleplay.roleplay_id,
      setup: validatedFields.data,
    };
  } catch (error) {
    return {
      message:
        error instanceof Error
          ? error.message
          : "Failed to create roleplay session.",
    };
  }
}
