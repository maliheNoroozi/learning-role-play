import type { ChangeEvent, RefObject, SubmitEvent, KeyboardEvent } from "react";
import { CircleArrowUp } from "lucide-react";
import { DEFAULT_ROLEPLAY } from "@/lib/roleplay-defaults";
import { Button, Textarea } from "@/components/ui";

type ChatFormProps = {
  input: string;
  isLoading: boolean;
  error: string | null;
  isEmpty: boolean;
  inputRef: RefObject<HTMLTextAreaElement | null>;
  onChange: (event: ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: (event: SubmitEvent<HTMLFormElement>) => Promise<void>;
};

export default function ChatForm({
  input,
  isLoading,
  error,
  isEmpty,
  inputRef,
  onChange,
  onSubmit,
}: ChatFormProps) {
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Enter" || event.shiftKey) return;

    event.preventDefault();
    event.currentTarget.form?.requestSubmit();
  };

  return (
    <div className="mx-auto max-w-3xl">
      {isEmpty ? (
        <div className="mb-6 rounded-2xl bg-card px-6 py-10 text-center">
          <h1 className="inline-flex min-h-10.5 items-baseline text-3xl font-semibold whitespace-pre-wrap">
            Start the conversation
          </h1>
          <p className="mt-2 text-base font-normal text-muted-foreground">
            You are playing {DEFAULT_ROLEPLAY.learner_role.toLowerCase()}. Send
            a message to begin.
          </p>
        </div>
      ) : null}
      <form onSubmit={onSubmit} className="flex items-end gap-3">
        <div className="relative flex w-full items-center gap-2">
          <Textarea
            ref={inputRef}
            rows={4}
            placeholder="Type your message..."
            className="min-h-12 w-full resize-none pr-12"
            value={input}
            onChange={onChange}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />
          <Button
            type="submit"
            variant="ghost"
            size="icon-sm"
            aria-label="Send message"
            className="absolute right-2 bottom-2 cursor-pointer rounded-full text-muted-foreground"
            disabled={isLoading || input.trim().length === 0}
          >
            <CircleArrowUp className="size-6" />
          </Button>
        </div>
      </form>
      {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
