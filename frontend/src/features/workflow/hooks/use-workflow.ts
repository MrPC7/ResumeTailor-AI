"use client";

import { useCallback, useState } from "react";
import type {
  AnalysisResult,
  JDStepData,
  UploadStepData,
  WorkflowStep,
} from "@/features/workflow/types/workflow.types";

type WorkflowState = {
  step: WorkflowStep;
  uploadData: UploadStepData | null;
  jdData: JDStepData | null;
  analysisResult: AnalysisResult | null;
};

const INITIAL: WorkflowState = {
  step: "upload",
  uploadData: null,
  jdData: null,
  analysisResult: null,
};

export function useWorkflow() {
  const [state, setState] = useState<WorkflowState>(INITIAL);

  const completeUpload = useCallback((data: UploadStepData) => {
    setState((prev) => ({ ...prev, step: "jd", uploadData: data }));
  }, []);

  const completeJD = useCallback((data: JDStepData) => {
    setState((prev) => ({ ...prev, step: "analyze", jdData: data }));
  }, []);

  const completeAnalysis = useCallback((result: AnalysisResult) => {
    setState((prev) => ({ ...prev, step: "preview", analysisResult: result }));
  }, []);

  const goToDownload = useCallback(() => {
    setState((prev) => ({ ...prev, step: "download" }));
  }, []);

  const reset = useCallback(() => {
    setState(INITIAL);
  }, []);

  return { ...state, completeUpload, completeJD, completeAnalysis, goToDownload, reset };
}
