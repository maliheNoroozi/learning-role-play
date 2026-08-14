import type { RoleplaySetup } from "@/lib/types";

const STORAGE_PREFIX = "roleplay-setup:";

export function saveRoleplaySetup(
  roleplayId: string,
  setup: RoleplaySetup,
): void {
  sessionStorage.setItem(
    `${STORAGE_PREFIX}${roleplayId}`,
    JSON.stringify(setup),
  );
}

export function loadRoleplaySetup(roleplayId: string): RoleplaySetup | null {
  const raw = sessionStorage.getItem(`${STORAGE_PREFIX}${roleplayId}`);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as RoleplaySetup;
  } catch {
    return null;
  }
}
