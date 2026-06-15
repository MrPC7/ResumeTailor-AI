"use client";

/**
 * Thin re-export facade kept for backward compatibility.
 * New code should import directly from the Zustand store:
 *   import { useWorkflowStore } from "@/features/workflow/store/workflow.store"
 */
export { useWorkflowStore as useWorkflow } from "@/features/workflow/store/workflow.store";
