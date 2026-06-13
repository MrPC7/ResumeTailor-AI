"use client";

import { useCallback, useState } from "react";
import type {
  JDStepData,
  OptimizeResult,
  UploadStepData,
  WorkflowStep,
} from "@/features/workflow/types/workflow.types";

type WorkflowState = {
  step: WorkflowStep;
  uploadData: UploadStepData | null;
  jdData: JDStepData | null;
  optimizeResult: OptimizeResult | null;
};

const INITIAL: WorkflowState = {
  step: "upload",
  uploadData: null,
  jdData: null,
  optimizeResult: null,
};

export function useWorkflow() {
  const [state, setState] = useState<WorkflowState>(INITIAL);

  const completeUpload = useCallback((data: UploadStepData) => {
    setState((prev) => ({ ...prev, step: "jd", uploadData: data }));
  }, []);

  const completeJD = useCallback((data: JDStepData) => {
    setState((prev) => ({ ...prev, step: "optimize", jdData: data }));
  }, []);

  const completeOptimize = useCallback((result: OptimizeResult) => {
    setState((prev) => ({ ...prev, step: "download", optimizeResult: result }));
  }, []);

  const reset = useCallback(() => {
    setState(INITIAL);
  }, []);

  return { ...state, completeUpload, completeJD, completeOptimize, reset };
}
