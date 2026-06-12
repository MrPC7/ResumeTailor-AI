"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ResumeDiffViewer } from "@/features/resume-diff/components/ResumeDiffViewer";
import type {
  AnalysisResult,
  AnalyzedJD,
  StructuredResume,
} from "@/features/workflow/types/workflow.types";
import { cn } from "@/lib/utils";

type Props = {
  resume: StructuredResume;
  analyzedJD: AnalyzedJD;
  analysisResult: AnalysisResult;
  onContinue: () => void;
  onReset: () => void;
};

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-600";
  if (score >= 60) return "text-amber-600";
  return "text-red-600";
}

function scoreLabel(score: number): string {
  if (score >= 80) return "Strong Match";
  if (score >= 60) return "Good Match";
  if (score >= 40) return "Fair Match";
  return "Needs Work";
}

function ScoreArc({ score }: { score: number }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444";

  return (
    <div className="relative flex items-center justify-center">
      <svg className="-rotate-90" width="140" height="140">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="10" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className={cn("text-4xl font-bold tabular-nums", scoreColor(score))}>{score}</span>
        <span className="text-xs text-slate-500">/ 100</span>
      </div>
    </div>
  );
}

function SubScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-600">{label}</span>
        <span className={cn("font-medium tabular-nums", scoreColor(value))}>{value}%</span>
      </div>
      <Progress value={value} className="h-1.5" />
    </div>
  );
}

function ResumeView({ resume }: { resume: StructuredResume }) {
  return (
    <div className="space-y-5 text-sm">
      {/* Contact */}
      <div>
        <h3 className="text-base font-semibold text-slate-900">{resume.name ?? "—"}</h3>
        <p className="mt-0.5 text-xs text-slate-500">
          {[resume.email, resume.phone].filter(Boolean).join(" · ")}
        </p>
      </div>

      {resume.summary && (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Summary
          </p>
          <p className="leading-relaxed text-slate-700">{resume.summary}</p>
        </div>
      )}

      {resume.skills.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Skills
          </p>
          <div className="flex flex-wrap gap-1.5">
            {resume.skills.map((skill) => (
              <Badge key={skill} variant="secondary" className="text-xs">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {resume.experience.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Experience</p>
          {resume.experience.map((exp, i) => (
            <div key={i} className="space-y-0.5">
              <p className="font-medium text-slate-900">{exp.position}</p>
              <p className="text-xs text-slate-500">
                {exp.company} · {exp.duration}
              </p>
              <p className="leading-relaxed text-slate-600">{exp.description}</p>
            </div>
          ))}
        </div>
      )}

      {resume.education.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Education</p>
          {resume.education.map((edu, i) => (
            <div key={i}>
              <p className="font-medium text-slate-900">{edu.degree}</p>
              <p className="text-xs text-slate-500">
                {edu.institution} · {edu.year}
              </p>
            </div>
          ))}
        </div>
      )}

      {resume.projects.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Projects</p>
          {resume.projects.map((proj, i) => (
            <div key={i} className="space-y-1">
              <p className="font-medium text-slate-900">{proj.name}</p>
              <p className="leading-relaxed text-slate-600">{proj.description}</p>
              <div className="flex flex-wrap gap-1">
                {proj.technologies.map((t) => (
                  <Badge key={t} variant="outline" className="text-xs">
                    {t}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function StepPreview({ analysisResult, onContinue, onReset }: Props) {
  const { matchScore, gapAnalysis, customizedResume, suggestions, diff } = analysisResult;

  return (
    <div className="space-y-6">
      <Tabs defaultValue="score">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="score">Score</TabsTrigger>
          <TabsTrigger value="gaps">Gaps</TabsTrigger>
          <TabsTrigger value="resume">Resume</TabsTrigger>
          <TabsTrigger value="changes">Changes</TabsTrigger>
        </TabsList>

        {/* Score tab */}
        <TabsContent value="score">
          <Card>
            <CardContent className="space-y-6 pt-6">
              <div className="flex flex-col items-center gap-2">
                <ScoreArc score={matchScore.score} />
                <p className={cn("text-base font-semibold", scoreColor(matchScore.score))}>
                  {scoreLabel(matchScore.score)}
                </p>
                <p className="max-w-xs text-center text-xs text-slate-500">
                  Your resume&apos;s ATS match score against this job description
                </p>
              </div>
              <Separator />
              <div className="space-y-3">
                <SubScoreBar label="Skill Match" value={matchScore.skillScore} />
                <SubScoreBar label="Keyword Alignment" value={matchScore.keywordScore} />
                <SubScoreBar label="Experience Level" value={matchScore.experienceScore} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Gaps tab */}
        <TabsContent value="gaps">
          <Card>
            <CardContent className="space-y-5 pt-6">
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Matched Skills ({gapAnalysis.matchedSkills.length})
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {gapAnalysis.matchedSkills.map((s) => (
                      <Badge
                        key={s}
                        className="bg-emerald-100 text-xs text-emerald-800 hover:bg-emerald-100"
                      >
                        {s}
                      </Badge>
                    ))}
                    {gapAnalysis.matchedSkills.length === 0 && (
                      <p className="text-xs text-slate-400">None found</p>
                    )}
                  </div>
                </div>
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Missing Skills ({gapAnalysis.missingSkills.length})
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {gapAnalysis.missingSkills.map((s) => (
                      <Badge key={s} className="bg-red-100 text-xs text-red-800 hover:bg-red-100">
                        {s}
                      </Badge>
                    ))}
                    {gapAnalysis.missingSkills.length === 0 && (
                      <p className="text-xs text-emerald-600">No gaps &#8212; great match!</p>
                    )}
                  </div>
                </div>
              </div>

              {(gapAnalysis.recommendations.length > 0 || suggestions.length > 0) && (
                <>
                  <Separator />
                  <div>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Recommendations
                    </p>
                    <ul className="space-y-2">
                      {[...gapAnalysis.recommendations, ...suggestions].map((rec, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Resume tab */}
        <TabsContent value="resume">
          <Card>
            <CardContent className="pt-6">
              <ResumeView resume={customizedResume} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Changes tab */}
        <TabsContent value="changes">
          <Card>
            <CardContent className="pt-6">
              <ResumeDiffViewer diff={diff} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Navigation */}
      <div className="flex items-center justify-between gap-3">
        <Button variant="ghost" size="sm" onClick={onReset}>
          ← Start Over
        </Button>
        <Button onClick={onContinue}>Proceed to Download →</Button>
      </div>
    </div>
  );
}
