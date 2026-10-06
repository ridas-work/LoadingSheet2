import type { Role } from "./types";

export function homeForRole(role: Role | string): string {
  if (role === "batch_clerk") return "/batches";
  if (role === "dispatch_clerk") return "/dispatch";
  if (role === "loading_clerk") return "/loading";
  return "/orders";
}
