'use client'

import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { 
  Brain, 
  Search, 
  Shield, 
  FileCheck, 
  BarChart3, 
  ArrowRight,
  Sparkles,
  Users,
  Target
} from 'lucide-react'

export default function LandingPage() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-neutral-200 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Brain className="w-8 h-8 text-primary-700" />
            <span className="text-2xl font-bold text-primary-900">HireFlux</span>
          </div>
          <button
            onClick={() => router.push('/app')}
            className="btn-primary flex items-center space-x-2"
          >
            <span>Get Started</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <div className="inline-flex items-center space-x-2 bg-primary-50 text-primary-700 px-4 py-2 rounded-full mb-6">
              <Sparkles className="w-4 h-4" />
              <span className="text-sm font-medium">AI-Powered Recruitment</span>
            </div>
            
            <h1 className="text-6xl font-bold text-neutral-900 mb-6 leading-tight">
              Find the Perfect Candidate
              <br />
              <span className="text-primary-700">Powered by AI</span>
            </h1>
            
            <p className="text-xl text-neutral-600 mb-10 max-w-3xl mx-auto">
              Advanced AI agents analyze, research, and validate candidates to provide 
              comprehensive recruitment insights in minutes, not weeks.
            </p>
            
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => router.push('/app')}
                className="btn-primary text-lg flex items-center space-x-2"
              >
                <span>Start Analyzing</span>
                <ArrowRight className="w-5 h-5" />
              </button>
              <button className="btn-secondary text-lg">
                Watch Demo
              </button>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-700 mb-2">95%</div>
              <div className="text-neutral-600">Accuracy Rate</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-700 mb-2">10x</div>
              <div className="text-neutral-600">Faster Screening</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-700 mb-2">5+</div>
              <div className="text-neutral-600">AI Agents</div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-neutral-50">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-neutral-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-neutral-600 max-w-2xl mx-auto">
              Our AI-powered pipeline processes candidates through five specialized agents
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="card hover:shadow-md transition-shadow duration-200"
              >
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary-700" />
                </div>
                <h3 className="text-xl font-semibold text-neutral-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-neutral-600">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Process Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-neutral-900 mb-4">
              Simple, Powerful Process
            </h2>
            <p className="text-xl text-neutral-600 max-w-2xl mx-auto">
              Get comprehensive recruitment insights in three easy steps
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {steps.map((step, index) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="relative"
              >
                <div className="flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-primary-700 text-white rounded-full flex items-center justify-center text-2xl font-bold mb-4">
                    {index + 1}
                  </div>
                  <h3 className="text-xl font-semibold text-neutral-900 mb-2">
                    {step.title}
                  </h3>
                  <p className="text-neutral-600">
                    {step.description}
                  </p>
                </div>
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-[60%] w-[80%] h-0.5 bg-neutral-200" />
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary-700">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl font-bold text-white mb-6">
              Ready to Transform Your Hiring Process?
            </h2>
            <p className="text-xl text-primary-100 mb-8">
              Start analyzing candidates with AI-powered precision today
            </p>
            <button
              onClick={() => router.push('/app')}
              className="bg-white text-primary-700 hover:bg-primary-50 font-medium px-8 py-4 rounded-lg transition-colors duration-200 text-lg flex items-center space-x-2 mx-auto"
            >
              <span>Get Started Now</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-neutral-900 text-neutral-400 py-12">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Brain className="w-6 h-6 text-primary-500" />
            <span className="text-xl font-bold text-white">HireFlux</span>
          </div>
          <p className="mb-4">AI-Powered Recruitment Platform</p>
          <p className="text-sm">© 2026 HireFlux. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

const features = [
  {
    icon: FileCheck,
    title: 'Resume Analysis',
    description: 'AI-powered extraction and analysis of candidate resumes with comprehensive skill mapping',
  },
  {
    icon: Target,
    title: 'Smart Matching',
    description: 'Advanced semantic matching between candidate profiles and job requirements',
  },
  {
    icon: Search,
    title: 'Deep Research',
    description: 'Comprehensive web research across LinkedIn, GitHub, and professional platforms',
  },
  {
    icon: Shield,
    title: 'Validation',
    description: 'Multi-layer identity and information verification for authentic candidate profiles',
  },
  {
    icon: BarChart3,
    title: 'Analytics',
    description: 'Detailed insights, scoring, and executive-ready reports for decision making',
  },
  {
    icon: Users,
    title: 'Batch Processing',
    description: 'Process multiple candidates simultaneously with intelligent prioritization',
  },
]

const steps = [
  {
    title: 'Upload Data',
    description: 'Upload candidate spreadsheet and job description',
  },
  {
    title: 'AI Processing',
    description: 'Our AI agents analyze, research, and validate all candidates',
  },
  {
    title: 'Get Insights',
    description: 'Review comprehensive reports and make informed decisions',
  },
]
