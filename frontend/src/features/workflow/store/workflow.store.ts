import { create } from "zustand";
import type {
  ATSStepData,
  CoverLetterData,
  JDStepData,
  OptimizeResult,
  UploadStepData,
  WorkflowStep,
} from "@/features/workflow/types/workflow.types";

// ── Step ordering ─────────────────────────────────────────────────────────

export const STEP_ORDER: WorkflowStep[] = [
  "upload",
  "jd",
  "ats",
  "recommendations",
  "preview",
  "download",
];

// ── Dependency graph ─────────────────────────────────────────────────────
// Maps each step to the steps whose cached data should be cleared when
// that step's data is replaced (e.g. re-uploading a resume invalidates
// ATS results but not the stored job-description text).

const DOWNSTREAM: Record<WorkflowStep, WorkflowStep[]> = {
  upload: ["ats", "recommendations", "preview", "download"],
  jd: ["ats", "recommendations", "preview", "download"],
  ats: ["recommendations", "preview", "download"],
  recommendations: ["preview", "download"],
  preview: ["download"],
  download: [],
};

// ── Store shape ───────────────────────────────────────────────────────────

type State = {
  currentStep: WorkflowStep;
  /** Steps whose data has been successfully produced and not yet invalidated. */
  completedSteps: WorkflowStep[];
  uploadData: UploadStepData | null;
  jdData: JDStepData | null;
  atsStepData: ATSStepData | null;
  optimizeResult: OptimizeResult | null;
  coverLetter: CoverLetterData | null;
};

type Actions = {
  /** Returns true when the user has all prerequisites to visit `step`. */
  canNavigateTo: (step: WorkflowStep) => boolean;
  /** Returns true when the step is in the completed-steps list. */
  isCompleted: (step: WorkflowStep) => boolean;
  navigateTo: (step: WorkflowStep) => void;
  goPrev: () => void;

  completeUpload: (data: UploadStepData) => void;
  completeJD: (data: JDStepData) => void;
  completeATS: (data: ATSStepData) => void;
  /** Update recommendation selections without re-running analysis. */
  updateSelectedRecommendations: (selections: Record<string, boolean>) => void;
  completeRecommendations: (result: OptimizeResult) => void;
  completePreview: () => void;

  setCoverLetter: (data: CoverLetterData) => void;
  clearCoverLetter: () => void;

  reset: () => void;
};

export type WorkflowStore = State & Actions;

// ── Helpers ───────────────────────────────────────────────────────────────

function nextStep(current: WorkflowStep): WorkflowStep {
  const idx = STEP_ORDER.indexOf(current);
  return STEP_ORDER[Math.min(idx + 1, STEP_ORDER.length - 1)];
}

function prevStep(current: WorkflowStep): WorkflowStep {
  const idx = STEP_ORDER.indexOf(current);
  return STEP_ORDER[Math.max(idx - 1, 0)];
}

/**
 * Returns `completedSteps` with `completing` added and all its downstream
 * dependents removed.
 */
function advanceCompleted(current: WorkflowStep[], completing: WorkflowStep): WorkflowStep[] {
  const downstream = DOWNSTREAM[completing];
  const withoutDownstream = current.filter((s) => !downstream.includes(s));
  return withoutDownstream.includes(completing)
    ? withoutDownstream
    : [...withoutDownstream, completing];
}

const INITIAL_STATE: State = {
  currentStep: "upload",
  completedSteps: [],
  uploadData: null,
  jdData: null,
  atsStepData: null,
  optimizeResult: null,
  coverLetter: null,
};

// ── Store ─────────────────────────────────────────────────────────────────

export const useWorkflowStore = create<WorkflowStore>()((set, get) => ({
  ...INITIAL_STATE,

  // ── Query helpers ──────────────────────────────────────────────────────

  canNavigateTo: (step) => {
    const { uploadData, jdData, atsStepData, optimizeResult } = get();
    switch (step) {
      case "upload":
        return true;
      case "jd":
        return uploadData !== null;
      case "ats":
        return uploadData !== null && jdData !== null;
      case "recommendations":
        return uploadData !== null && jdData !== null && atsStepData !== null;
      case "preview":
        return optimizeResult !== null;
      case "download":
        return optimizeResult !== null;
    }
  },

  isCompleted: (step) => get().completedSteps.includes(step),

  // ── Navigation ─────────────────────────────────────────────────────────

  navigateTo: (step) => {
    if (!get().canNavigateTo(step)) return;
    set({ currentStep: step });
  },

  goPrev: () => set((s) => ({ currentStep: prevStep(s.currentStep) })),

  // ── Step completions ───────────────────────────────────────────────────

  completeUpload: (data) =>
    set((s) => ({
      uploadData: data,
      // Preserve jdData: JD analysis is independent of the resume file.
      // Invalidate atsStepData + optimizeResult as they depend on the resume.
      atsStepData: null,
      optimizeResult: null,
      coverLetter: null,
      completedSteps: advanceCompleted(s.completedSteps, "upload"),
      currentStep: nextStep("upload"),
    })),

  completeJD: (data) =>
    set((s) => ({
      jdData: data,
      atsStepData: null,
      optimizeResult: null,
      coverLetter: null,
      completedSteps: advanceCompleted(s.completedSteps, "jd"),
      currentStep: nextStep("jd"),
    })),

  completeATS: (data) =>
    set((s) => ({
      atsStepData: data,
      optimizeResult: null,
      coverLetter: null,
      completedSteps: advanceCompleted(s.completedSteps, "ats"),
      currentStep: nextStep("ats"),
    })),

  updateSelectedRecommendations: (selections) =>
    set((s) => {
      if (!s.atsStepData) return {};
      const downstream = DOWNSTREAM.recommendations;
      return {
        atsStepData: { ...s.atsStepData, selectedRecommendations: selections },
        // Clear cached optimization result so the next "Apply" re-runs.
        optimizeResult: null,
        completedSteps: s.completedSteps.filter((step) => !downstream.includes(step)),
      };
    }),

  completeRecommendations: (result) =>
    set((s) => ({
      optimizeResult: result,
      completedSteps: advanceCompleted(s.completedSteps, "recommendations"),
      currentStep: nextStep("recommendations"),
    })),

  completePreview: () =>
    set((s) => ({
      completedSteps: advanceCompleted(s.completedSteps, "preview"),
      currentStep: nextStep("preview"),
    })),

  setCoverLetter: (data) => set({ coverLetter: data }),
  clearCoverLetter: () => set({ coverLetter: null }),

  reset: () => set(INITIAL_STATE),
}));
