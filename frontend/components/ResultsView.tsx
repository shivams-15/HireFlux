'use client'

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
  AlertTriangle,
  Globe,
  FileText,
  Layers,
  Search,
  ArrowUpDown,
  TrendingUp,
  TrendingDown,
  Medal,
  Trophy,
  Info,
  Zap,
  Clock,
  Shield,
  RefreshCw,
} from 'lucide-react'
import { useState, useRef, useEffect, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'

interface ResultsViewProps {
  results: any
}

type SortKey = 'score' | 'name' | 'experience'

export default function ResultsView({ results }: ResultsViewProps) {
  const [expandedCandidate, setExpandedCandidate] = useState<number | null>(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<SortKey>('score')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')
  const [showExportMenu, setShowExportMenu] = useState(false)
  const expandedRef = useRef<HTMLDivElement>(null)

  const finalReport = results?.final_report || {}
  const executiveSummary = finalReport?.executive_summary || {}
  const candidateProfiles: any[] = finalReport?.candidate_profiles || []

  /* ── Data helpers ──────────────────────────────────────────── */
  const toPercent = (value: unknown): number => {
    if (typeof value === 'number' && Number.isFinite(value)) return Math.max(0, Math.min(100, Math.round(value)))
    if (typeof value === 'string') {
      const parsed = Number.parseFloat(value.replace('%', '').trim())
      if (Number.isFinite(parsed)) return Math.max(0, Math.min(100, Math.round(parsed)))
    }
    return 0
  }

  const normalizeSkills = (skills: any[] | string | undefined): string[] => {
    if (!skills) return []
    if (Array.isArray(skills)) {
      return skills
        .flatMap((s) => (typeof s === 'string' ? s.split(/[,\n•·]\s*/) : []))
        .map((s) => s.trim())
        .filter((s) => s.length > 0 && s.length < 60 && !s.startsWith('http'))
    }
    if (typeof skills === 'string') {
      return skills.split(/[,\n•·]\s*/).map((s) => s.trim()).filter((s) => s.length > 0 && s.length < 60)
    }
    return []
  }

  const getFullName = (candidate: any): string => {
    const basic = candidate?.basic_information || candidate?.personal_info || {}
    return candidate?.name || basic?.name || 'Unnamed Candidate'
  }

  const getLocation = (candidate: any): string | null => {
    const basic = candidate?.basic_information || candidate?.personal_info || {}
    const loc = candidate?.location || basic?.location || ''
    return loc && loc !== 'N/A' ? loc : null
  }

  const getEmail = (candidate: any): string | null => {
    const basic = candidate?.basic_information || candidate?.personal_info || {}
    const email = candidate?.contact_info?.emails?.[0] || basic?.email || ''
    return email && email !== 'N/A' ? email : null
  }

  const getExperienceYears = (candidate: any): number => {
    const prof = candidate?.professional_summary || candidate?.experience_summary || {}
    const yrs = prof?.total_experience_years
    return typeof yrs === 'number' && yrs >= 0 ? yrs : 0
  }

  const getCurrentRole = (candidate: any): string | null => {
    const prof = candidate?.professional_summary || {}
    const role = prof?.current_role
    return role && role !== 'N/A' ? role : null
  }

  const getCurrentCompany = (candidate: any): string | null => {
    const prof = candidate?.professional_summary || {}
    const comp = prof?.current_company
    return comp && comp !== 'N/A' ? comp : null
  }

  const getMatchScore = (candidate: any): number => {
    const score =
      candidate?.match_score ??
      candidate?.overall_recommendation?.confidence_level ??
      candidate?.match_analysis?.overall_score
    return toPercent(score)
  }

  /* ── Derived metrics ───────────────────────────────────────── */
  const overallSourcesChecked = candidateProfiles.reduce(
    (sum: number, c: any) => sum + (c?.verification_status?.data_sources_count ?? c?.research_sources?.length ?? 0),
    0,
  )

  const averageConfidence =
    candidateProfiles.length > 0
      ? Math.round(
          candidateProfiles.reduce((sum: number, c: any) => {
            const confidence =
              c?.verification_status?.confidence_score ?? c?.overall_recommendation?.confidence_level ?? 0
            return sum + toPercent(confidence)
          }, 0) / candidateProfiles.length,
        )
      : 0

  const topCandidatesCount = candidateProfiles.filter((c: any) => getMatchScore(c) >= 60).length

  const summaryMarkdown =
    typeof executiveSummary === 'string'
      ? executiveSummary
      : executiveSummary?.overview || executiveSummary?.summary || ''

  /* ── Filter + Sort ─────────────────────────────────────────── */
  const filteredCandidates = useMemo(() => {
    let filtered = [...candidateProfiles]

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      filtered = filtered.filter((c) => {
        const name = getFullName(c).toLowerCase()
        const role = (getCurrentRole(c) || '').toLowerCase()
        const company = (getCurrentCompany(c) || '').toLowerCase()
        const email = (getEmail(c) || '').toLowerCase()
        const skills = normalizeSkills(
          c?.technical_assessment?.claimed || c?.technical_assessment?.verified || c?.technical_assessment?.discovered,
        )
          .join(' ')
          .toLowerCase()
        const summary = (c?.executive_summary || '').toLowerCase()
        return (
          name.includes(q) ||
          role.includes(q) ||
          company.includes(q) ||
          email.includes(q) ||
          skills.includes(q) ||
          summary.includes(q)
        )
      })
    }

    filtered.sort((a, b) => {
      let cmp = 0
      if (sortBy === 'score') cmp = getMatchScore(b) - getMatchScore(a)
      else if (sortBy === 'name') cmp = getFullName(a).localeCompare(getFullName(b))
      else if (sortBy === 'experience') cmp = getExperienceYears(b) - getExperienceYears(a)
      return sortDirection === 'desc' ? cmp : -cmp
    })

    return filtered
  }, [candidateProfiles, searchQuery, sortBy, sortDirection])

  /* ── Export ────────────────────────────────────────────────── */
  const handleExport = (format: 'json' | 'csv') => {
    if (format === 'json') {
      const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `hireflux_report_${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      URL.revokeObjectURL(url)
    } else {
      const headers = ['Name', 'Role', 'Company', 'Match Score', 'Experience (Years)', 'Location', 'Email']
      const rows = candidateProfiles.map((c) => [
        getFullName(c),
        getCurrentRole(c) || '-',
        getCurrentCompany(c) || '-',
        `${getMatchScore(c)}%`,
        getExperienceYears(c),
        getLocation(c) || '-',
        getEmail(c) || '-',
      ])
      const csv = [headers, ...rows]
        .map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(','))
        .join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `hireflux_candidates_${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      URL.revokeObjectURL(url)
    }
    setShowExportMenu(false)
  }

  /* ── Smooth scroll on expand ───────────────────────────────── */
  useEffect(() => {
    if (expandedCandidate !== null && expandedRef.current) {
      expandedRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [expandedCandidate])

  /* ── Style helpers ─────────────────────────────────────────── */
  const getStatusColor = (status: string) => {
    const s = status?.toLowerCase() || ''
    if (s.includes('verified')) return 'success'
    if (s.includes('questionable') || s.includes('conditional')) return 'warning'
    if (s.includes('invalid') || s.includes('unverified')) return 'error'
    return 'neutral'
  }

  const getStatusPillClass = (status: string) => {
    const c = getStatusColor(status)
    if (c === 'success') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    if (c === 'warning') return 'bg-amber-50 text-amber-700 border-amber-200'
    if (c === 'error') return 'bg-rose-50 text-rose-700 border-rose-200'
    return 'bg-slate-50 text-slate-500 border-slate-200'
  }

  const getStatusIcon = (status: string) => {
    const c = getStatusColor(status)
    if (c === 'success') return <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
    if (c === 'warning') return <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
    if (c === 'error') return <XCircle className="w-3.5 h-3.5 text-rose-600" />
    return <AlertCircle className="w-3.5 h-3.5 text-slate-400" />
  }

  const getInitials = (name: string) => {
    if (!name) return '?'
    const parts = name.trim().split(/\s+/)
    if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
    return name.slice(0, 2).toUpperCase()
  }

  const getScoreColorClass = (score: number) => {
    if (score >= 80) return 'text-emerald-600'
    if (score >= 60) return 'text-sky-600'
    if (score >= 40) return 'text-amber-500'
    return 'text-rose-500'
  }

  const getScoreBgClass = (score: number) => {
    if (score >= 80) return 'bg-emerald-50 border-emerald-200'
    if (score >= 60) return 'bg-sky-50 border-sky-200'
    if (score >= 40) return 'bg-amber-50 border-amber-200'
    return 'bg-rose-50 border-rose-200'
  }

  const getTierBadge = (score: number) => {
    if (score >= 80) return { label: 'Top Tier', icon: <Trophy className="w-3.5 h-3.5" />, cls: 'text-emerald-700 bg-emerald-50 border-emerald-200' }
    if (score >= 60) return { label: 'Strong Match', icon: <Medal className="w-3.5 h-3.5" />, cls: 'text-sky-700 bg-sky-50 border-sky-200' }
    if (score >= 40) return { label: 'Potential', icon: <TrendingUp className="w-3.5 h-3.5" />, cls: 'text-amber-700 bg-amber-50 border-amber-200' }
    return { label: 'Low Match', icon: <TrendingDown className="w-3.5 h-3.5" />, cls: 'text-rose-700 bg-rose-50 border-rose-200' }
  }

  /* ── Empty state ───────────────────────────────────────────── */
  if (!candidateProfiles.length) {
    return (
      <div className="max-w-2xl mx-auto py-20 text-center">
        <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Users className="w-10 h-10 text-slate-400" />
        </div>
        <h2 className="text-2xl font-bold text-neutral-900 mb-2">No Candidate Data</h2>
        <p className="text-neutral-500 mb-8">
          The analysis completed but no candidate profiles were returned. Try reprocessing with a different file or job
          description.
        </p>
        <button onClick={() => window.location.reload()} className="btn-primary inline-flex items-center gap-2">
          <RefreshCw className="w-4 h-4" />
          <span>Try Again</span>
        </button>
      </div>
    )
  }

  /* ── Render ────────────────────────────────────────────────── */
  return (
    <div className="space-y-6">
      {/* ── Header ─────────────────────────────────────────── */}
      <div className="bg-white border border-neutral-200/80 rounded-2xl p-5 md:p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-neutral-900 tracking-tight">
              Recruitment Analysis
            </h1>
            <p className="text-neutral-500 mt-1 text-sm">
              {candidateProfiles.length} candidate{candidateProfiles.length !== 1 ? 's' : ''} evaluated
              {results?.candidates_processed ? ` • ${results.candidates_processed} processed` : ''}
            </p>
          </div>

          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="btn-primary flex items-center justify-center space-x-2 shadow-sm hover:shadow active:scale-95 transition-all"
            >
              <Download className="w-4 h-4" />
              <span>Export Report</span>
            </button>
            {showExportMenu && (
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute right-0 top-full mt-2 w-48 bg-white border border-neutral-200 rounded-xl shadow-lg z-50 overflow-hidden"
              >
                <button
                  onClick={() => handleExport('json')}
                  className="w-full text-left px-4 py-3 text-sm hover:bg-slate-50 flex items-center gap-2.5 transition-colors"
                >
                  <FileText className="w-4 h-4 text-slate-500" />
                  <div>
                    <div className="font-semibold text-neutral-800">JSON Report</div>
                    <div className="text-[11px] text-neutral-400">Full machine-readable data</div>
                  </div>
                </button>
                <button
                  onClick={() => handleExport('csv')}
                  className="w-full text-left px-4 py-3 text-sm hover:bg-slate-50 flex items-center gap-2.5 transition-colors border-t border-neutral-100"
                >
                  <Layers className="w-4 h-4 text-slate-500" />
                  <div>
                    <div className="font-semibold text-neutral-800">CSV Spreadsheet</div>
                    <div className="text-[11px] text-neutral-400">Candidate summary table</div>
                  </div>
                </button>
              </motion.div>
            )}
          </div>
        </div>
      </div>

      {/* ── Executive Summary ──────────────────────────────── */}
      <div className="bg-white border border-neutral-200/80 rounded-2xl p-5 md:p-6 shadow-sm">
        <h2 className="text-lg font-bold text-neutral-900 mb-5 flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center">
            <FileText className="w-4 h-4 text-primary-700" />
          </div>
          <span>Executive Summary</span>
        </h2>

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Candidates', value: candidateProfiles.length, icon: <Users className="w-4 h-4" />, bg: 'bg-slate-50 border-slate-200', color: 'text-slate-800' },
            { label: 'Top Matches', value: topCandidatesCount, icon: <Trophy className="w-4 h-4" />, bg: 'bg-emerald-50 border-emerald-200', color: 'text-emerald-700' },
            { label: 'Avg Confidence', value: `${averageConfidence}%`, icon: <Target className="w-4 h-4" />, bg: 'bg-sky-50 border-sky-200', color: 'text-sky-700' },
            { label: 'Sources Checked', value: overallSourcesChecked, icon: <Globe className="w-4 h-4" />, bg: 'bg-violet-50 border-violet-200', color: 'text-violet-700' },
          ].map((stat, i) => (
            <div key={i} className={`${stat.bg} border rounded-xl p-4 hover:shadow-sm transition-all`}>
              <div className="flex items-center gap-2 mb-1.5">
                <span className={stat.color}>{stat.icon}</span>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{stat.label}</span>
              </div>
              <div className={`text-2xl font-extrabold ${stat.color}`}>{stat.value}</div>
            </div>
          ))}
        </div>

        {/* Summary markdown */}
        {summaryMarkdown && (
          <div className="border-t border-neutral-100 pt-5">
            <div className="prose prose-sm prose-slate max-w-none report-markdown">
              <ReactMarkdown>{summaryMarkdown}</ReactMarkdown>
            </div>
          </div>
        )}

        {/* Key findings */}
        {executiveSummary?.key_findings && Array.isArray(executiveSummary.key_findings) && executiveSummary.key_findings.length > 0 && (
          <div className="border-t border-neutral-100 pt-5 mt-5">
            <h3 className="font-bold text-neutral-800 text-xs uppercase tracking-wider mb-3 flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              Key Findings
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {executiveSummary.key_findings.map((finding: string, i: number) => (
                <div
                  key={i}
                  className="flex items-start gap-2.5 p-3 bg-amber-50/50 border border-amber-100/60 rounded-xl text-sm text-neutral-700 leading-relaxed"
                >
                  <div className="w-5 h-5 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-[10px] font-bold text-amber-700">{i + 1}</span>
                  </div>
                  <span>{finding}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Candidate Controls ─────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-neutral-900 flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center">
            <Users className="w-4 h-4 text-primary-700" />
          </div>
          <span>Candidate Evaluations</span>
          <span className="text-sm font-normal text-neutral-400 ml-1">
            ({filteredCandidates.length} of {candidateProfiles.length})
          </span>
        </h2>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {/* Search */}
          <div className="relative flex-1 sm:flex-initial">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
            <input
              type="text"
              placeholder="Search candidates..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setExpandedCandidate(null)
              }}
              className="w-full sm:w-56 pl-9 pr-3 py-2.5 border border-neutral-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all"
            />
          </div>

          {/* Sort */}
          <div className="flex items-center gap-1.5 bg-white border border-neutral-200 rounded-xl px-2 py-1.5">
            <ArrowUpDown className="w-3.5 h-3.5 text-neutral-400 ml-1" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortKey)}
              className="text-xs font-semibold text-neutral-700 bg-transparent border-none outline-none cursor-pointer"
            >
              <option value="score">Match Score</option>
              <option value="name">Name</option>
              <option value="experience">Experience</option>
            </select>
            <button
              onClick={() => setSortDirection((d) => (d === 'desc' ? 'asc' : 'desc'))}
              className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
              title="Toggle direction"
            >
              {sortDirection === 'desc' ? (
                <TrendingDown className="w-3.5 h-3.5 text-neutral-500" />
              ) : (
                <TrendingUp className="w-3.5 h-3.5 text-neutral-500" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* ── Candidate Cards ────────────────────────────────── */}
      {filteredCandidates.length === 0 ? (
        <div className="bg-white border border-neutral-200/80 rounded-2xl p-12 text-center">
          <Search className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-neutral-600 font-semibold">No candidates match &ldquo;{searchQuery}&rdquo;</p>
          <p className="text-sm text-neutral-400 mt-1">Try a different search term</p>
          <button onClick={() => setSearchQuery('')} className="mt-4 text-sm text-primary-700 hover:text-primary-800 font-semibold">
            Clear search
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredCandidates.map((candidate: any, displayIndex: number) => {
            const candidateName = getFullName(candidate)
            const candidateLocation = getLocation(candidate)
            const candidateEmail = getEmail(candidate)
            const matchScore = getMatchScore(candidate)
            const yearsOfExp = getExperienceYears(candidate)
            const currentRole = getCurrentRole(candidate)
            const currentCompany = getCurrentCompany(candidate)

            const validation = candidate?.validation_assessment || candidate?.verification_status || {}
            const recommendation = candidate?.overall_recommendation || {}
            const professionalSummary = candidate?.professional_summary || {}
            const technicalAssessment = candidate?.technical_assessment || {}
            const isExpanded = expandedCandidate === displayIndex

            const tier = getTierBadge(matchScore)

            const hasRoleOrCompany = currentRole || currentCompany
            const summaryLine = hasRoleOrCompany ? [currentRole, currentCompany].filter(Boolean).join(' at ') : null

            // Radial gauge
            const radius = 18
            const strokeWidth = 3.5
            const circumference = 2 * Math.PI * radius
            const strokeDashoffset = circumference - (matchScore / 100) * circumference
            const scoreColor = getScoreColorClass(matchScore)

            const hasAnyDetail =
              candidate?.executive_summary ||
              professionalSummary?.total_experience_years != null ||
              technicalAssessment?.verified_skills?.high_confidence?.length ||
              technicalAssessment?.verified_skills?.medium_confidence?.length ||
              candidate?.professional_presence ||
              candidate?.research_sources?.length ||
              candidate?.projects?.length ||
              candidate?.experience_summary?.length

            return (
              <motion.div
                key={displayIndex}
                ref={isExpanded ? expandedRef : undefined}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: Math.min(displayIndex * 0.03, 0.2) }}
                className={`bg-white border rounded-2xl shadow-sm transition-all duration-300 overflow-hidden ${
                  isExpanded
                    ? 'border-primary-300 ring-1 ring-primary-100/50 shadow-md'
                    : 'border-neutral-200/80 hover:border-neutral-300 hover:shadow-md'
                }`}
              >
                {/* Header */}
                <div
                  className={`p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer select-none transition-colors ${
                    isExpanded ? 'bg-slate-50/60' : 'hover:bg-slate-50/30'
                  }`}
                  onClick={() => setExpandedCandidate(isExpanded ? null : displayIndex)}
                >
                  <div className="flex items-start gap-4 flex-1 min-w-0">
                    <div className="relative flex-shrink-0">
                      <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-primary-600 to-primary-900 text-white flex items-center justify-center font-bold text-sm shadow-sm">
                        {getInitials(candidateName)}
                      </div>
                      {displayIndex < 3 && matchScore >= 50 && (
                        <div className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-amber-400 text-white flex items-center justify-center shadow-sm">
                          <Trophy className="w-3 h-3" />
                        </div>
                      )}
                    </div>

                    <div className="min-w-0 flex-1 space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-base font-bold text-neutral-900 leading-tight truncate">{candidateName}</h3>
                        <span className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-bold border ${tier.cls}`}>
                          {tier.icon}
                          <span>{tier.label}</span>
                        </span>
                        {validation?.overall_status && (
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border inline-flex items-center gap-1 ${getStatusPillClass(validation.overall_status)}`}>
                            {getStatusIcon(validation.overall_status)}
                            <span>{validation.overall_status}</span>
                          </span>
                        )}
                      </div>

                      {summaryLine ? (
                        <p className="text-sm text-neutral-600 font-medium truncate">{summaryLine}</p>
                      ) : (
                        <p className="text-sm text-neutral-400 italic">Professional summary unavailable</p>
                      )}

                      <div className="flex flex-wrap gap-x-4 gap-y-0.5 pt-0.5">
                        {candidateEmail && (
                          <span className="inline-flex items-center gap-1.5 text-xs text-neutral-500">
                            <Mail className="w-3 h-3 text-neutral-400" />
                            <span className="truncate max-w-[180px]">{candidateEmail}</span>
                          </span>
                        )}
                        {candidateLocation && (
                          <span className="inline-flex items-center gap-1.5 text-xs text-neutral-500">
                            <MapPin className="w-3 h-3 text-neutral-400" />
                            <span>{candidateLocation}</span>
                          </span>
                        )}
                        {yearsOfExp > 0 && (
                          <span className="inline-flex items-center gap-1.5 text-xs text-neutral-500">
                            <Briefcase className="w-3 h-3 text-neutral-400" />
                            <span>
                              {yearsOfExp} {yearsOfExp === 1 ? 'year' : 'years'} exp
                            </span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Gauge + expand */}
                  <div className="flex items-center gap-4 border-t border-neutral-100 md:border-none pt-3 md:pt-0">
                    <div className={`flex items-center gap-3 px-3 py-2 rounded-xl border ${getScoreBgClass(matchScore)}`}>
                      <div className="relative w-10 h-10 flex items-center justify-center">
                        <svg className="w-full h-full -rotate-90">
                          <circle cx="20" cy="20" r={radius} className="stroke-slate-200 fill-none" strokeWidth={strokeWidth} />
                          <circle
                            cx="20" cy="20" r={radius}
                            className={`fill-none transition-all duration-700 ease-out ${scoreColor}`}
                            strokeWidth={strokeWidth}
                            strokeDasharray={circumference}
                            strokeDashoffset={strokeDashoffset}
                            strokeLinecap="round"
                          />
                        </svg>
                        <span className="absolute text-[11px] font-extrabold text-neutral-700">{matchScore}%</span>
                      </div>
                      <div className="text-left">
                        <div className="text-[11px] font-bold text-neutral-700">Match</div>
                        <div className="text-[10px] text-neutral-400">Score</div>
                      </div>
                    </div>

                    <div
                      className={`p-1.5 rounded-lg transition-colors ${
                        isExpanded ? 'bg-primary-100 text-primary-700' : 'hover:bg-slate-100 text-neutral-400'
                      }`}
                    >
                      {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </div>
                  </div>
                </div>

                {/* Expanded body */}
                <AnimatePresence initial={false}>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2, ease: 'easeInOut' }}
                      className="border-t border-neutral-100 bg-slate-50/30 overflow-hidden"
                    >
                      <div className="p-5 md:p-6 space-y-5">
                        {/* No detail state */}
                        {!hasAnyDetail && (
                          <div className="bg-amber-50/60 border border-amber-200 rounded-xl p-6 text-center">
                            <Info className="w-8 h-8 text-amber-400 mx-auto mb-2" />
                            <p className="text-sm font-semibold text-amber-800">Limited candidate data available</p>
                            <p className="text-xs text-amber-600 mt-1">
                              This candidate&apos;s profile couldn&apos;t be enriched from web sources. The resume may
                              have insufficient information for deep analysis.
                            </p>
                          </div>
                        )}

                        {/* Executive Summary */}
                        {candidate?.executive_summary && (
                          <div className="bg-primary-50/50 border border-primary-200/60 rounded-xl p-4 flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <Sparkles className="w-4 h-4 text-primary-700" />
                            </div>
                            <div>
                              <h4 className="text-xs font-bold text-neutral-700 uppercase tracking-wider mb-1.5">
                                AI Executive Summary
                              </h4>
                              <div className="prose prose-sm prose-slate max-w-none report-markdown text-sm">
                                <ReactMarkdown>{candidate.executive_summary}</ReactMarkdown>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Two-Column Layout */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                          {/* LEFT COLUMN */}
                          <div className="space-y-4">
                            {/* Professional Details */}
                            {(professionalSummary?.total_experience_years != null || currentRole || currentCompany) && (
                              <SectionCard icon={<User className="w-4 h-4" />} title="Professional Summary">
                                <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                                  {professionalSummary?.total_experience_years != null && (
                                    <div>
                                      <MetaLabel>Total Experience</MetaLabel>
                                      <MetaValue>{professionalSummary.total_experience_years} Years</MetaValue>
                                    </div>
                                  )}
                                  {currentRole && (
                                    <div>
                                      <MetaLabel>Current Role</MetaLabel>
                                      <MetaValue>{currentRole}</MetaValue>
                                    </div>
                                  )}
                                  {currentCompany && (
                                    <div>
                                      <MetaLabel>Company</MetaLabel>
                                      <MetaValue>{currentCompany}</MetaValue>
                                    </div>
                                  )}
                                  {professionalSummary?.industry && professionalSummary.industry !== 'N/A' && (
                                    <div>
                                      <MetaLabel>Industry</MetaLabel>
                                      <MetaValue>{professionalSummary.industry}</MetaValue>
                                    </div>
                                  )}
                                  {professionalSummary?.specialization && professionalSummary.specialization !== 'N/A' && (
                                    <div className="col-span-2">
                                      <MetaLabel>Specialization</MetaLabel>
                                      <MetaValue>{professionalSummary.specialization}</MetaValue>
                                    </div>
                                  )}
                                </div>
                              </SectionCard>
                            )}

                            {/* Skills */}
                            <SectionCard icon={<Award className="w-4 h-4" />} title="Technical Skills">
                              {(() => {
                                const verifiedSkills = normalizeSkills(
                                  technicalAssessment?.verified_skills?.high_confidence || technicalAssessment?.verified || [],
                                )
                                const claimedSkills = normalizeSkills(
                                  technicalAssessment?.verified_skills?.medium_confidence || technicalAssessment?.claimed || [],
                                )
                                const discoveredSkills = normalizeSkills(technicalAssessment?.discovered || [])

                                if (!verifiedSkills.length && !claimedSkills.length && !discoveredSkills.length) {
                                  return (
                                    <div className="text-center py-6 text-sm text-slate-400 bg-slate-50/60 rounded-xl border border-dashed border-slate-200">
                                      <Code className="w-6 h-6 mx-auto mb-2 text-slate-300" />
                                      No technical skills data available
                                    </div>
                                  )
                                }

                                return (
                                  <div className="space-y-3">
                                    {verifiedSkills.length > 0 && (
                                      <div>
                                        <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full inline-flex items-center gap-1 mb-2">
                                          <CheckCircle className="w-2.5 h-2.5" />
                                          Verified Skills
                                        </span>
                                        <div className="flex flex-wrap gap-1.5">
                                          {verifiedSkills.slice(0, 20).map((skill, i) => (
                                            <span
                                              key={i}
                                              className="px-2.5 py-1 bg-emerald-50 text-emerald-800 border border-emerald-100 rounded-lg text-xs font-semibold"
                                            >
                                              {skill}
                                            </span>
                                          ))}
                                        </div>
                                      </div>
                                    )}

                                    {claimedSkills.length > 0 && (
                                      <div>
                                        <span className="text-[10px] font-bold text-sky-700 bg-sky-50 border border-sky-100 px-2 py-0.5 rounded-full inline-flex items-center gap-1 mb-2">
                                          <Info className="w-2.5 h-2.5" />
                                          Claimed Skills
                                        </span>
                                        <div className="flex flex-wrap gap-1.5">
                                          {claimedSkills.slice(0, 25).map((skill, i) => (
                                            <span
                                              key={i}
                                              className="px-2.5 py-1 bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-medium"
                                            >
                                              {skill}
                                            </span>
                                          ))}
                                        </div>
                                      </div>
                                    )}

                                    {discoveredSkills.length > 0 && (
                                      <div>
                                        <span className="text-[10px] font-bold text-violet-700 bg-violet-50 border border-violet-100 px-2 py-0.5 rounded-full inline-flex items-center gap-1 mb-2">
                                          <Zap className="w-2.5 h-2.5" />
                                          Discovered
                                        </span>
                                        <div className="flex flex-wrap gap-1.5">
                                          {discoveredSkills.slice(0, 15).map((skill, i) => (
                                            <span
                                              key={i}
                                              className="px-2.5 py-1 bg-violet-50 text-violet-800 border border-violet-100 rounded-lg text-xs font-medium"
                                            >
                                              {skill}
                                            </span>
                                          ))}
                                        </div>
                                      </div>
                                    )}

                                    {technicalAssessment?.total_skills > 0 && (
                                      <div className="text-[10px] text-slate-400 pt-2 border-t border-slate-100 flex justify-between">
                                        <span>Total skills identified</span>
                                        <span className="font-bold text-slate-600">{technicalAssessment.total_skills}</span>
                                      </div>
                                    )}
                                  </div>
                                )
                              })()}
                            </SectionCard>
                          </div>

                          {/* RIGHT COLUMN */}
                          <div className="space-y-4">
                            {/* Verification */}
                            <SectionCard icon={<Target className="w-4 h-4" />} title="Verification Status">
                              <div className="space-y-3">
                                <div>
                                  <div className="flex justify-between items-center text-xs font-semibold mb-1.5">
                                    <span className="text-slate-500">Background Integrity Score</span>
                                    <span className="text-slate-800">
                                      {validation?.confidence_score ?? validation?.consistency_score ?? 0}%
                                    </span>
                                  </div>
                                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                                    <div
                                      className={`h-full rounded-full transition-all duration-500 ${
                                        (validation?.confidence_score ?? 0) >= 75
                                          ? 'bg-emerald-500'
                                          : (validation?.confidence_score ?? 0) >= 50
                                            ? 'bg-amber-500'
                                            : 'bg-slate-400'
                                      }`}
                                      style={{ width: `${validation?.confidence_score ?? validation?.consistency_score ?? 0}%` }}
                                    />
                                  </div>
                                </div>

                                <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100">
                                  <div>
                                    <span className="text-slate-400 block mb-0.5">Status</span>
                                    <span className="font-bold text-slate-700">{validation?.overall_status || 'Pending'}</span>
                                  </div>
                                  <div>
                                    <span className="text-slate-400 block mb-0.5">Sources</span>
                                    <span className="font-bold text-slate-700">
                                      {validation?.data_sources_count || candidate?.research_sources?.length || 0} platforms
                                    </span>
                                  </div>
                                </div>

                                {validation?.discrepancies && validation.discrepancies.length > 0 && (
                                  <div className="p-3 bg-rose-50/60 border border-rose-100 rounded-xl space-y-1.5">
                                    <span className="text-[10px] font-bold text-rose-700 uppercase">Discrepancies Found</span>
                                    {validation.discrepancies.map((d: string, i: number) => (
                                      <div key={i} className="flex items-start gap-1.5 text-xs text-rose-800">
                                        <AlertTriangle className="w-3 h-3 text-rose-500 flex-shrink-0 mt-0.5" />
                                        <span>{d}</span>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </SectionCard>

                            {/* Social Footprint */}
                            {candidate?.professional_presence &&
                              (candidate.professional_presence.github_activity ||
                                candidate.professional_presence.github?.metrics ||
                                candidate.professional_presence.linkedin_presence ||
                                candidate.professional_presence.linkedin?.metrics) && (
                                <SectionCard icon={<Globe className="w-4 h-4" />} title="Social Footprint">
                                  <div className="space-y-2.5">
                                    {candidate.professional_presence.github?.metrics && (
                                      <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl text-xs">
                                        <p className="font-bold text-slate-800">GitHub</p>
                                        <p className="text-slate-500 mt-0.5">
                                          {candidate.professional_presence.github.metrics.public_repos} repos •{' '}
                                          {candidate.professional_presence.github.metrics.followers} followers •{' '}
                                          {candidate.professional_presence.github.metrics.total_stars} stars
                                        </p>
                                        <span className="inline-block mt-1.5 text-[10px] font-bold uppercase text-slate-600 bg-slate-200/60 px-1.5 py-0.5 rounded">
                                          {candidate.professional_presence.github.activity_level}
                                        </span>
                                      </div>
                                    )}
                                    {candidate.professional_presence.linkedin?.metrics && (
                                      <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl text-xs">
                                        <p className="font-bold text-slate-800">LinkedIn</p>
                                        <p className="text-slate-500 mt-0.5">
                                          {candidate.professional_presence.linkedin.metrics.connections} connections •{' '}
                                          {candidate.professional_presence.linkedin.metrics.recommendations} recommendations
                                        </p>
                                        <span className="inline-block mt-1.5 text-[10px] font-bold uppercase text-slate-600 bg-slate-200/60 px-1.5 py-0.5 rounded">
                                          {candidate.professional_presence.linkedin.profile_completeness}
                                        </span>
                                      </div>
                                    )}
                                    {candidate.professional_presence.overall_presence_score != null && (
                                      <div className="p-3 bg-primary-50/50 border border-primary-100 rounded-xl flex items-center justify-between text-xs">
                                        <span className="font-semibold text-primary-900">Footprint Score</span>
                                        <span className="text-lg font-extrabold text-primary-700">
                                          {candidate.professional_presence.overall_presence_score}%
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                </SectionCard>
                              )}

                            {/* Recommendation */}
                            {(recommendation?.recommendation || recommendation?.rationale) && (
                              <SectionCard icon={<Medal className="w-4 h-4" />} title="Recommendation">
                                {recommendation.recommendation && (
                                  <span
                                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
                                      recommendation.recommendation.includes('STRONGLY') ||
                                      recommendation.recommendation.includes('HIGHLY')
                                        ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                        : recommendation.recommendation.includes('CONDITIONAL') ||
                                            recommendation.recommendation.includes('CONSIDER')
                                          ? 'bg-amber-50 text-amber-800 border-amber-200'
                                          : recommendation.recommendation.includes('RECOMMEND')
                                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                            : 'bg-rose-50 text-rose-800 border-rose-200'
                                    }`}
                                  >
                                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                    {recommendation.recommendation}
                                  </span>
                                )}
                                {recommendation.rationale && (
                                  <p className="text-sm text-slate-600 leading-relaxed mt-3 pt-3 border-t border-slate-100">
                                    {recommendation.rationale}
                                  </p>
                                )}
                              </SectionCard>
                            )}
                          </div>
                        </div>

                        {/* Strengths & Gaps */}
                        {((candidate?.strengths_and_concerns?.key_strengths || candidate?.match_analysis?.strengths || [])
                          .length > 0 ||
                          (candidate?.strengths_and_concerns?.key_concerns || candidate?.match_analysis?.gaps || [])
                            .length > 0) && (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-emerald-50/30 border border-emerald-200/60 rounded-xl p-4">
                              <h4 className="font-bold text-emerald-800 text-xs uppercase tracking-wider flex items-center gap-2 mb-3">
                                <CheckCircle className="w-3.5 h-3.5" />
                                Key Strengths
                              </h4>
                              {(candidate?.strengths_and_concerns?.key_strengths || candidate?.match_analysis?.strengths || [])
                                .length > 0 ? (
                                <ul className="space-y-2">
                                  {(candidate?.strengths_and_concerns?.key_strengths || candidate?.match_analysis?.strengths || [])
                                    .slice(0, 5)
                                    .map((s: string, i: number) => (
                                      <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                                        <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                                        <span>{s}</span>
                                      </li>
                                    ))}
                                </ul>
                              ) : (
                                <p className="text-sm text-slate-500 italic">No explicit strengths identified.</p>
                              )}
                            </div>

                            <div className="bg-amber-50/30 border border-amber-200/60 rounded-xl p-4">
                              <h4 className="font-bold text-amber-800 text-xs uppercase tracking-wider flex items-center gap-2 mb-3">
                                <AlertTriangle className="w-3.5 h-3.5" />
                                Gaps &amp; Concerns
                              </h4>
                              {(candidate?.strengths_and_concerns?.key_concerns || candidate?.match_analysis?.gaps || [])
                                .length > 0 ? (
                                <ul className="space-y-2">
                                  {(candidate?.strengths_and_concerns?.key_concerns || candidate?.match_analysis?.gaps || [])
                                    .slice(0, 5)
                                    .map((g: string, i: number) => (
                                      <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
                                        <span>{g}</span>
                                      </li>
                                    ))}
                                </ul>
                              ) : (
                                <p className="text-sm text-slate-500 italic">
                                  No critical gaps identified for this role.
                                </p>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Research Sources */}
                        {candidate?.research_sources && candidate.research_sources.length > 0 && (
                          <div className="space-y-3">
                            <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-2">
                              <Globe className="w-3.5 h-3.5 text-primary-700" />
                              Research Sources ({candidate.research_sources.length})
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                              {candidate.research_sources.map((source: any, i: number) => (
                                <div
                                  key={i}
                                  className="p-3.5 bg-white border border-slate-200 rounded-xl hover:shadow-sm hover:border-slate-300 transition-all duration-200"
                                >
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="font-bold text-sm text-slate-800">{source.platform}</span>
                                    {source.verified && (
                                      <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-100 font-bold px-2 py-0.5 rounded-full flex items-center gap-0.5">
                                        <CheckCircle className="w-2.5 h-2.5" />
                                        Verified
                                      </span>
                                    )}
                                  </div>
                                  {source.data_points && (
                                    <div className="space-y-1 text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                                      {Object.entries(source.data_points)
                                        .slice(0, 5)
                                        .map(([key, value]: [string, any]) => (
                                          <div key={key} className="flex justify-between">
                                            <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                                            <span className="font-semibold text-slate-600 truncate max-w-[120px]">
                                              {String(value)}
                                            </span>
                                          </div>
                                        ))}
                                    </div>
                                  )}
                                  {source.profile_url && (
                                    <a
                                      href={source.profile_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-primary-700 hover:text-primary-800 hover:underline inline-flex items-center gap-1 mt-2.5 font-semibold"
                                    >
                                      View Profile <ExternalLink className="w-3 h-3" />
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Projects */}
                        {candidate?.projects && candidate.projects.length > 0 && (
                          <div className="space-y-3">
                            <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-2">
                              <Code className="w-3.5 h-3.5 text-primary-700" />
                              Portfolio &amp; Projects ({candidate.projects.length})
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              {candidate.projects.slice(0, 6).map((project: any, i: number) => (
                                <div
                                  key={i}
                                  className="p-3.5 bg-white border border-slate-200 rounded-xl hover:shadow-sm transition-all duration-200"
                                >
                                  <div className="flex items-start justify-between gap-2">
                                    <h5 className="font-bold text-sm text-slate-800 truncate">{project.name}</h5>
                                    {project.verified && (
                                      <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-100 px-1.5 py-0.3 rounded-full font-bold flex items-center gap-0.5 flex-shrink-0">
                                        <CheckCircle className="w-2.5 h-2.5" />
                                        Verified
                                      </span>
                                    )}
                                  </div>
                                  {project.description && (
                                    <p className="text-xs text-slate-500 mt-1.5 line-clamp-2">{project.description}</p>
                                  )}
                                  <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-slate-50 text-xs">
                                    <span className="text-slate-400 font-medium">{project.source}</span>
                                    <div className="flex items-center gap-3">
                                      {project.metrics && (
                                        <div className="flex items-center gap-2.5 text-slate-500 font-semibold text-[11px]">
                                          <span className="flex items-center">
                                            <Star className="w-3 h-3 text-amber-500 fill-amber-500 mr-0.5" />
                                            {project.metrics.stars || 0}
                                          </span>
                                          <span className="flex items-center">
                                            <GitFork className="w-3 h-3 text-slate-400 mr-0.5" />
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
                                          View <ExternalLink className="w-2.5 h-2.5" />
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
                            <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-2">
                              <Building className="w-3.5 h-3.5 text-primary-700" />
                              Career History
                            </h4>
                            <div className="relative border-l-2 border-slate-200 pl-6 ml-2 space-y-5 pt-1">
                              {candidate.experience_summary.slice(0, 5).map((exp: any, i: number) => (
                                <div key={i} className="relative">
                                  <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-white border-2 border-primary-300 flex items-center justify-center">
                                    <div className="w-1.5 h-1.5 rounded-full bg-primary-600" />
                                  </div>
                                  <div className="space-y-0.5">
                                    <div className="flex flex-wrap items-center gap-x-2">
                                      <span className="font-bold text-sm text-slate-900">{exp.role}</span>
                                      {exp.verification?.verified_linkedin && (
                                        <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-100 px-1.5 py-0.2 rounded-full font-bold inline-flex items-center gap-0.5">
                                          <CheckCircle className="w-2.5 h-2.5" />
                                          LinkedIn Verified
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-slate-500 font-medium text-xs">{exp.company}</p>
                                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
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
                        {candidate?.publications_thought_leadership?.total_count > 0 &&
                          candidate.publications_thought_leadership.articles?.length > 0 && (
                            <div className="space-y-3">
                              <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-2">
                                <BookOpen className="w-3.5 h-3.5 text-primary-700" />
                                Publications ({candidate.publications_thought_leadership.total_count})
                              </h4>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {candidate.publications_thought_leadership.articles
                                  .slice(0, 3)
                                  .map((article: any, i: number) => (
                                    <div
                                      key={i}
                                      className="p-3.5 bg-white border border-slate-200 rounded-xl hover:shadow-sm transition-all duration-200"
                                    >
                                      <a
                                        href={article.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="font-bold text-sm text-primary-700 hover:text-primary-800 hover:underline leading-snug"
                                      >
                                        {article.title}
                                      </a>
                                      <div className="flex items-center justify-between text-xs text-slate-400 mt-2.5 pt-2 border-t border-slate-50">
                                        <span>{article.platform}</span>
                                        <ExternalLink className="w-3 h-3" />
                                      </div>
                                    </div>
                                  ))}
                              </div>
                            </div>
                          )}

                        {/* Data Completeness */}
                        {candidate?.data_completeness && (
                          <SectionCard icon={<Layers className="w-4 h-4" />} title="Data Integrity">
                            <div className="grid grid-cols-3 gap-4 text-center">
                              {[
                                {
                                  value: candidate.data_completeness.resume_completeness_percent,
                                  label: 'Resume',
                                  color: 'text-primary-700',
                                },
                                {
                                  value: candidate.data_completeness.research_completeness_percent,
                                  label: 'Research',
                                  color: 'text-primary-700',
                                },
                                {
                                  value: candidate.data_completeness.overall_completeness_percent,
                                  label: 'Overall',
                                  color: 'text-emerald-600',
                                },
                              ].map((item, i) => (
                                <div key={i} className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                                  <div className={`text-xl font-extrabold ${item.color}`}>{item.value}%</div>
                                  <div className="text-[10px] text-slate-400 font-semibold mt-0.5 uppercase">
                                    {item.label}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </SectionCard>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )
          })}
        </div>
      )}

      {/* ── Footer ──────────────────────────────────────────── */}
      <div className="text-center text-xs text-slate-400 py-4">
        Report generated with HireFlux AI •{' '}
        {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
      </div>
    </div>
  )
}

/* ── Reusable sub-components ──────────────────────────────────── */
function SectionCard({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm">
      <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2.5 mb-3">
        <span className="text-primary-600">{icon}</span>
        <span>{title}</span>
      </h4>
      {children}
    </div>
  )
}

function MetaLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-[10px] text-slate-400 font-semibold block uppercase tracking-wider">{children}</span>
  )
}

function MetaValue({ children }: { children: React.ReactNode }) {
  return <span className="font-semibold text-slate-800 text-sm">{children}</span>
}
