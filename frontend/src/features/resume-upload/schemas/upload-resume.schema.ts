import { z } from "zod";

export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

const allowedMimeTypes = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
] as const;

const allowedExtensions = ["pdf", "docx"] as const;

const hasSupportedExtension = (fileName: string): boolean => {
  const extension = fileName.split(".").pop()?.toLowerCase();
  if (!extension) {
    return false;
  }
  return allowedExtensions.includes(extension as (typeof allowedExtensions)[number]);
};

export const uploadResumeSchema = z.object({
  file: z
    .instanceof(File, { message: "Please select a file." })
    .refine((file) => file.size <= MAX_FILE_SIZE_BYTES, {
      message: "File size must be 10MB or less.",
    })
    .refine((file) => allowedMimeTypes.includes(file.type as (typeof allowedMimeTypes)[number]), {
      message: "Only PDF and DOCX files are allowed.",
    })
    .refine((file) => hasSupportedExtension(file.name), {
      message: "Invalid file extension. Use .pdf or .docx.",
    }),
});

export type UploadResumeFormValues = z.infer<typeof uploadResumeSchema>;
