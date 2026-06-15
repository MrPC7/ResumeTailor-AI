export type ToastType = "error" | "success" | "info";

export type ToastPayload = {
  type: ToastType;
  message: string;
};

export const APP_TOAST_EVENT = "resume-tailor-toast";

export function pushToast(payload: ToastPayload): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent<ToastPayload>(APP_TOAST_EVENT, { detail: payload }));
}
