import { motion } from 'framer-motion'
import { Loader2, CheckCircle, Circle } from 'lucide-react'

interface ProgressViewProps {
  status: any
}

export default function ProgressView({ status }: ProgressViewProps) {
  if (!status) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-primary-700" />
      </div>
    )
  }

  const steps = [
    { key: 'resume', label: 'Resume Analysis', description: 'Extracting and analyzing resume data' },
    { key: 'matching', label: 'Candidate Matching', description: 'Matching candidates to job requirements' },
    { key: 'research', label: 'Deep Research', description: 'Researching candidates across platforms' },
    { key: 'validation', label: 'Information Validation', description: 'Validating candidate information' },
    { key: 'report', label: 'Report Generation', description: 'Generating comprehensive reports' },
  ]

  const getCurrentStepIndex = () => {
    const stepName = status.current_step?.toLowerCase() || ''
    if (stepName.includes('resume') || stepName.includes('parsing')) return 0
    if (stepName.includes('matching')) return 1
    if (stepName.includes('research')) return 2
    if (stepName.includes('validation')) return 3
    if (stepName.includes('report')) return 4
    return 0
  }

  const currentStepIndex = getCurrentStepIndex()

  return (
    <div className="max-w-4xl mx-auto">
      <div className="card">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
            <Loader2 className="w-8 h-8 text-primary-700 animate-spin" />
          </div>
          <h2 className="text-2xl font-bold text-neutral-900 mb-2">
            AI Processing in Progress
          </h2>
          <p className="text-neutral-600">
            {status.message || status.current_step}
          </p>
        </div>

        {/* Overall Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-neutral-600 mb-2">
            <span>Overall Progress</span>
            <span>{Math.round((status.progress || 0) * 100)}%</span>
          </div>
          <div className="w-full h-2 bg-neutral-200 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-primary-700"
              initial={{ width: 0 }}
              animate={{ width: `${(status.progress || 0) * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Step Progress */}
        <div className="space-y-4">
          {steps.map((step, index) => {
            const isComplete = index < currentStepIndex
            const isCurrent = index === currentStepIndex
            const isPending = index > currentStepIndex

            return (
              <motion.div
                key={step.key}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex items-center space-x-4 p-4 rounded-lg border ${
                  isCurrent
                    ? 'border-primary-500 bg-primary-50'
                    : isComplete
                    ? 'border-success-light bg-success-light/10'
                    : 'border-neutral-200 bg-white'
                }`}
              >
                <div className="flex-shrink-0">
                  {isComplete ? (
                    <CheckCircle className="w-6 h-6 text-success-light" />
                  ) : isCurrent ? (
                    <Loader2 className="w-6 h-6 text-primary-700 animate-spin" />
                  ) : (
                    <Circle className="w-6 h-6 text-neutral-300" />
                  )}
                </div>
                <div className="flex-1">
                  <h3 className={`font-semibold ${
                    isCurrent ? 'text-primary-900' : isComplete ? 'text-success-dark' : 'text-neutral-400'
                  }`}>
                    {step.label}
                  </h3>
                  <p className={`text-sm ${
                    isCurrent ? 'text-primary-700' : isComplete ? 'text-success-dark' : 'text-neutral-400'
                  }`}>
                    {step.description}
                  </p>
                </div>
              </motion.div>
            )
          })}
        </div>

        <div className="mt-8 p-4 bg-neutral-100 rounded-lg">
          <p className="text-sm text-neutral-600 text-center">
            ⏱️ This process may take several minutes depending on the number of candidates
          </p>
        </div>
      </div>
    </div>
  )
}
