"use client";

import { useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";
import { Check, Pencil, Plus, Trash2, X } from "lucide-react";
import { Button, Input } from "@/components/ui";
import { createMessageId } from "@/lib/utils";

type GoalItem = {
  id: string;
  text: string;
};

type GoalsFieldProps = {
  goals: GoalItem[];
  onChange: (goals: GoalItem[]) => void;
};

export default function GoalsField({ goals, onChange }: GoalsFieldProps) {
  const [draft, setDraft] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState("");

  const addGoal = () => {
    const text = draft.trim();
    if (!text) return;

    onChange([...goals, { id: createMessageId(), text }]);
    setDraft("");
  };

  const handleDraftKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    addGoal();
  };

  const startEdit = (goal: GoalItem) => {
    setEditingId(goal.id);
    setEditDraft(goal.text);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditDraft("");
  };

  const saveEdit = () => {
    const text = editDraft.trim();
    if (!text || !editingId) return;

    onChange(
      goals.map((goal) => (goal.id === editingId ? { ...goal, text } : goal)),
    );
    cancelEdit();
  };

  const handleEditKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      saveEdit();
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      cancelEdit();
    }
  };

  const deleteGoal = (id: string) => {
    onChange(goals.filter((goal) => goal.id !== id));
    if (editingId === id) cancelEdit();
  };

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium">Your goals</span>

      <div className="relative flex items-center gap-2">
        <Input
          placeholder="Negotiate a fair price"
          value={draft}
          onChange={(event: ChangeEvent<HTMLInputElement>) =>
            setDraft(event.target.value)
          }
          onKeyDown={handleDraftKeyDown}
          aria-label="New goal"
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          aria-label="Add goal"
          className="shrink-0"
          onClick={addGoal}
          disabled={draft.trim().length === 0}
        >
          <Plus />
        </Button>
      </div>

      {goals.length > 0 ? (
        <ul className="mt-2 flex flex-col gap-2">
          {goals.map((goal) => {
            const isEditing = editingId === goal.id;

            return (
              <li
                key={goal.id}
                className="flex items-center gap-2 rounded-lg border border-border px-2.5 py-1.5"
              >
                {isEditing ? (
                  <>
                    <Input
                      value={editDraft}
                      onChange={(event: ChangeEvent<HTMLInputElement>) =>
                        setEditDraft(event.target.value)
                      }
                      onKeyDown={handleEditKeyDown}
                      aria-label="Edit goal"
                      className="h-8"
                      autoFocus
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Save goal"
                      onClick={saveEdit}
                      disabled={editDraft.trim().length === 0}
                    >
                      <Check />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Cancel edit"
                      onClick={cancelEdit}
                    >
                      <X />
                    </Button>
                  </>
                ) : (
                  <>
                    <span className="min-w-0 flex-1 text-sm leading-5">
                      {goal.text}
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Edit goal"
                      onClick={() => startEdit(goal)}
                    >
                      <Pencil />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Delete goal"
                      onClick={() => deleteGoal(goal.id)}
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
    </div>
  );
}

export type { GoalItem };
