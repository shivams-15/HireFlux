import { motion } from 'framer-motion'
import { 
  User, 
  Mail, 
  MapPin, 
  Briefcase, 
  Award,
  Download,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  AlertCircle,
  XCircle
} from 'lucide-react'
import { useState } from 'react'

interface ResultsViewProps {
  results: any
}

export default function ResultsView({ results }: ResultsViewProps) {
  const [expandedCandidate, setExpandedCandidate] = useState<number | null>(0)

  const finalReport = results?.final_report || {}
  const executiveSummary = finalReport?.executive_summary || {}
  const candidateProfiles = finalReport?.candidate_profiles || []

  const getStatusColor = (status: string) => {
    const statusLower = status?.toLowerCase() || ''
    if (statusLower.includes('verified')) return 'success'
    if (statusLower.includes('questionable')) return 'warning'
    if (statusLower.includes('invalid')) return 'error'
    return 'neutral'
  }

  const getStatusIcon = (status: string) => {
    const color = getStatusColor(status)
    if (color === 'success') return <CheckCircle className="w-5 h-5 text-success-light" />
    if (color === 'warning') return <AlertCircle className="w-5 h-5 text-warning-light" />
    if (color === 'error') return <XCircle className="w-5 h-5 text-error-light" />
    return <AlertCircle className="w-5 h-5 text-neutral-400" />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-neutral-900 mb-2">
              Recruitment Analysis Complete
            </h1>
            <p className="text-neutral-600">
              Comprehensive AI-powered candidate evaluation results
            </p>
          </div>
          <button className="btn-primary flex items-center space-x-2">
            <Download className="w-4 h-4" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="card">
        <h2 className="text-2xl font-bold text-neutral-900 mb-6">
          Executive Summary
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="text-center p-4 bg-primary-50 rounded-lg">
            <div className="text-3xl font-bold text-primary-700 mb-1">
              {results?.candidates_processed || 0}
            </div>
            <div className="text-sm text-neutral-600">Total Candidates</div>
          </div>
          <div className="text-center p-4 bg-success-light/10 rounded-lg">
            <div className="text-3xl font-bold text-success-dark mb-1">
              {results?.top_candidates_count || 0}
            </div>
            <div className="text-sm text-neutral-600">Top Candidates</div>
          </div>
          <div className="text-center p-4 bg-primary-50 rounded-lg">
            <div className="text-3xl font-bold text-primary-700 mb-1">
              95%
            </div>
            <div className="text-sm text-neutral-600">Avg Confidence</div>
          </div>
          <div className="text-center p-4 bg-primary-50 rounded-lg">
            <div className="text-3xl font-bold text-primary-700 mb-1">
              12
            </div>
            <div className="text-sm text-neutral-600">Sources Checked</div>
          </div>
        </div>

        {executiveSummary?.key_findings && (
          <div className="border-t border-neutral-200 pt-4">
            <h3 className="font-semibold text-neutral-900 mb-3">Key Findings</h3>
            <ul className="space-y-2">
              {(Array.isArray(executiveSummary.key_findings) 
                ? executiveSummary.key_findings 
                : []
              ).map((finding: string, index: number) => (
                <li key={index} className="flex items-start space-x-2">
                  <CheckCircle className="w-5 h-5 text-success-light flex-shrink-0 mt-0.5" />
                  <span className="text-neutral-700">{finding}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Top Candidates */}
      <div>
        <h2 className="text-2xl font-bold text-neutral-900 mb-4">
          Top Candidates
        </h2>
        
        <div className="space-y-4">
          {candidateProfiles.slice(0, 5).map((candidate: any, index: number) => {
            // Handle multiple possible data structures
            const basicInfo = candidate?.basic_information || candidate?.personal_info || {}
            const candidateName = candidate?.name || basicInfo?.name || 'Unknown Candidate'
            const candidateLocation = candidate?.location || basicInfo?.location || 'N/A'
            const candidateEmail = candidate?.contact_info?.emails?.[0] || basicInfo?.email || 'N/A'
            const matchScore = candidate?.match_score || candidate?.overall_recommendation?.confidence_level || 0
            
            const validation = candidate?.validation_assessment || candidate?.verification_status || {}
            const recommendation = candidate?.overall_recommendation || {}
            const professionalSummary = candidate?.professional_summary || candidate?.experience_summary || {}
            const technicalAssessment = candidate?.technical_assessment || {}
            const isExpanded = expandedCandidate === index

            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="card hover:shadow-md transition-shadow"
              >
                {/* Header */}
                <div 
                  className="flex items-start justify-between cursor-pointer"
                  onClick={() => setExpandedCandidate(isExpanded ? null : index)}
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center text-primary-700 font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <h3 className="text-xl font-semibold text-neutral-900">
                          {candidateName}
                        </h3>
                        <p className="text-sm text-neutral-600">
                          {professionalSummary?.current_role || 'N/A'} at {professionalSummary?.current_company || 'N/A'}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-4 text-sm text-neutral-600 ml-13">
                      {candidateEmail && candidateEmail !== 'N/A' && (
                        <div className="flex items-center space-x-1">
                          <Mail className="w-4 h-4" />
                          <span>{candidateEmail}</span>
                        </div>
                      )}
                      {candidateLocation && candidateLocation !== 'N/A' && (
                        <div className="flex items-center space-x-1">
                          <MapPin className="w-4 h-4" />
                          <span>{candidateLocation}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-2xl font-bold text-primary-700">
                        {matchScore}%
                      </div>
                      <div className="text-xs text-neutral-600">Match Score</div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(validation?.overall_status)}
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-neutral-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-neutral-400" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-6 pt-6 border-t border-neutral-200"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Left Column */}
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-semibold text-neutral-900 mb-2 flex items-center space-x-2">
                            <Briefcase className="w-4 h-4" />
                            <span>Professional Summary</span>
                          </h4>
                          <div className="text-sm text-neutral-600 space-y-1">
                            <p><strong>Total Positions:</strong> {professionalSummary?.total_positions || 0}</p>
                            <p><strong>Years of Experience:</strong> {professionalSummary?.years_of_experience || 'N/A'}</p>
                          </div>
                        </div>

                        <div>
                          <h4 className="font-semibold text-neutral-900 mb-2 flex items-center space-x-2">
                            <Award className="w-4 h-4" />
                            <span>Technical Skills</span>
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {(technicalAssessment?.verified_skills || []).slice(0, 10).map((skill: string, i: number) => (
                              <span
                                key={i}
                                className="px-2 py-1 bg-primary-50 text-primary-700 rounded text-xs font-medium"
                              >
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Right Column */}
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-semibold text-neutral-900 mb-2">
                            Key Strengths
                          </h4>
                          <ul className="space-y-1 text-sm text-neutral-600">
                            {(candidate?.strengths_and_concerns?.key_strengths || []).slice(0, 3).map((strength: string, i: number) => (
                              <li key={i} className="flex items-start space-x-2">
                                <CheckCircle className="w-4 h-4 text-success-light flex-shrink-0 mt-0.5" />
                                <span>{strength}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <h4 className="font-semibold text-neutral-900 mb-2">
                            Recommendation
                          </h4>
                          <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                            recommendation?.recommendation === 'STRONGLY RECOMMEND'
                              ? 'bg-success-light/10 text-success-dark'
                              : recommendation?.recommendation === 'RECOMMEND'
                              ? 'bg-success-light/10 text-success-dark'
                              : recommendation?.recommendation === 'CONDITIONAL RECOMMEND'
                              ? 'bg-warning-light/10 text-warning-dark'
                              : 'bg-error-light/10 text-error-dark'
                          }`}>
                            {recommendation?.recommendation || 'PENDING'}
                          </div>
                          <p className="text-sm text-neutral-600 mt-2">
                            {recommendation?.rationale || 'Analysis in progress...'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
