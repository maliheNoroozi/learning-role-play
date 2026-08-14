"use client";

import { useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";
import { Check, Pencil, Plus, Trash2, X } from "lucide-react";
import { Button, Input } from "@/components/ui";

type GoalItem = {
  id: string;
  text: string;
};

type RoleplayGoalsFieldProps = {
  defaultGoals?: string[];
  error?: string;
  disabled?: boolean;
};

function createGoalId() {
  return crypto.randomUUID();
}

export default function RoleplayFormGoalsField({
  defaultGoals = [],
  error,
  disabled = false,
}: RoleplayGoalsFieldProps) {
  const [items, setItems] = useState<GoalItem[]>(() =>
    defaultGoals.map((text) => ({ id: createGoalId(), text })),
  );
  const [draft, setDraft] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState("");

  const addGoal = () => {
    const text = draft.trim();
    if (!text) return;

    setItems((current) => [...current, { id: createGoalId(), text }]);
    setDraft("");
  };

  const handleDraftKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    addGoal();
  };

  const startEdit = (id: string, text: string) => {
    setEditingId(id);
    setEditDraft(text);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditDraft("");
  };

  const saveEdit = (id: string) => {
    const text = editDraft.trim();
    if (!text) return;

    setItems((current) =>
      current.map((item) => (item.id === id ? { ...item, text } : item)),
    );
    cancelEdit();
  };

  const handleEditKeyDown = (
    event: KeyboardEvent<HTMLInputElement>,
    id: string,
  ) => {
    if (event.key === "Enter") {
      event.preventDefault();
      saveEdit(id);
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      cancelEdit();
    }
  };

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium">Your goals</span>

      {items.map((item) => (
        <input
          key={item.id}
          type="hidden"
          name="learner_goals"
          value={item.text}
        />
      ))}

      <div className="relative flex items-center gap-2">
        <Input
          placeholder="Negotiate a fair price"
          value={draft}
          onChange={(event: ChangeEvent<HTMLInputElement>) =>
            setDraft(event.target.value)
          }
          onKeyDown={handleDraftKeyDown}
          aria-label="New goal"
          aria-invalid={Boolean(error)}
          disabled={disabled}
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          aria-label="Add goal"
          className="shrink-0"
          onClick={addGoal}
          disabled={disabled || draft.trim().length === 0}
        >
          <Plus />
        </Button>
      </div>

      {items.length > 0 ? (
        <ul className="mt-2 flex flex-col gap-2">
          {items.map((item) => {
            const isEditing = editingId === item.id;

            return (
              <li
                key={item.id}
                className="flex items-center gap-2 rounded-lg border border-border px-2.5 py-1.5"
              >
                {isEditing ? (
                  <>
                    <Input
                      value={editDraft}
                      onChange={(event: ChangeEvent<HTMLInputElement>) =>
                        setEditDraft(event.target.value)
                      }
                      onKeyDown={(event) => handleEditKeyDown(event, item.id)}
                      aria-label="Edit goal"
                      className="h-8"
                      autoFocus
                      disabled={disabled}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Save goal"
                      onClick={() => saveEdit(item.id)}
                      disabled={disabled || editDraft.trim().length === 0}
                    >
                      <Check />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Cancel edit"
                      onClick={cancelEdit}
                      disabled={disabled}
                    >
                      <X />
                    </Button>
                  </>
                ) : (
                  <>
                    <span className="min-w-0 flex-1 text-sm leading-5">
                      {item.text}
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Edit goal"
                      onClick={() => startEdit(item.id, item.text)}
                      disabled={disabled}
                    >
                      <Pencil />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Delete goal"
                      onClick={() => {
                        setItems((current) =>
                          current.filter((goal) => goal.id !== item.id),
                        );
                        if (editingId === item.id) cancelEdit();
                      }}
                      disabled={disabled}
                    >
                      <Trash2 />
                    </Button>
                  </>
                )}
              </li>
            );
          })}
        </ul>
      ) : (
        <span className="mt-1 text-xs text-muted-foreground">
          Press Enter or click + to add a goal.
        </span>
      )}

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
