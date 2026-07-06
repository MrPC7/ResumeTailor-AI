import { create } from "zustand";
import type {
  CoverLetterData,
  JDStepData,
  PreviewStepData,
  RecruiterStepData,
  SuggestionsStepData,
  UploadStepData,
  WorkflowStep,
} from "@/features/workflow/types/workflow.types";

// ── Step ordering ─────────────────────────────────────────────────────────

export const STEP_ORDER: WorkflowStep[] = [
  "upload",
  "jd",
  "recruiter",
  "suggestions",
  "preview",
  "download",
];

// ── Dependency graph ─────────────────────────────────────────────────────

const DOWNSTREAM: Record<WorkflowStep, WorkflowStep[]> = {
  upload: ["recruiter", "suggestions", "preview", "download"],
  jd: ["recruiter", "suggestions", "preview", "download"],
  recruiter: ["suggestions", "preview", "download"],
  suggestions: ["preview", "download"],
  preview: ["download"],
  download: [],
};

// ── Store shape ───────────────────────────────────────────────────────────

type State = {
  currentStep: WorkflowStep;
  completedSteps: WorkflowStep[];
  uploadData: UploadStepData | null;
  jdData: JDStepData | null;
  recruiterData: RecruiterStepData | null;
  suggestionsData: SuggestionsStepData | null;
  previewData: PreviewStepData | null;
  coverLetter: CoverLetterData | null;
};

type Actions = {
  canNavigateTo: (step: WorkflowStep) => boolean;
  isCompleted: (step: WorkflowStep) => boolean;
  navigateTo: (step: WorkflowStep) => void;
  goPrev: () => void;

  completeUpload: (data: UploadStepData) => void;
  completeJD: (data: JDStepData) => void;
  completeRecruiter: (data: RecruiterStepData) => void;
  setSuggestionsData: (data: SuggestionsStepData) => void;
  completeSuggestions: (data: SuggestionsStepData) => void;
  toggleSuggestion: (id: string) => void;

  completePreview: (data: PreviewStepData) => void;

  setCoverLetter: (data: CoverLetterData) => void;
  clearCoverLetter: () => void;

  reset: () => void;
};

export type WorkflowStore = State & Actions;

// ── Helpers ───────────────────────────────────────────────────────────────

function prevStep(current: WorkflowStep): WorkflowStep {
  const idx = STEP_ORDER.indexOf(current);
  return STEP_ORDER[Math.max(idx - 1, 0)];
}

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
  recruiterData: null,
  suggestionsData: null,
  previewData: null,
  coverLetter: null,
};

// ── Store ─────────────────────────────────────────────────────────────────

const WORKFLOW_STATE_MACHINE: Record<WorkflowStep, { canEnter: (state: State) => boolean }> = {
  upload: { canEnter: () => true },
  jd: { canEnter: (state) => state.uploadData !== null },
  recruiter: { canEnter: (state) => state.uploadData !== null && state.jdData !== null },
  suggestions: { canEnter: (state) => state.recruiterData !== null },
  preview: { canEnter: (state) => state.previewData !== null },
  download: { canEnter: (state) => state.previewData !== null },
};

export const useWorkflowStore = create<WorkflowStore>()((set, get) => ({
  ...INITIAL_STATE,

  canNavigateTo: (step) => WORKFLOW_STATE_MACHINE[step].canEnter(get()),

  isCompleted: (step) => get().completedSteps.includes(step),

  navigateTo: (step) => {
    if (!get().canNavigateTo(step)) return;
    set({ currentStep: step });
  },

  goPrev: () => set((s) => ({ currentStep: prevStep(s.currentStep) })),

  completeUpload: (data) =>
    set((s) => ({
      uploadData: data,
      recruiterData: null,
      suggestionsData: null,
      previewData: null,
      coverLetter: null,
      completedSteps: advanceCompleted(s.completedSteps, "upload"),
    })),

  completeJD: (data) =>
    set((s) => ({
      jdData: data,
      recruiterData: null,
      suggestionsData: null,
      previewData: null,
      coverLetter: null,
      completedSteps: advanceCompleted(s.completedSteps, "jd"),
    })),

  completeRecruiter: (data) =>
    set((s) => ({
      recruiterData: data,
      suggestionsData: null,
      previewData: null,
      coverLetter: null,
      completedSteps: advanceCompleted(s.completedSteps, "recruiter"),
    })),

  setSuggestionsData: (data) =>
    set((s) => ({
      suggestionsData: data,
      previewData: null,
      coverLetter: null,
      completedSteps: s.completedSteps.filter(
        (step) => step !== "suggestions" && step !== "preview" && step !== "download"
      ),
    })),

  completeSuggestions: (data) =>
    set((s) => ({
      suggestionsData: data,
      previewData: null,
      coverLetter: null,
      completedSteps: advanceCompleted(s.completedSteps, "suggestions"),
    })),

  toggleSuggestion: (id) =>
    set((s) => {
      if (!s.suggestionsData) return {};
      return {
        suggestionsData: {
          ...s.suggestionsData,
          selectedSuggestions: {
            ...s.suggestionsData.selectedSuggestions,
            [id]: !s.suggestionsData.selectedSuggestions[id],
          },
        },
        previewData: null,
        coverLetter: null,
        completedSteps: s.completedSteps.filter(
          (step) => step !== "suggestions" && step !== "preview" && step !== "download"
        ),
      };
    }),

  completePreview: (data) =>
    set((s) => ({
      previewData: data,
      completedSteps: advanceCompleted(s.completedSteps, "preview"),
    })),

  setCoverLetter: (data) => set({ coverLetter: data }),
  clearCoverLetter: () => set({ coverLetter: null }),

  reset: () => set(INITIAL_STATE),
}));
