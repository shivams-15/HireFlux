import { motion, AnimatePresence } from 'framer-motion'
import { 
  User, 
  Users,
  Mail, 
  MapPin, 
  Briefcase, 
  Award,
  Download,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  AlertCircle,
  XCircle,
  ExternalLink,
  Code,
  Star,
  GitFork,
  BookOpen,
  Calendar,
  Building,
  Target,
  Sparkles,
  Link as LinkIcon,
  AlertTriangle,
  Globe,
  FileText,
  Activity,
  Layers,
  GraduationCap
} from 'lucide-react'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

interface ResultsViewProps {
  results: any
}

export default function ResultsView({ results }: ResultsViewProps) {
  const [expandedCandidate, setExpandedCandidate] = useState<number | null>(0)

  const finalReport = results?.final_report || {}
  const executiveSummary = finalReport?.executive_summary || {}
  const candidateProfiles = finalReport?.candidate_profiles || []

  const toPercent = (value: unknown): number => {
    if (typeof value === 'number' && Number.isFinite(value)) return Math.max(0, Math.min(100, Math.round(value)))
    if (typeof value === 'string') {
      const parsed = Number.parseFloat(value.replace('%', '').trim())
      if (Number.isFinite(parsed)) return Math.max(0, Math.min(100, Math.round(parsed)))
    }
    return 0
  }

  const overallSourcesChecked = candidateProfiles.reduce((sum: number, candidate: any) => {
    const sourceCount =
      candidate?.verification_status?.data_sources_count ??
      candidate?.research_sources?.length ??
      0
    return sum + (Number.isFinite(sourceCount) ? Number(sourceCount) : 0)
  }, 0)

  const averageConfidence = candidateProfiles.length > 0
    ? Math.round(
        candidateProfiles.reduce((sum: number, candidate: any) => {
          const confidence =
            candidate?.verification_status?.confidence_score ??
            candidate?.overall_recommendation?.confidence_level ??
            0
          return sum + toPercent(confidence)
        }, 0) / candidateProfiles.length
      )
    : 0

  const topCandidatesCount =
    results?.top_candidates_count ||
    candidateProfiles.filter((candidate: any) => toPercent(candidate?.match_score) > 0).length ||
    candidateProfiles.length

  const summaryMarkdown = typeof executiveSummary === 'string'
    ? executiveSummary
    : executiveSummary?.overview || executiveSummary?.summary || ''

  const getStatusColor = (status: string) => {
    const statusLower = status?.toLowerCase() || ''
    if (statusLower.includes('verified')) return 'success'
    if (statusLower.includes('questionable') || statusLower.includes('conditional')) return 'warning'
    if (statusLower.includes('invalid') || statusLower.includes('unverified')) return 'error'
    return 'neutral'
  }

  const getStatusLabelColor = (status: string) => {
    const color = getStatusColor(status)
    if (color === 'success') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    if (color === 'warning') return 'bg-amber-50 text-amber-700 border-amber-200'
    if (color === 'error') return 'bg-rose-50 text-rose-700 border-rose-200'
    return 'bg-neutral-50 text-neutral-600 border-neutral-200'
  }

  const getStatusIcon = (status: string) => {
    const color = getStatusColor(status)
    if (color === 'success') return <CheckCircle className="w-4 h-4 text-emerald-600" />
    if (color === 'warning') return <AlertTriangle className="w-4 h-4 text-amber-600" />
    if (color === 'error') return <XCircle className="w-4 h-4 text-rose-600" />
    return <AlertCircle className="w-4 h-4 text-neutral-400" />
  }

  const getInitials = (name: string) => {
    if (!name) return 'CN'
    const parts = name.trim().split(/\s+/)
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
    }
    return name.slice(0, 2).toUpperCase()
  }

  const getMatchScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-600 stroke-emerald-600'
    if (score >= 60) return 'text-sky-600 stroke-sky-600'
    if (score >= 40) return 'text-amber-500 stroke-amber-500'
    return 'text-rose-500 stroke-rose-500'
  }

  const getMatchScoreBg = (score: number) => {
    if (score >= 80) return 'bg-emerald-50 border-emerald-100'
    if (score >= 60) return 'bg-sky-50 border-sky-100'
    if (score >= 40) return 'bg-amber-50 border-amber-100'
    return 'bg-rose-50 border-rose-100'
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white border border-neutral-200/80 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-neutral-900 tracking-tight">
              Recruitment Analysis Complete
            </h1>
            <p className="text-neutral-500 mt-1 text-sm md:text-base">
              Comprehensive AI-powered candidate evaluation results
            </p>
          </div>
          <button className="btn-primary flex items-center justify-center space-x-2 shadow-sm hover:shadow active:scale-95 transition-all">
            <Download className="w-4 h-4" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="bg-white border border-neutral-200/80 rounded-xl p-6 shadow-sm">
        <h2 className="text-xl font-bold text-neutral-900 mb-6 flex items-center space-x-2">
          <FileText className="w-5 h-5 text-primary-700" />
          <span>Executive Summary</span>
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl hover:shadow-sm transition-all">
            <div className="text-2xl font-extrabold text-slate-800">
              {results?.candidates_processed || 0}
            </div>
            <div className="text-xs text-neutral-500 font-medium mt-1 uppercase tracking-wider">Total Candidates</div>
          </div>
          <div className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-xl hover:shadow-sm transition-all">
            <div className="text-2xl font-extrabold text-emerald-700">
              {topCandidatesCount}
            </div>
            <div className="text-xs text-neutral-500 font-medium mt-1 uppercase tracking-wider">Top Matches</div>
          </div>
          <div className="p-4 bg-sky-50/50 border border-sky-100 rounded-xl hover:shadow-sm transition-all">
            <div className="text-2xl font-extrabold text-sky-700">
              {averageConfidence}%
            </div>
            <div className="text-xs text-neutral-500 font-medium mt-1 uppercase tracking-wider">Avg Confidence</div>
          </div>
          <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl hover:shadow-sm transition-all">
            <div className="text-2xl font-extrabold text-slate-800">
              {overallSourcesChecked}
            </div>
            <div className="text-xs text-neutral-500 font-medium mt-1 uppercase tracking-wider">Sources Checked</div>
          </div>
        </div>

        {summaryMarkdown && (
          <div className="border-t border-neutral-100 pt-5 mb-5">
            <ReactMarkdown className="markdown-body text-sm text-neutral-700 leading-relaxed">
              {summaryMarkdown}
            </ReactMarkdown>
          </div>
        )}

        {executiveSummary?.key_findings && (
          <div className="border-t border-neutral-100 pt-5">
            <h3 className="font-bold text-neutral-800 text-sm uppercase tracking-wider mb-3">Key Findings</h3>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(Array.isArray(executiveSummary.key_findings) 
                ? executiveSummary.key_findings 
                : []
              ).map((finding: string, index: number) => (
                <li key={index} className="flex items-start space-x-2.5 p-2 bg-neutral-50/60 rounded-lg border border-neutral-100/50">
                  <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-neutral-700 leading-relaxed">{finding}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Candidates List */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-neutral-900 flex items-center space-x-2">
          <Users className="w-5 h-5 text-primary-700" />
          <span>Candidate Evaluations</span>
        </h2>
        
        <div className="space-y-4">
          {candidateProfiles.map((candidate: any, index: number) => {
            const basicInfo = candidate?.basic_information || candidate?.personal_info || {}
            const candidateName = candidate?.name || basicInfo?.name || 'Unknown Candidate'
            const candidateLocation = candidate?.location || basicInfo?.location || 'N/A'
            const candidateEmail = candidate?.contact_info?.emails?.[0] || basicInfo?.email || 'N/A'
            const matchScore = toPercent(candidate?.match_score || candidate?.overall_recommendation?.confidence_level)
            
            const validation = candidate?.validation_assessment || candidate?.verification_status || {}
            const recommendation = candidate?.overall_recommendation || {}
            const professionalSummary = candidate?.professional_summary || candidate?.experience_summary || {}
            const technicalAssessment = candidate?.technical_assessment || {}
            const isExpanded = expandedCandidate === index

            // Clean experience label
            const yearsOfExp = professionalSummary?.total_experience_years ?? 0
            const currentRole = professionalSummary?.current_role
            const currentCompany = professionalSummary?.current_company
            const companyDisplay = (currentRole && currentRole !== 'N/A') || (currentCompany && currentCompany !== 'N/A')
              ? `${currentRole || 'Role N/A'} at ${currentCompany || 'Company N/A'}`
              : 'Professional details not provided'

            // Dynamic border and score styling
            const matchColorClass = getMatchScoreColor(matchScore)

            // Radial gauge math
            const radius = 18
            const strokeWidth = 3.5
            const circumference = 2 * Math.PI * radius
            const strokeDashoffset = circumference - (matchScore / 100) * circumference

            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: Math.min(index * 0.05, 0.3) }}
                className={`bg-white border rounded-xl shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden ${
                  isExpanded ? 'border-primary-300 ring-1 ring-primary-100/50' : 'border-neutral-200/80 hover:border-neutral-300'
                }`}
              >
                {/* Card Header (Collapsed View) */}
                <div 
                  className={`p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer select-none transition-colors ${
                    isExpanded ? 'bg-slate-50/50' : 'hover:bg-slate-50/30'
                  }`}
                  onClick={() => setExpandedCandidate(isExpanded ? null : index)}
                >
                  <div className="flex items-start space-x-4 flex-1">
                    {/* Initials Avatar */}
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-700 to-primary-900 text-white flex items-center justify-center font-bold text-base shadow-sm flex-shrink-0">
                      {getInitials(candidateName)}
                    </div>
                    
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-lg font-bold text-neutral-900 leading-tight">
                          {candidateName}
                        </h3>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold border flex items-center gap-1 ${getStatusLabelColor(validation?.overall_status)}`}>
                          {getStatusIcon(validation?.overall_status)}
                          <span>{validation?.overall_status || 'Unverified'}</span>
                        </span>
                      </div>
                      
                      <p className="text-sm text-neutral-600 font-medium">
                        {companyDisplay}
                      </p>

                      <div className="flex flex-wrap gap-x-4 gap-y-1 pt-1">
                        {candidateEmail && candidateEmail !== 'N/A' && (
                          <div className="flex items-center space-x-1.5 text-xs text-neutral-500">
                            <Mail className="w-3.5 h-3.5 text-neutral-400" />
                            <span>{candidateEmail}</span>
                          </div>
                        )}
                        {candidateLocation && candidateLocation !== 'N/A' && (
                          <div className="flex items-center space-x-1.5 text-xs text-neutral-500">
                            <MapPin className="w-3.5 h-3.5 text-neutral-400" />
                            <span>{candidateLocation}</span>
                          </div>
                        )}
                        <div className="flex items-center space-x-1.5 text-xs text-neutral-500">
                          <Briefcase className="w-3.5 h-3.5 text-neutral-400" />
                          <span>{yearsOfExp} years exp</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between md:justify-end gap-5 border-t border-neutral-100 md:border-none pt-3 md:pt-0">
                    {/* SVG Radial Progress Meter for Match Score */}
                    <div className="flex items-center space-x-3 bg-neutral-50 px-3 py-1.5 rounded-lg border border-neutral-100">
                      <div className="relative w-10 h-10 flex items-center justify-center">
                        <svg className="w-full h-full transform -rotate-90">
                          {/* Background Circle */}
                          <circle
                            cx="20"
                            cy="20"
                            r={radius}
                            className="stroke-neutral-200 fill-none"
                            strokeWidth={strokeWidth}
                          />
                          {/* Active Gauge Arc */}
                          <circle
                            cx="20"
                            cy="20"
                            r={radius}
                            className={`fill-none transition-all duration-500 ease-out ${matchColorClass}`}
                            strokeWidth={strokeWidth}
                            strokeDasharray={circumference}
                            strokeDashoffset={strokeDashoffset}
                            strokeLinecap="round"
                          />
                        </svg>
                        <div className="absolute text-[11px] font-extrabold text-neutral-700">
                          {matchScore}%
                        </div>
                      </div>
                      <div className="text-left">
                        <div className="text-xs font-bold text-neutral-700">Match Score</div>
                        <div className="text-[10px] text-neutral-500">AI Requirement Fit</div>
                      </div>
                    </div>

                    <div className="p-1.5 hover:bg-neutral-100 rounded-lg transition-colors">
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-neutral-500" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-neutral-500" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Card Body (Expanded View) */}
                <AnimatePresence initial={false}>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25, ease: 'easeInOut' }}
                      className="border-t border-neutral-100 bg-slate-50/30 overflow-hidden"
                    >
                      <div className="p-6 space-y-6">
                        {/* Executive Summary Callout */}
                        {candidate?.executive_summary && (
                          <div className="bg-primary-50/40 border border-primary-100/70 rounded-xl p-4.5 flex items-start space-x-3">
                            <Sparkles className="w-5 h-5 text-primary-700 mt-0.5 flex-shrink-0" />
                            <div className="space-y-1">
                              <h4 className="text-sm font-bold text-neutral-800">Executive Summary</h4>
                              <ReactMarkdown className="markdown-body text-sm text-neutral-600 leading-relaxed">
                                {candidate.executive_summary}
                              </ReactMarkdown>
                            </div>
                          </div>
                        )}

                        {/* Split Grid Section */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          
                          {/* Left Panel: Profile Details & Skills */}
                          <div className="space-y-5">
                            
                            {/* Professional Details Card */}
                            <div className="bg-white border border-neutral-100 rounded-xl p-5 shadow-sm space-y-4">
                              <h4 className="font-bold text-neutral-800 text-sm uppercase tracking-wider flex items-center space-x-2 border-b border-neutral-100 pb-2.5">
                                <User className="w-4 h-4 text-primary-700" />
                                <span>Professional Summary</span>
                              </h4>
                              
                              <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                                <div>
                                  <span className="text-xs text-neutral-400 font-medium block">Total Experience</span>
                                  <span className="font-semibold text-neutral-800">{professionalSummary?.total_experience_years || 0} Years</span>
                                </div>
                                <div>
                                  <span className="text-xs text-neutral-400 font-medium block">Current Role</span>
                                  <span className="font-semibold text-neutral-800 truncate block">{professionalSummary?.current_role || 'N/A'}</span>
                                </div>
                                <div>
                                  <span className="text-xs text-neutral-400 font-medium block">Company</span>
                                  <span className="font-semibold text-neutral-800 truncate block">{professionalSummary?.current_company || 'N/A'}</span>
                                </div>
                                <div>
                                  <span className="text-xs text-neutral-400 font-medium block">Industry Focus</span>
                                  <span className="font-semibold text-neutral-800 truncate block">{professionalSummary?.industry || 'N/A'}</span>
                                </div>
                                <div className="col-span-2">
                                  <span className="text-xs text-neutral-400 font-medium block">Specialization</span>
                                  <span className="font-semibold text-neutral-800">{professionalSummary?.specialization || 'N/A'}</span>
                                </div>
                              </div>
                            </div>

                            {/* Technical Skills Card */}
                            <div className="bg-white border border-neutral-100 rounded-xl p-5 shadow-sm space-y-4">
                              <h4 className="font-bold text-neutral-800 text-sm uppercase tracking-wider flex items-center space-x-2 border-b border-neutral-100 pb-2.5">
                                <Award className="w-4 h-4 text-primary-700" />
                                <span>Technical Skill Matrix</span>
                              </h4>

                              {/* High Confidence Skills */}
                              {technicalAssessment?.verified_skills?.high_confidence?.length > 0 ? (
                                <div className="space-y-2">
                                  <div className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded inline-block font-semibold">
                                    Verified (Cross-Referenced)
                                  </div>
                                  <div className="flex flex-wrap gap-1.5">
                                    {technicalAssessment.verified_skills.high_confidence.map((skill: string, i: number) => (
                                      <span
                                        key={i}
                                        className="px-2.5 py-1 bg-emerald-50 text-emerald-800 border border-emerald-100 rounded-lg text-xs font-semibold flex items-center space-x-1"
                                      >
                                        <CheckCircle className="w-3 h-3 text-emerald-600" />
                                        <span>{skill}</span>
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              ) : null}

                              {/* Medium Confidence Skills */}
                              {technicalAssessment?.verified_skills?.medium_confidence?.length > 0 ? (
                                <div className="space-y-2">
                                  <div className="text-xs text-sky-700 bg-sky-50 border border-sky-100 px-2 py-0.5 rounded inline-block font-semibold">
                                    Identified Skills (Resume claims)
                                  </div>
                                  <div className="flex flex-wrap gap-1.5">
                                    {technicalAssessment.verified_skills.medium_confidence.slice(0, 15).map((skill: string, i: number) => (
                                      <span
                                        key={i}
                                        className="px-2.5 py-1 bg-slate-50 text-slate-700 border border-slate-100 rounded-lg text-xs font-medium"
                                      >
                                        {skill}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              ) : null}

                              {(!technicalAssessment?.verified_skills?.high_confidence?.length && 
                                !technicalAssessment?.verified_skills?.medium_confidence?.length) ? (
                                <div className="text-center py-6 text-sm text-neutral-400 bg-neutral-50/50 rounded-xl border border-dashed border-neutral-200">
                                  No technical skills matching analysis models
                                </div>
                              ) : (
                                <div className="text-xs text-neutral-400 pt-1 border-t border-neutral-50 flex justify-between">
                                  <span>Analyzed Skill Profile</span>
                                  <span>Total identified: {technicalAssessment?.total_skills || 0}</span>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Right Panel: Verification Details, Presence & Recommendations */}
                          <div className="space-y-5">
                            
                            {/* Verification Stats Card */}
                            <div className="bg-white border border-neutral-100 rounded-xl p-5 shadow-sm space-y-4">
                              <h4 className="font-bold text-neutral-800 text-sm uppercase tracking-wider flex items-center space-x-2 border-b border-neutral-100 pb-2.5">
                                <Target className="w-4 h-4 text-primary-700" />
                                <span>Verification Status</span>
                              </h4>

                              <div className="space-y-3.5">
                                {/* Confidence Score Progress bar */}
                                <div>
                                  <div className="flex justify-between items-center text-xs font-semibold text-neutral-600 mb-1.5">
                                    <span>Background Integrity Score</span>
                                    <span className="text-neutral-900">{validation?.confidence_score || 0}%</span>
                                  </div>
                                  <div className="w-full bg-slate-100 rounded-full h-2">
                                    <div 
                                      className={`h-2 rounded-full transition-all duration-500 ${
                                        (validation?.confidence_score || 0) >= 75 ? 'bg-emerald-500' :
                                        (validation?.confidence_score || 0) >= 50 ? 'bg-amber-500' : 'bg-slate-400'
                                      }`}
                                      style={{ width: `${validation?.confidence_score || 0}%` }}
                                    />
                                  </div>
                                </div>

                                <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-lg border border-neutral-100">
                                  <div>
                                    <span className="text-neutral-400 block mb-0.5">Verification Integrity</span>
                                    <span className="font-bold text-neutral-700">{validation?.overall_status || 'Unverified'}</span>
                                  </div>
                                  <div>
                                    <span className="text-neutral-400 block mb-0.5">Data Sources Scraped</span>
                                    <span className="font-bold text-neutral-700">{validation?.data_sources_count || 0} platform sources</span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Professional Presence Card */}
                            {candidate?.professional_presence && (
                              <div className="bg-white border border-neutral-100 rounded-xl p-5 shadow-sm space-y-4">
                                <h4 className="font-bold text-neutral-800 text-sm uppercase tracking-wider flex items-center space-x-2 border-b border-neutral-100 pb-2.5">
                                  <Globe className="w-4 h-4 text-primary-700" />
                                  <span>Social Footprint & Metrics</span>
                                </h4>

                                <div className="space-y-3">
                                  {candidate.professional_presence.github?.metrics && (
                                    <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-between text-xs">
                                      <div>
                                        <p className="font-bold text-neutral-800">GitHub Developer Profile</p>
                                        <p className="text-neutral-500 mt-0.5">
                                          {candidate.professional_presence.github.metrics.public_repos} repos • {candidate.professional_presence.github.metrics.followers} followers • {candidate.professional_presence.github.metrics.total_stars} stars
                                        </p>
                                      </div>
                                      <span className="px-2 py-0.5 bg-neutral-200/60 rounded text-[10px] font-bold uppercase text-neutral-700 border border-neutral-300/40">
                                        {candidate.professional_presence.github.activity_level}
                                      </span>
                                    </div>
                                  )}

                                  {candidate.professional_presence.linkedin?.metrics && (
                                    <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-between text-xs">
                                      <div>
                                        <p className="font-bold text-neutral-800">LinkedIn Career Profile</p>
                                        <p className="text-neutral-500 mt-0.5">
                                          {candidate.professional_presence.linkedin.metrics.connections} connections • {candidate.professional_presence.linkedin.metrics.recommendations} recommendations
                                        </p>
                                      </div>
                                      <span className="px-2 py-0.5 bg-neutral-200/60 rounded text-[10px] font-bold uppercase text-neutral-700 border border-neutral-300/40">
                                        {candidate.professional_presence.linkedin.profile_completeness}
                                      </span>
                                    </div>
                                  )}

                                  {!candidate.professional_presence.github?.metrics && !candidate.professional_presence.linkedin?.metrics && (
                                    <div className="p-3 bg-amber-50/70 border border-amber-100 rounded-lg text-amber-800 text-xs flex items-start gap-2">
                                      <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                                      <span>External profile data is limited. Web research returned few verifiable footprint sources.</span>
                                    </div>
                                  )}

                                  <div className="p-3 bg-primary-50/50 border border-primary-100 rounded-xl flex items-center justify-between text-xs">
                                    <span className="font-semibold text-primary-900">Footprint Score</span>
                                    <span className="text-base font-extrabold text-primary-800">
                                      {candidate.professional_presence.overall_presence_score || 0}%
                                    </span>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Recommendation & Rationale Card */}
                            <div className="bg-white border border-neutral-100 rounded-xl p-5 shadow-sm space-y-3.5">
                              <h4 className="font-bold text-neutral-800 text-sm uppercase tracking-wider flex items-center space-x-2 border-b border-neutral-100 pb-2.5">
                                <Target className="w-4 h-4 text-primary-700" />
                                <span>Recommendation</span>
                              </h4>

                              <div>
                                <span className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
                                  recommendation?.recommendation?.includes('STRONGLY') || recommendation?.recommendation?.includes('HIGHLY')
                                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                    : recommendation?.recommendation?.includes('CONDITIONAL') || recommendation?.recommendation?.includes('CONSIDER')
                                    ? 'bg-amber-50 text-amber-800 border-amber-200'
                                    : recommendation?.recommendation?.includes('RECOMMEND')
                                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                    : 'bg-rose-50 text-rose-800 border-rose-200'
                                }`}>
                                  <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                  <span>{recommendation?.recommendation || 'PENDING'}</span>
                                </span>
                              </div>

                              <p className="text-sm text-neutral-600 leading-relaxed pt-1 border-t border-neutral-50 font-medium">
                                {recommendation?.rationale || candidate?.match_analysis?.strengths?.[0] || 'Analysis in progress...'}
                              </p>
                            </div>

                          </div>
                        </div>

                        {/* Strengths & Gaps Row */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          
                          {/* Strengths */}
                          <div className="bg-emerald-50/20 border-l-4 border-emerald-500 rounded-r-xl p-5 border border-neutral-100 space-y-3">
                            <h4 className="font-bold text-emerald-800 text-sm uppercase tracking-wider flex items-center space-x-2">
                              <CheckCircle className="w-4 h-4 text-emerald-600" />
                              <span>Key Strengths</span>
                            </h4>
                            
                            {(candidate?.strengths_and_concerns?.key_strengths || candidate?.match_analysis?.strengths || []).length > 0 ? (
                              <ul className="space-y-2 text-sm text-neutral-700">
                                {(candidate?.strengths_and_concerns?.key_strengths || 
                                  candidate?.match_analysis?.strengths || []).slice(0, 5).map((strength: string, i: number) => (
                                  <li key={i} className="flex items-start space-x-2">
                                    <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                                    <span className="leading-tight">{strength}</span>
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-sm text-neutral-500 italic">No explicit key strength signals verified in reports.</p>
                            )}
                          </div>

                          {/* Gaps/Concerns */}
                          <div className="bg-amber-50/20 border-l-4 border-amber-500 rounded-r-xl p-5 border border-neutral-100 space-y-3">
                            <h4 className="font-bold text-amber-800 text-sm uppercase tracking-wider flex items-center space-x-2">
                              <AlertTriangle className="w-4 h-4 text-amber-600" />
                              <span>Key Gaps & Concerns</span>
                            </h4>

                            {(candidate?.strengths_and_concerns?.key_concerns || candidate?.match_analysis?.gaps || []).length > 0 ? (
                              <ul className="space-y-2 text-sm text-neutral-700">
                                {(candidate?.strengths_and_concerns?.key_concerns || 
                                  candidate?.match_analysis?.gaps || []).slice(0, 5).map((gap: string, i: number) => (
                                  <li key={i} className="flex items-start space-x-2">
                                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
                                    <span className="leading-tight">{gap}</span>
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-sm text-neutral-600 leading-relaxed">No critical background mismatch concerns or skills gaps identified for this role.</p>
                            )}
                          </div>
                        </div>

                        {/* Research Sources Platforms */}
                        {candidate?.research_sources && candidate.research_sources.length > 0 && (
                          <div className="space-y-3">
                            <h4 className="font-bold text-neutral-800 text-sm uppercase tracking-wider flex items-center space-x-2">
                              <Globe className="w-4 h-4 text-primary-700" />
                              <span>Scraped Platforms ({candidate.research_sources.length})</span>
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                              {candidate.research_sources.map((source: any, i: number) => (
                                <div key={i} className="p-4 bg-white border border-neutral-100 rounded-xl flex flex-col justify-between hover:shadow-sm transition-all duration-200">
                                  <div>
                                    <div className="flex items-center justify-between mb-2">
                                      <span className="font-bold text-sm text-neutral-800">{source.platform}</span>
                                      {source.verified && (
                                        <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-100 font-bold px-2 py-0.5 rounded flex items-center gap-0.5">
                                          <CheckCircle className="w-2.5 h-2.5 text-emerald-600" />
                                          <span>Verified</span>
                                        </span>
                                      )}
                                    </div>
                                    
                                    {source.data_points && (
                                      <div className="space-y-1 text-xs text-neutral-500 mt-2 bg-slate-50 p-2.5 rounded-lg border border-neutral-100">
                                        {Object.entries(source.data_points).map(([key, value]: [string, any]) => (
                                          <div key={key} className="flex justify-between">
                                            <span className="font-medium text-neutral-400 capitalize">{key.replace('_', ' ')}:</span>
                                            <span className="font-bold text-neutral-600 truncate max-w-[120px]">{String(value)}</span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                  
                                  {source.profile_url && (
                                    <a 
                                      href={source.profile_url} 
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      className="text-xs text-primary-700 hover:text-primary-800 hover:underline inline-flex items-center gap-1 mt-3 font-semibold"
                                    >
                                      <span>View Scraped Profile</span>
                                      <ExternalLink className="w-3.5 h-3.5" />
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Projects Section */}
                        {candidate?.projects && candidate.projects.length > 0 && (
                          <div className="space-y-3">
                            <h4 className="font-bold text-neutral-800 text-sm uppercase tracking-wider flex items-center space-x-2">
                              <Code className="w-4 h-4 text-primary-700" />
                              <span>Portfolio & Repositories ({candidate.projects.length})</span>
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {candidate.projects.slice(0, 6).map((project: any, i: number) => (
                                <div key={i} className="p-4 bg-white border border-neutral-100 rounded-xl hover:shadow-sm transition-all duration-200 flex flex-col justify-between">
                                  <div>
                                    <div className="flex items-start justify-between gap-2">
                                      <h5 className="font-bold text-sm text-neutral-800 truncate">{project.name}</h5>
                                      {project.verified && (
                                        <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-100 font-bold px-1.5 py-0.5 rounded flex items-center gap-0.5">
                                          <CheckCircle className="w-2.5 h-2.5 text-emerald-600" />
                                          <span>Verified</span>
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-xs text-neutral-500 mt-1.5 leading-relaxed line-clamp-2">{project.description}</p>
                                  </div>
                                  
                                  <div className="flex items-center justify-between mt-3.5 pt-2.5 border-t border-neutral-50 text-xs">
                                    <span className="text-neutral-400 font-medium">{project.source}</span>
                                    
                                    <div className="flex items-center gap-3.5">
                                      {project.metrics && (
                                        <div className="flex items-center gap-2.5 text-neutral-500 font-semibold text-[11px]">
                                          <span className="flex items-center">
                                            <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500 mr-0.5" />
                                            {project.metrics.stars || 0}
                                          </span>
                                          <span className="flex items-center">
                                            <GitFork className="w-3.5 h-3.5 text-neutral-400 mr-0.5" />
                                            {project.metrics.forks || 0}
                                          </span>
                                        </div>
                                      )}
                                      
                                      {project.url && (
                                        <a 
                                          href={project.url} 
                                          target="_blank" 
                                          rel="noopener noreferrer"
                                          className="text-primary-700 hover:text-primary-800 hover:underline inline-flex items-center gap-0.5 font-bold"
                                        >
                                          <span>View</span>
                                          <ExternalLink className="w-3 h-3" />
                                        </a>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Experience Timeline */}
                        {candidate?.experience_summary && candidate.experience_summary.length > 0 && (
                          <div className="space-y-3">
                            <h4 className="font-bold text-neutral-800 text-sm uppercase tracking-wider flex items-center space-x-2">
                              <Building className="w-4 h-4 text-primary-700" />
                              <span>Professional Career History</span>
                            </h4>
                            <div className="relative border-l border-neutral-200 pl-4.5 ml-2.5 space-y-6 pt-2">
                              {candidate.experience_summary.slice(0, 5).map((exp: any, i: number) => (
                                <div key={i} className="relative">
                                  {/* Timeline Node */}
                                  <div className="absolute -left-[27.5px] top-1.5 w-4 h-4 rounded-full bg-white border border-neutral-300 flex items-center justify-center">
                                    <div className="w-2 h-2 rounded-full bg-primary-700" />
                                  </div>
                                  
                                  <div className="space-y-0.5 text-sm">
                                    <div className="flex flex-wrap items-center gap-x-2">
                                      <span className="font-bold text-neutral-900">{exp.role}</span>
                                      {exp.verification?.verified_linkedin && (
                                        <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-100 px-1.5 py-0.2 rounded font-bold inline-flex items-center gap-0.5">
                                          <CheckCircle className="w-2.5 h-2.5 text-emerald-600" />
                                          <span>LinkedIn Verified</span>
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-neutral-600 font-medium text-xs">{exp.company}</p>
                                    <div className="flex items-center gap-1.5 text-xs text-neutral-400">
                                      <Calendar className="w-3 h-3" />
                                      <span>{exp.duration}</span>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Publications */}
                        {candidate?.publications_thought_leadership?.total_count > 0 && (
                          <div className="space-y-3">
                            <h4 className="font-bold text-neutral-800 text-sm uppercase tracking-wider flex items-center space-x-2">
                              <BookOpen className="w-4 h-4 text-primary-700" />
                              <span>Publications & Thought Leadership ({candidate.publications_thought_leadership.total_count})</span>
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              {candidate.publications_thought_leadership.articles?.slice(0, 3).map((article: any, i: number) => (
                                <div key={i} className="p-3.5 bg-white border border-neutral-100 rounded-xl hover:shadow-sm transition-all duration-200 flex flex-col justify-between">
                                  <a 
                                    href={article.url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="font-bold text-sm text-primary-700 hover:text-primary-800 hover:underline leading-snug"
                                  >
                                    {article.title}
                                  </a>
                                  <div className="flex items-center justify-between text-xs text-neutral-400 mt-2.5 pt-2 border-t border-neutral-50">
                                    <span>{article.platform}</span>
                                    <ExternalLink className="w-3.5 h-3.5" />
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Data Completeness */}
                        {candidate?.data_completeness && (
                          <div className="bg-white border border-neutral-100 rounded-xl p-5 shadow-sm space-y-4">
                            <h4 className="font-bold text-neutral-800 text-sm uppercase tracking-wider flex items-center space-x-2 border-b border-neutral-100 pb-2.5">
                              <Layers className="w-4 h-4 text-primary-700" />
                              <span>Data Integrity Coverage</span>
                            </h4>
                            <div className="grid grid-cols-3 gap-6 text-center">
                              <div>
                                <span className="text-2xl font-extrabold text-primary-700 block">
                                  {candidate.data_completeness.resume_completeness_percent}%
                                </span>
                                <span className="text-xs text-neutral-400 font-semibold mt-1 block">Resume Completeness</span>
                              </div>
                              <div>
                                <span className="text-2xl font-extrabold text-primary-700 block">
                                  {candidate.data_completeness.research_completeness_percent}%
                                </span>
                                <span className="text-xs text-neutral-400 font-semibold mt-1 block">Social Research Match</span>
                              </div>
                              <div>
                                <span className="text-2xl font-extrabold text-emerald-600 block">
                                  {candidate.data_completeness.overall_completeness_percent}%
                                </span>
                                <span className="text-xs text-neutral-400 font-semibold mt-1 block">Overall Profile Integrity</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
