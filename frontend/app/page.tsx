import { RoleplayForm } from "@/components/Roleplay";

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
        <header className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">
            Set up a roleplay
          </h1>
          <p className="mt-2 text-base text-muted-foreground">
            Define the scenario, your role, goals, and the AI character. Then
            start chatting.
          </p>
        </header>

        <RoleplayForm
          submitLabel="Create roleplay"
          submittingLabel="Creating session…"
        />
      </div>
    </div>
  );
}
