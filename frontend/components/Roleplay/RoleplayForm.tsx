"use client";

import { useActionState } from "react";
import { useRouter } from "next/navigation";
import { Button, Input, Textarea } from "@/components/ui";
import {
  RoleplayFormField,
  RoleplayFormGoalsField,
  fieldError,
} from "@/components/Roleplay";
import { createRoleplayAction } from "@/app/actions/roleplay";
import { saveRoleplaySetup } from "@/lib/session";
import { useRoleplayFormDefaults } from "@/hooks";
import {
  EXAMPLE_ROLEPLAY,
  toRoleplayFormValues,
} from "@/lib/roleplay-defaults";
import {
  EMPTY_ROLEPLAY_FORM_VALUES,
  INITIAL_ROLEPLAY_FORM_STATE,
  type RoleplayFormState,
} from "@/lib/roleplay-schema";

type RoleplayFormProps = {
  submitLabel?: string;
  submittingLabel?: string;
};

export default function RoleplayForm({
  submitLabel = "Save roleplay",
  submittingLabel = "Saving…",
}: RoleplayFormProps) {
  const router = useRouter();
  const { defaults, formKey, resetForm } = useRoleplayFormDefaults();
  const [state, formAction, pending] = useActionState(
    async (
      prevState: RoleplayFormState,
      formData: FormData,
    ): Promise<RoleplayFormState> => {
      const nextState = await createRoleplayAction(prevState, formData);

      if (nextState.roleplayId && nextState.setup) {
        saveRoleplaySetup(nextState.roleplayId, nextState.setup);
        router.push(`/roleplays/${nextState.roleplayId}/chat`);
      }

      return nextState;
    },
    INITIAL_ROLEPLAY_FORM_STATE,
  );

  return (
    <form key={formKey} action={formAction} className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          Leave blank and fill in your own, or load the example scenario.
        </p>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => resetForm(toRoleplayFormValues(EXAMPLE_ROLEPLAY))}
            disabled={pending}
          >
            Use example
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => resetForm(EMPTY_ROLEPLAY_FORM_VALUES)}
            disabled={pending}
          >
            Clear
          </Button>
        </div>
      </div>

      <RoleplayFormField
        id="scenario"
        label="Scenario"
        error={fieldError(state.errors, "scenario")}
      >
        {(control) => (
          <Textarea
            {...control}
            name="scenario"
            rows={3}
            defaultValue={defaults.scenario}
            placeholder={EXAMPLE_ROLEPLAY.scenario}
            required
            disabled={pending}
          />
        )}
      </RoleplayFormField>

      <RoleplayFormField
        id="learner_role"
        label="Your role"
        error={fieldError(state.errors, "learner_role")}
      >
        {(control) => (
          <Input
            {...control}
            name="learner_role"
            defaultValue={defaults.learner_role}
            placeholder={EXAMPLE_ROLEPLAY.learner_role}
            required
            disabled={pending}
          />
        )}
      </RoleplayFormField>

      <RoleplayFormGoalsField
        defaultGoals={defaults.learner_goals}
        error={fieldError(state.errors, "learner_goals")}
        disabled={pending}
      />

      <div className="grid gap-5 sm:grid-cols-2">
        <RoleplayFormField
          id="ai_character_name"
          label="AI character name"
          error={fieldError(state.errors, "ai_character_name")}
        >
          {(control) => (
            <Input
              {...control}
              name="ai_character_name"
              defaultValue={defaults.ai_character_name}
              placeholder={EXAMPLE_ROLEPLAY.ai_character_name}
              required
              disabled={pending}
            />
          )}
        </RoleplayFormField>

        <RoleplayFormField
          id="ai_character_role"
          label="AI character role"
          error={fieldError(state.errors, "ai_character_role")}
        >
          {(control) => (
            <Input
              {...control}
              name="ai_character_role"
              defaultValue={defaults.ai_character_role}
              placeholder={EXAMPLE_ROLEPLAY.ai_character_role}
              required
              disabled={pending}
            />
          )}
        </RoleplayFormField>
      </div>

      <RoleplayFormField
        id="ai_character_personality"
        label="AI character personality"
        error={fieldError(state.errors, "ai_character_personality")}
      >
        {(control) => (
          <Textarea
            {...control}
            name="ai_character_personality"
            rows={2}
            defaultValue={defaults.ai_character_personality}
            placeholder={EXAMPLE_ROLEPLAY.ai_character_personality}
            required
            disabled={pending}
          />
        )}
      </RoleplayFormField>

      {state.message ? (
        <p className="text-sm text-destructive" aria-live="polite">
          {state.message}
        </p>
      ) : null}

      <Button type="submit" size="lg" className="self-start" disabled={pending}>
        {pending ? submittingLabel : submitLabel}
      </Button>
    </form>
  );
}
