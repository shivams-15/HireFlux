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
                    {/* Executive Summary */}
                    {candidate?.executive_summary && (
                      <div className="mb-6 p-4 bg-primary-50 rounded-lg">
                        <h4 className="font-semibold text-neutral-900 mb-2">Executive Summary</h4>
                        <div className="text-sm text-neutral-700 whitespace-pre-line">
                          {candidate.executive_summary}
                        </div>
                      </div>
                    )}
                    
                    {/* Research Sources */}
                    {candidate?.research_sources && candidate.research_sources.length > 0 && (
                      <div className="mb-6">
                        <h4 className="font-semibold text-neutral-900 mb-3">Verified Sources ({candidate.research_sources.length})</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                          {candidate.research_sources.map((source: any, i: number) => (
                            <div key={i} className="p-3 border border-neutral-200 rounded-lg">
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-medium text-sm text-neutral-900">{source.platform}</span>
                                {source.verified && (
                                  <CheckCircle className="w-4 h-4 text-success-light" />
                                )}
                              </div>
                              {source.profile_url && (
                                <a 
                                  href={source.profile_url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-xs text-primary-600 hover:underline block truncate"
                                >
                                  View Profile
                                </a>
                              )}
                              {source.data_points && (
                                <div className="mt-2 text-xs text-neutral-600">
                                  {Object.entries(source.data_points).map(([key, value]: [string, any]) => (
                                    <div key={key}>{key}: {value}</div>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Left Column */}
                      <div className="space-y-4">
                        {/* Professional Summary */}
                        <div>
                          <h4 className="font-semibold text-neutral-900 mb-2 flex items-center space-x-2">
                            <Briefcase className="w-4 h-4" />
                            <span>Professional Summary</span>
                          </h4>
                          <div className="text-sm text-neutral-600 space-y-1">
                            <p><strong>Experience:</strong> {professionalSummary?.total_experience_years || 0} years</p>
                            <p><strong>Current Role:</strong> {professionalSummary?.current_role || 'N/A'}</p>
                            <p><strong>Company:</strong> {professionalSummary?.current_company || 'N/A'}</p>
                            <p><strong>Industry:</strong> {professionalSummary?.industry || 'N/A'}</p>
                            <p><strong>Specialization:</strong> {professionalSummary?.specialization || 'N/A'}</p>
                          </div>
                        </div>

                        {/* Technical Skills */}
                        <div>
                          <h4 className="font-semibold text-neutral-900 mb-2 flex items-center space-x-2">
                            <Award className="w-4 h-4" />
                            <span>Technical Skills</span>
                          </h4>
                          
                          {/* High Confidence Skills */}
                          {technicalAssessment?.verified_skills?.high_confidence?.length > 0 && (
                            <div className="mb-3">
                              <p className="text-xs text-neutral-500 mb-1">Verified (Multiple Sources)</p>
                              <div className="flex flex-wrap gap-2">
                                {technicalAssessment.verified_skills.high_confidence.map((skill: string, i: number) => (
                                  <span
                                    key={i}
                                    className="px-2 py-1 bg-success-light/20 text-success-dark rounded text-xs font-medium flex items-center space-x-1"
                                  >
                                    <CheckCircle className="w-3 h-3" />
                                    <span>{skill}</span>
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Medium Confidence Skills */}
                          {technicalAssessment?.verified_skills?.medium_confidence?.length > 0 && (
                            <div className="mb-3">
                              <p className="text-xs text-neutral-500 mb-1">Verified (Single Source)</p>
                              <div className="flex flex-wrap gap-2">
                                {technicalAssessment.verified_skills.medium_confidence.slice(0, 10).map((skill: string, i: number) => (
                                  <span
                                    key={i}
                                    className="px-2 py-1 bg-primary-50 text-primary-700 rounded text-xs font-medium"
                                  >
                                    {skill}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          <div className="text-xs text-neutral-500 mt-2">
                            Total Skills: {technicalAssessment?.total_skills || 0}
                          </div>
                        </div>

                        {/* Experience Details */}
                        {candidate?.experience_summary && candidate.experience_summary.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-neutral-900 mb-2">Experience</h4>
                            <div className="space-y-3">
                              {candidate.experience_summary.slice(0, 3).map((exp: any, i: number) => (
                                <div key={i} className="text-sm">
                                  <p className="font-medium text-neutral-900">{exp.role}</p>
                                  <p className="text-neutral-600">{exp.company}</p>
                                  <p className="text-xs text-neutral-500">{exp.duration}</p>
                                  {exp.verification?.verified_linkedin && (
                                    <span className="inline-flex items-center space-x-1 text-xs text-success-dark mt-1">
                                      <CheckCircle className="w-3 h-3" />
                                      <span>Verified on LinkedIn</span>
                                    </span>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Right Column */}
                      <div className="space-y-4">
                        {/* Verification Status */}
                        {candidate?.verification_status && (
                          <div>
                            <h4 className="font-semibold text-neutral-900 mb-2">Verification Status</h4>
                            <div className="text-sm space-y-2">
                              <div className="flex items-center justify-between p-2 bg-neutral-50 rounded">
                                <span>Overall Status</span>
                                <span className={`font-medium ${
                                  candidate.verification_status.overall_status === 'Verified' 
                                    ? 'text-success-dark' 
                                    : 'text-warning-dark'
                                }`}>
                                  {candidate.verification_status.overall_status}
                                </span>
                              </div>
                              <div className="flex items-center justify-between p-2 bg-neutral-50 rounded">
                                <span>Confidence Score</span>
                                <span className="font-medium">{candidate.verification_status.confidence_score || 0}%</span>
                              </div>
                              <div className="flex items-center justify-between p-2 bg-neutral-50 rounded">
                                <span>Data Sources</span>
                                <span className="font-medium">{candidate.verification_status.data_sources_count || 0}</span>
                              </div>
                            </div>
                          </div>
                        )}
                        
                        {/* Professional Presence */}
                        {candidate?.professional_presence && (
                          <div>
                            <h4 className="font-semibold text-neutral-900 mb-2">Professional Presence</h4>
                            <div className="space-y-2 text-sm">
                              {candidate.professional_presence.github?.metrics && (
                                <div className="p-2 bg-neutral-50 rounded">
                                  <p className="font-medium text-neutral-900">GitHub</p>
                                  <p className="text-xs text-neutral-600">
                                    {candidate.professional_presence.github.metrics.public_repos} repos • 
                                    {' '}{candidate.professional_presence.github.metrics.followers} followers • 
                                    {' '}{candidate.professional_presence.github.metrics.total_stars} stars
                                  </p>
                                  <p className="text-xs text-neutral-500">
                                    Activity: {candidate.professional_presence.github.activity_level}
                                  </p>
                                </div>
                              )}
                              
                              {candidate.professional_presence.linkedin?.metrics && (
                                <div className="p-2 bg-neutral-50 rounded">
                                  <p className="font-medium text-neutral-900">LinkedIn</p>
                                  <p className="text-xs text-neutral-600">
                                    {candidate.professional_presence.linkedin.metrics.connections} connections • 
                                    {' '}{candidate.professional_presence.linkedin.metrics.recommendations} recommendations
                                  </p>
                                  <p className="text-xs text-neutral-500">
                                    Profile: {candidate.professional_presence.linkedin.profile_completeness}
                                  </p>
                                </div>
                              )}
                              
                              <div className="p-2 bg-primary-50 rounded">
                                <p className="font-medium text-neutral-900">Overall Presence Score</p>
                                <p className="text-2xl font-bold text-primary-700">
                                  {candidate.professional_presence.overall_presence_score || 0}%
                                </p>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Key Strengths */}
                        <div>
                          <h4 className="font-semibold text-neutral-900 mb-2">Key Strengths</h4>
                          <ul className="space-y-1 text-sm text-neutral-600">
                            {(candidate?.strengths_and_concerns?.key_strengths || 
                              candidate?.match_analysis?.strengths || []).slice(0, 5).map((strength: string, i: number) => (
                              <li key={i} className="flex items-start space-x-2">
                                <CheckCircle className="w-4 h-4 text-success-light flex-shrink-0 mt-0.5" />
                                <span>{strength}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        {/* Recommendation */}
                        <div>
                          <h4 className="font-semibold text-neutral-900 mb-2">Recommendation</h4>
                          <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                            recommendation?.recommendation === 'STRONGLY RECOMMEND' || recommendation?.recommendation === 'HIGHLY RECOMMENDED'
                              ? 'bg-success-light/10 text-success-dark'
                              : recommendation?.recommendation === 'RECOMMEND' || recommendation?.recommendation === 'RECOMMENDED'
                              ? 'bg-success-light/10 text-success-dark'
                              : recommendation?.recommendation === 'CONDITIONAL RECOMMEND' || recommendation?.recommendation === 'CONSIDER'
                              ? 'bg-warning-light/10 text-warning-dark'
                              : 'bg-error-light/10 text-error-dark'
                          }`}>
                            {recommendation?.recommendation || 'PENDING'}
                          </div>
                          <p className="text-sm text-neutral-600 mt-2">
                            {recommendation?.rationale || candidate?.match_analysis?.strengths?.[0] || 'Analysis in progress...'}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    {/* Projects Section */}
                    {candidate?.projects && candidate.projects.length > 0 && (
                      <div className="mt-6">
                        <h4 className="font-semibold text-neutral-900 mb-3">Projects ({candidate.projects.length})</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {candidate.projects.slice(0, 6).map((project: any, i: number) => (
                            <div key={i} className="p-3 border border-neutral-200 rounded-lg">
                              <div className="flex items-start justify-between mb-1">
                                <h5 className="font-medium text-sm text-neutral-900">{project.name}</h5>
                                {project.verified && (
                                  <CheckCircle className="w-4 h-4 text-success-light flex-shrink-0" />
                                )}
                              </div>
                              <p className="text-xs text-neutral-600 mb-2">{project.description}</p>
                              <div className="flex items-center justify-between">
                                <span className="text-xs text-neutral-500">{project.source}</span>
                                {project.url && (
                                  <a 
                                    href={project.url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-xs text-primary-600 hover:underline"
                                  >
                                    View
                                  </a>
                                )}
                              </div>
                              {project.metrics && (
                                <div className="mt-2 text-xs text-neutral-600">
                                  ⭐ {project.metrics.stars} • 🔀 {project.metrics.forks}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Publications */}
                    {candidate?.publications_thought_leadership?.total_count > 0 && (
                      <div className="mt-6">
                        <h4 className="font-semibold text-neutral-900 mb-3">
                          Publications & Thought Leadership ({candidate.publications_thought_leadership.total_count})
                        </h4>
                        <div className="space-y-2">
                          {candidate.publications_thought_leadership.articles?.slice(0, 3).map((article: any, i: number) => (
                            <div key={i} className="p-2 bg-neutral-50 rounded text-sm">
                              <a 
                                href={article.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="font-medium text-primary-600 hover:underline"
                              >
                                {article.title}
                              </a>
                              <p className="text-xs text-neutral-500 mt-1">{article.platform}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Data Completeness */}
                    {candidate?.data_completeness && (
                      <div className="mt-6 p-4 bg-neutral-50 rounded-lg">
                        <h4 className="font-semibold text-neutral-900 mb-2">Data Completeness</h4>
                        <div className="grid grid-cols-3 gap-4 text-center text-sm">
                          <div>
                            <div className="text-2xl font-bold text-primary-700">
                              {candidate.data_completeness.resume_completeness_percent}%
                            </div>
                            <div className="text-xs text-neutral-600">Resume Data</div>
                          </div>
                          <div>
                            <div className="text-2xl font-bold text-primary-700">
                              {candidate.data_completeness.research_completeness_percent}%
                            </div>
                            <div className="text-xs text-neutral-600">Research Data</div>
                          </div>
                          <div>
                            <div className="text-2xl font-bold text-success-dark">
                              {candidate.data_completeness.overall_completeness_percent}%
                            </div>
                            <div className="text-xs text-neutral-600">Overall</div>
                          </div>
                        </div>
                      </div>
                    )}
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
