import type { ReactNode } from "react";
import type { RoleplayFormValues } from "@/lib/roleplay-schema";

type RoleplayFieldErrors = Partial<Record<keyof RoleplayFormValues, string[]>>;

export function fieldError(
  errors: RoleplayFieldErrors | undefined,
  field: keyof RoleplayFormValues,
) {
  return errors?.[field]?.[0];
}

type ControlProps = {
  id: string;
  "aria-invalid": boolean;
  "aria-describedby"?: string;
};

type RoleplayFormFieldProps = {
  id: string;
  label: string;
  error?: string;
  children: (control: ControlProps) => ReactNode;
};

export default function RoleplayFormField({
  id,
  label,
  error,
  children,
}: RoleplayFormFieldProps) {
  const errorId = `${id}-error`;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      {children({
        id,
        "aria-invalid": Boolean(error),
        "aria-describedby": error ? errorId : undefined,
      })}
      {error ? (
        <p id={errorId} className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
