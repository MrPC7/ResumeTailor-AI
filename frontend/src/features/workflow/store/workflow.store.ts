import { create } from "zustand";
import type {
  CoverLetterData,
  JDStepData,
  RecruiterStepData,
  UploadStepData,
  WorkflowStep,
} from "@/features/workflow/types/workflow.types";

// ── Step ordering ─────────────────────────────────────────────────────────

export const STEP_ORDER: WorkflowStep[] = ["upload", "jd", "recruiter", "preview", "download"];

// ── Dependency graph ─────────────────────────────────────────────────────

const DOWNSTREAM: Record<WorkflowStep, WorkflowStep[]> = {
  upload: ["recruiter", "preview", "download"],
  jd: ["recruiter", "preview", "download"],
  recruiter: ["preview", "download"],
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
  coverLetter: null,
};

// ── Store ─────────────────────────────────────────────────────────────────

export const useWorkflowStore = create<WorkflowStore>()((set, get) => ({
  ...INITIAL_STATE,

  canNavigateTo: (step) => {
    const { uploadData, jdData, recruiterData } = get();
    switch (step) {
      case "upload":
        return true;
      case "jd":
        return uploadData !== null;
      case "recruiter":
        return uploadData !== null && jdData !== null;
      case "preview":
        return recruiterData !== null;
      case "download":
        return recruiterData !== null;
    }
  },

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
      coverLetter: null,
      completedSteps: advanceCompleted(s.completedSteps, "upload"),
      currentStep: nextStep("upload"),
    })),

  completeJD: (data) =>
    set((s) => ({
      jdData: data,
      recruiterData: null,
      coverLetter: null,
      completedSteps: advanceCompleted(s.completedSteps, "jd"),
      currentStep: nextStep("jd"),
    })),

  completeRecruiter: (data) =>
    set((s) => ({
      recruiterData: data,
      coverLetter: null,
      completedSteps: advanceCompleted(s.completedSteps, "recruiter"),
      currentStep: nextStep("recruiter"),
    })),

  setCoverLetter: (data) => set({ coverLetter: data }),
  clearCoverLetter: () => set({ coverLetter: null }),

  reset: () => set(INITIAL_STATE),
}));
