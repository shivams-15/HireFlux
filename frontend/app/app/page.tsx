'use client'

import { useState, useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
  Brain,
  Upload,
  FileText,
  ArrowLeft,
  Check,
  AlertCircle,
  Loader2,
  ChevronRight,
  Users,
  Target,
  Search,
  Shield,
  BarChart3,
  Download,
  CheckCircle
} from 'lucide-react'
import { uploadCandidates, startProcessing, getJobStatus, checkApiConfig } from '@/lib/api'
import ResultsView from '@/components/ResultsView'
import ProgressView from '@/components/ProgressView'

type Step = 'upload' | 'processing' | 'results'

export default function AppPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>('upload')
  
  // API Config status
  const [apiConfigured, setApiConfigured] = useState(false)
  const [apiServices, setApiServices] = useState<any>({})
  const [checkingConfig, setCheckingConfig] = useState(true)
  
  // Files
  const [candidatesFile, setCandidatesFile] = useState<File | null>(null)
  const [candidatesFilePath, setCandidatesFilePath] = useState<string>('')
  const [candidatesCount, setCandidatesCount] = useState<number>(0)
  const [fileType, setFileType] = useState<string>('')
  const [jobDescription, setJobDescription] = useState<string>('')
  
  // Processing
  const [isProcessing, setIsProcessing] = useState(false)
  const [jobId, setJobId] = useState<string>('')
  const [processingStatus, setProcessingStatus] = useState<any>(null)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState<string>('')

  // Check API configuration on mount
  useEffect(() => {
    const checkConfig = async () => {
      try {
        const config = await checkApiConfig()
        setApiConfigured(config.configured)
        setApiServices(config.services)
      } catch (err) {
        console.error('Failed to check API config:', err)
        setError('Failed to connect to backend. Make sure the backend server is running.')
      } finally {
        setCheckingConfig(false)
      }
    }
    checkConfig()
  }, [])

  const onDropCandidates = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      setCandidatesFile(file)
      setError('')
      
      try {
        const response = await uploadCandidates(file)
        setCandidatesFilePath(response.file_path)
        setCandidatesCount(response.candidates_count)
        setFileType(response.file_type)
      } catch (err: any) {
        setError(err.message || 'Failed to upload file')
      }
    }
  }, [])

  const { getRootProps: getCandidatesRootProps, getInputProps: getCandidatesInputProps, isDragActive: isCandidatesDragActive } = useDropzone({
    onDrop: onDropCandidates,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv'],
      'application/pdf': ['.pdf']
    },
    multiple: false
  })

  const handleStartProcessing = async () => {
    if (!candidatesFilePath || !jobDescription) {
      setError('Please upload a file and provide job description')
      return
    }

    if (!apiConfigured) {
      setError('Backend API keys not configured. Please check backend .env file.')
      return
    }

    setIsProcessing(true)
    setError('')
    setStep('processing')

    try {
      const response = await startProcessing({
        candidates_file: candidatesFilePath,
        job_description: jobDescription
      })

      setJobId(response.job_id)
      
      // Poll for status
      const interval = setInterval(async () => {
        try {
          const status = await getJobStatus(response.job_id)
          setProcessingStatus(status)
          
          if (status.status === 'completed') {
            clearInterval(interval)
            setResults(status.result)
            setStep('results')
            setIsProcessing(false)
          } else if (status.status === 'failed') {
            clearInterval(interval)
            setError(status.message || 'Processing failed')
            setIsProcessing(false)
          }
        } catch (err: any) {
          console.error('Status check error:', err)
        }
      }, 2000)
    } catch (err: any) {
      setError(err.message || 'Failed to start processing')
      setIsProcessing(false)
    }
  }

  const isUploadComplete = candidatesFile !== null && jobDescription !== ''

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <header className="bg-white border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/')}
                className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-neutral-600" />
              </button>
              <div className="flex items-center space-x-2">
                <Brain className="w-8 h-8 text-primary-700" />
                <span className="text-2xl font-bold text-primary-900">HireFlux</span>
              </div>
            </div>
            
            {/* Progress Indicator */}
            <div className="flex items-center space-x-2">
              {[
                { key: 'upload', label: 'Upload', icon: Upload },
                { key: 'processing', label: 'Processing', icon: Brain },
                { key: 'results', label: 'Results', icon: BarChart3 }
              ].map((s, i) => (
                <div key={s.key} className="flex items-center">
                  <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg ${
                    step === s.key 
                      ? 'bg-primary-700 text-white' 
                      : steps.indexOf(step as any) > i 
                        ? 'bg-primary-100 text-primary-700' 
                        : 'bg-neutral-100 text-neutral-500'
                  }`}>
                    <s.icon className="w-4 h-4" />
                    <span className="text-sm font-medium hidden md:inline">{s.label}</span>
                  </div>
                  {i < 2 && (
                    <ChevronRight className="w-4 h-4 text-neutral-400 mx-1" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {/* Loading Config Check */}
          {checkingConfig && (
            <motion.div
              key="checking"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <Loader2 className="w-8 h-8 animate-spin text-primary-700 mb-4" />
              <p className="text-neutral-600">Checking backend configuration...</p>
            </motion.div>
          )}

          {/* API Not Configured Warning */}
          {!checkingConfig && !apiConfigured && (
            <motion.div
              key="not-configured"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-3xl mx-auto"
            >
              <div className="card">
                <div className="flex items-start space-x-4">
                  <AlertCircle className="w-6 h-6 text-error-light flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="text-xl font-semibold text-neutral-900 mb-2">
                      Backend Not Configured
                    </h3>
                    <p className="text-neutral-600 mb-4">
                      The backend API keys are not configured. Please add your GEMINI_API_KEY to the backend .env file.
                    </p>
                    <div className="bg-neutral-100 p-4 rounded-lg mb-4">
                      <p className="text-sm font-mono mb-2">backend/.env</p>
                      <code className="text-sm">GEMINI_API_KEY=your_api_key_here</code>
                    </div>
                    <p className="text-sm text-neutral-600">
                      Get your API key from{' '}
                      <a
                        href="https://makersuite.google.com/app/apikey"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-700 hover:underline"
                      >
                        Google AI Studio
                      </a>
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 1: File Upload */}
          {!checkingConfig && apiConfigured && step === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <div className="max-w-4xl mx-auto">
                {/* Backend Config Status */}
                <div className="mb-6 p-4 bg-success-light/10 border border-success-light rounded-lg">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-success-dark" />
                    <div>
                      <p className="font-medium text-success-dark">Backend Configured</p>
                      <p className="text-sm text-neutral-600">
                        API services: {Object.entries(apiServices).filter(([_, v]) => v).map(([k]) => k).join(', ')}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Candidates Upload */}
                  <div className="card">
                    <h3 className="text-xl font-semibold text-neutral-900 mb-4">
                      Upload Candidates or Resume
                    </h3>
                    
                    <div
                      {...getCandidatesRootProps()}
                      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                        isCandidatesDragActive
                          ? 'border-primary-500 bg-primary-50'
                          : candidatesFile
                          ? 'border-success-light bg-success-light/10'
                          : 'border-neutral-300 hover:border-primary-500'
                      }`}
                    >
                      <input {...getCandidatesInputProps()} />
                      <Upload className={`w-12 h-12 mx-auto mb-4 ${
                        candidatesFile ? 'text-success-light' : 'text-neutral-400'
                      }`} />
                      
                      {candidatesFile ? (
                        <div>
                          <p className="font-medium text-neutral-900 mb-1">
                            {candidatesFile.name}
                          </p>
                          <p className="text-sm text-success-dark">
                            ✓ {candidatesCount} candidate{candidatesCount !== 1 ? 's' : ''} loaded
                            {fileType === 'resume' && ' (Resume PDF)'}
                          </p>
                        </div>
                      ) : (
                        <div>
                          <p className="font-medium text-neutral-900 mb-1">
                            Drop file here
                          </p>
                          <p className="text-sm text-neutral-500">
                            Spreadsheet (.xlsx, .csv) or Resume PDF
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Job Description */}
                  <div className="card">
                    <h3 className="text-xl font-semibold text-neutral-900 mb-4">
                      Job Description
                    </h3>
                    
                    <textarea
                      className="input min-h-[200px] resize-none"
                      placeholder="Paste the job description here including requirements, responsibilities, and qualifications..."
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                    />
                    
                    {jobDescription && (
                      <p className="text-sm text-success-dark mt-2">
                        ✓ Job description added ({jobDescription.length} characters)
                      </p>
                    )}
                  </div>
                </div>

                {error && (
                  <div className="mt-4 p-4 bg-error-light/10 border border-error-light rounded-lg flex items-center space-x-2 text-error-dark">
                    <AlertCircle className="w-5 h-5" />
                    <span>{error}</span>
                  </div>
                )}

                <div className="mt-6 flex justify-end">
                  <button
                    onClick={handleStartProcessing}
                    disabled={!isUploadComplete || isProcessing}
                    className="btn-primary flex items-center space-x-2"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Starting...</span>
                      </>
                    ) : (
                      <>
                        <Brain className="w-4 h-4" />
                        <span>Start AI Analysis</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 2: Processing */}
          {step === 'processing' && (
            <motion.div
              key="processing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <ProgressView status={processingStatus} />
            </motion.div>
          )}

          {/* Step 3: Results */}
          {step === 'results' && results && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <ResultsView results={results} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}

const steps = ['upload', 'processing', 'results']
