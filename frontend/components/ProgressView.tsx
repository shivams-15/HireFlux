'use client'

import { motion } from 'framer-motion'
import { Loader2, CheckCircle, Circle, AlertTriangle, Clock, Zap, FileText, Search, Shield, Users, BarChart3 } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'

interface ProgressViewProps {
  status: any
}

interface StepDef {
  key: string
  label: string
  icon: React.ReactNode
  description: string
  matchPhrases: string[]
  progressRange: [number, number]
}

const STEPS: StepDef[] = [
  {
    key: 'resume',
    label: 'Resume Analysis',
    icon: <FileText className="w-5 h-5" />,
    description: 'Extracting and analyzing resume data with AI',
    matchPhrases: ['resume', 'parsing', 'parse', 'analyzing resume', 'resume analysis', 'initializing'],
    progressRange: [0, 0.3],
  },
  {
    key: 'matching',
    label: 'Candidate Matching',
    icon: <Users className="w-5 h-5" />,
    description: 'Semantic matching of candidates to job requirements',
    matchPhrases: ['matching', 'match', 'job requirement', 'requirement'],
    progressRange: [0.25, 0.5],
  },
  {
    key: 'research',
    label: 'Deep Research',
    icon: <Search className="w-5 h-5" />,
    description: 'Cross-platform web research on top candidates',
    matchPhrases: ['research', 'researching', 'gathering data', 'platform'],
    progressRange: [0.45, 0.7],
  },
  {
    key: 'validation',
    label: 'Information Validation',
    icon: <Shield className="w-5 h-5" />,
    description: 'Multi-source verification of candidate claims',
    matchPhrases: ['validation', 'validating', 'verify'],
    progressRange: [0.65, 0.85],
  },
  {
    key: 'report',
    label: 'Report Generation',
    icon: <BarChart3 className="w-5 h-5" />,
    description: 'Compiling comprehensive evaluation reports',
    matchPhrases: ['report', 'summarization', 'generating', 'saving'],
    progressRange: [0.8, 1.0],
  },
]

export default function ProgressView({ status }: ProgressViewProps) {
  const [elapsed, setElapsed] = useState(0)
  const [smoothProgress, setSmoothProgress] = useState(0)
  const startTimeRef = useRef<number>(Date.now())
  const animFrameRef = useRef<number>(0)

  // ── Elapsed time ticker ──────────────────────────────────
  useEffect(() => {
    startTimeRef.current = Date.now()
    setElapsed(0)
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // ── Smooth progress animation ────────────────────────────
  useEffect(() => {
    const target = status?.progress || 0

    const animate = () => {
      setSmoothProgress((prev) => {
        const diff = target - prev
        if (Math.abs(diff) < 0.001) return target
        return prev + diff * 0.08
      })
      animFrameRef.current = requestAnimationFrame(animate)
    }

    animFrameRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animFrameRef.current)
  }, [status?.progress])

  // ── Step detection ───────────────────────────────────────
  const getCurrentStepIndex = (): number => {
    if (!status) return -1
    const stepName = (status.current_step || '').toLowerCase()

    for (let i = 0; i < STEPS.length; i++) {
      if (STEPS[i].matchPhrases.some((phrase) => stepName.includes(phrase))) {
        return i
      }
    }
    // Fallback: use progress range
    const prog = status.progress || 0
    for (let i = 0; i < STEPS.length; i++) {
      if (prog >= STEPS[i].progressRange[0] && prog <= STEPS[i].progressRange[1] + 0.05) {
        return i
      }
    }
    return 0
  }

  const currentStepIndex = getCurrentStepIndex()

  // ── Per-step sub-progress ────────────────────────────────
  const getStepSubProgress = (stepIndex: number): number => {
    const backendProg = status?.progress || 0
    const [rangeStart, rangeEnd] = STEPS[stepIndex].progressRange

    if (stepIndex < currentStepIndex) return 1
    if (stepIndex > currentStepIndex) return 0
    const raw = (backendProg - rangeStart) / (rangeEnd - rangeStart)
    return Math.max(0, Math.min(1, raw))
  }

  // ── Format time ──────────────────────────────────────────
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    if (mins > 0) return `${mins}m ${secs.toString().padStart(2, '0')}s`
    return `${secs}s`
  }

  // ── Estimate remaining ────────────────────────────────────
  const getEstimatedRemaining = (): string | null => {
    const prog = status?.progress || 0
    if (prog <= 0 || elapsed < 3) return null
    const totalEstimated = elapsed / prog
    const remaining = Math.max(0, totalEstimated - elapsed)
    return formatTime(Math.round(remaining))
  }

  const estimatedRemaining = getEstimatedRemaining()

  // ── Candidate count extraction ────────────────────────────
  const extractCount = (message: string): number | null => {
    const match = message?.match(/(\d+)\s+candidate/)
    return match ? parseInt(match[1], 10) : null
  }

  const candidateCount = extractCount(status?.message || '')

  // ── Loading / No status ──────────────────────────────────
  if (!status) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative">
          <Loader2 className="w-10 h-10 animate-spin text-primary-600" />
          <div className="absolute inset-0 w-10 h-10 rounded-full border-2 border-primary-200 animate-ping opacity-20" />
        </div>
        <p className="mt-6 text-neutral-500 font-medium text-sm">Initializing processing pipeline...</p>
      </div>
    )
  }

  // ── Error state ──────────────────────────────────────────
  if (status.status === 'failed') {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white border border-rose-200 rounded-2xl p-8 text-center shadow-sm">
          <div className="w-16 h-16 bg-rose-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-8 h-8 text-rose-600" />
          </div>
          <h2 className="text-xl font-bold text-neutral-900 mb-2">Processing Failed</h2>
          <p className="text-neutral-500 mb-6 max-w-md mx-auto">
            {status.message || 'An unexpected error occurred during the AI processing pipeline.'}
          </p>
          <button onClick={() => window.location.reload()} className="btn-primary inline-flex items-center gap-2">
            <Zap className="w-4 h-4" />
            <span>Try Again</span>
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white border border-neutral-200/80 rounded-2xl p-6 md:p-8 shadow-sm">
        {/* ── Header ──────────────────────────────────────── */}
        <div className="text-center mb-8">
          <div className="relative inline-flex items-center justify-center mb-5">
            <div className="w-16 h-16 rounded-2xl bg-primary-100 flex items-center justify-center">
              <Loader2 className="w-7 h-7 text-primary-600 animate-spin" />
            </div>
            <div className="absolute inset-0 w-16 h-16 rounded-2xl border-2 border-primary-300 animate-ping opacity-30" />
          </div>

          <h2 className="text-2xl font-extrabold text-neutral-900 mb-1.5">AI Processing Pipeline</h2>
          <p className="text-sm text-neutral-500 max-w-md mx-auto leading-relaxed">
            {status.message || status.current_step || 'Processing candidates...'}
          </p>

          {/* Timing + counts row */}
          <div className="flex items-center justify-center gap-4 mt-4 text-xs text-neutral-400 flex-wrap">
            <span className="inline-flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              Elapsed: {formatTime(elapsed)}
            </span>
            {estimatedRemaining && (
              <span className="inline-flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5" />
                Est. remaining: ~{estimatedRemaining}
              </span>
            )}
            {candidateCount && (
              <span className="inline-flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5" />
                {candidateCount} candidate{candidateCount !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>

        {/* ── Overall Progress Bar ────────────────────────── */}
        <div className="mb-8">
          <div className="flex justify-between items-center text-sm mb-3">
            <span className="font-semibold text-neutral-700">Overall Progress</span>
            <span className="text-base font-extrabold text-primary-700 tabular-nums">
              {Math.round(smoothProgress * 100)}%
            </span>
          </div>
          <div className="relative w-full h-3 bg-slate-100 rounded-full overflow-hidden">
            <motion.div
              className="absolute inset-0 h-full bg-gradient-to-r from-primary-500 via-primary-400 to-primary-600 rounded-full"
              initial={{ width: '0%' }}
              animate={{ width: `${smoothProgress * 100}%` }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
            />
            {/* Shimmer */}
            {smoothProgress > 0 && smoothProgress < 1 && (
              <motion.div
                className="absolute inset-0 h-full w-20 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                animate={{ left: ['-20%', '120%'] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
              />
            )}
          </div>
        </div>

        {/* ── Step Timeline ────────────────────────────────── */}
        <div className="space-y-1">
          {STEPS.map((step, index) => {
            const isComplete = index < currentStepIndex
            const isCurrent = index === currentStepIndex
            const isPending = index > currentStepIndex
            const subProgress = getStepSubProgress(index)

            return (
              <motion.div
                key={step.key}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.06 }}
                className="relative"
              >
                {/* Vertical connector line */}
                {index < STEPS.length - 1 && (
                  <div className="absolute left-[27px] top-12 bottom-0 w-0.5">
                    <div
                      className={`h-full rounded-full transition-colors duration-500 ${
                        isComplete ? 'bg-emerald-300' : 'bg-slate-200'
                      }`}
                    />
                  </div>
                )}

                <div
                  className={`flex items-start gap-4 p-3.5 rounded-xl transition-all duration-300 ${
                    isCurrent
                      ? 'bg-primary-50/70 border border-primary-200/60 shadow-sm'
                      : isComplete
                        ? 'bg-transparent'
                        : 'bg-transparent'
                  }`}
                >
                  {/* Step indicator */}
                  <div className="relative flex-shrink-0 mt-0.5">
                    <div
                      className={`w-[30px] h-[30px] rounded-full flex items-center justify-center transition-all duration-300 ${
                        isComplete
                          ? 'bg-emerald-100'
                          : isCurrent
                            ? 'bg-primary-100 ring-4 ring-primary-100/50'
                            : 'bg-slate-100'
                      }`}
                    >
                      {isComplete ? (
                        <CheckCircle className="w-4 h-4 text-emerald-600" />
                      ) : isCurrent ? (
                        <Loader2 className="w-4 h-4 text-primary-600 animate-spin" />
                      ) : (
                        <Circle className="w-4 h-4 text-slate-300" />
                      )}
                    </div>

                    {/* Sub-progress ring for current step */}
                    {isCurrent && (
                      <svg className="absolute -inset-1 w-[38px] h-[38px] -rotate-90">
                        <circle cx="19" cy="19" r="17" className="fill-none stroke-primary-300/40" strokeWidth="2" />
                        <circle
                          cx="19" cy="19" r="17"
                          className="fill-none stroke-primary-500 transition-all duration-700"
                          strokeWidth="2"
                          strokeDasharray={2 * Math.PI * 17}
                          strokeDashoffset={2 * Math.PI * 17 * (1 - subProgress)}
                          strokeLinecap="round"
                        />
                      </svg>
                    )}
                  </div>

                  {/* Step content */}
                  <div className="flex-1 min-w-0 pt-0.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3
                        className={`text-sm font-bold transition-colors duration-300 ${
                          isCurrent ? 'text-primary-800' : isComplete ? 'text-emerald-700' : 'text-slate-400'
                        }`}
                      >
                        {step.label}
                      </h3>
                      {isComplete && (
                        <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-1.5 py-0.5 rounded-full">
                          Done
                        </span>
                      )}
                      {isCurrent && (
                        <span className="text-[10px] font-bold text-primary-600 bg-primary-100 border border-primary-200 px-1.5 py-0.5 rounded-full animate-pulse">
                          Active
                        </span>
                      )}
                    </div>

                    <p
                      className={`text-xs mt-0.5 transition-colors duration-300 ${
                        isCurrent ? 'text-primary-600' : isComplete ? 'text-emerald-600/70' : 'text-slate-400'
                      }`}
                    >
                      {isCurrent && status?.message ? status.message : step.description}
                    </p>

                    {/* Sub-progress bar for current step */}
                    {isCurrent && (
                      <div className="mt-2 w-full h-1.5 bg-primary-100 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-primary-500 rounded-full"
                          initial={{ width: '0%' }}
                          animate={{ width: `${subProgress * 100}%` }}
                          transition={{ duration: 0.5 }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Step icon (desktop) */}
                  <div
                    className={`flex-shrink-0 hidden sm:flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-300 ${
                      isCurrent
                        ? 'bg-primary-100 text-primary-600'
                        : isComplete
                          ? 'bg-emerald-50 text-emerald-600'
                          : 'bg-slate-50 text-slate-300'
                    }`}
                  >
                    {step.icon}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* ── Footer note ──────────────────────────────────── */}
        <div className="mt-8 p-4 bg-amber-50/60 border border-amber-100/60 rounded-xl">
          <p className="text-xs text-amber-700 text-center leading-relaxed">
            <span className="font-semibold">⏱ Processing time varies</span> — depends on the number of candidates and
            web research depth. Do not close this page while processing is active.
          </p>
        </div>
      </div>
    </div>
  )
}
