"use client";

import { useState } from "react";
import {
  EMPTY_ROLEPLAY_FORM_VALUES,
  type RoleplayFormValues,
} from "@/lib/roleplay-schema";

export default function useRoleplayFormDefaults() {
  const [defaults, setDefaults] = useState(EMPTY_ROLEPLAY_FORM_VALUES);
  const [formKey, setFormKey] = useState(0);

  const resetForm = (values: RoleplayFormValues) => {
    setDefaults(values);
    setFormKey((key) => key + 1);
  };

  return { defaults, formKey, resetForm };
}
