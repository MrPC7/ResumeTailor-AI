import { UploadResume } from "@/features/resume-upload/components/UploadResume";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 sm:px-6 lg:px-8">
      <section className="mx-auto w-full max-w-3xl space-y-6">
        <header className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">ResumeTailor AI</h1>
          <p className="text-sm text-slate-600">
            Upload your resume securely. Supported formats are PDF and DOCX with a maximum size of
            10MB.
          </p>
        </header>
        <UploadResume />
      </section>
    </main>
  );
}
