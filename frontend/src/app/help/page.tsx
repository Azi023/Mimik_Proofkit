'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  FileSearch,
  Zap,
  Target,
  Shield,
  TrendingUp,
  Palette,
} from 'lucide-react';

const FEATURES = [
  {
    icon: FileSearch,
    title: 'Comprehensive Audits',
    description:
      'Analyze websites across multiple dimensions including performance, SEO, UX, security, and conversion optimization.',
  },
  {
    icon: Zap,
    title: 'Quick Wins',
    description:
      'Get actionable recommendations that can be implemented quickly for immediate impact.',
  },
  {
    icon: Target,
    title: 'Strategic Priorities',
    description:
      'Long-term recommendations tailored to your business type and conversion goals.',
  },
  {
    icon: Shield,
    title: 'Security Analysis',
    description:
      'Identify security vulnerabilities including HTTPS, security headers, and SSL configuration.',
  },
  {
    icon: TrendingUp,
    title: 'Performance Metrics',
    description:
      'Detailed Core Web Vitals analysis with specific optimization recommendations.',
  },
  {
    icon: Palette,
    title: 'Lovable.dev Integration',
    description:
      'Generate ready-to-use prompts for AI website builders to implement your improvements.',
  },
];

const FAQ = [
  {
    question: 'How long does an audit take?',
    answer:
      'A fast audit (homepage only) takes about 1 minute. A full audit (crawling the site) takes 2-3 minutes depending on the site size.',
  },
  {
    question: 'What business types are supported?',
    answer:
      'We support Real Estate, E-Commerce, SaaS, Hospitality, Restaurant, Healthcare, Agency, and general business websites.',
  },
  {
    question: 'How are scores calculated?',
    answer:
      'Scores are calculated based on severity of findings in each category. P0 (Critical) issues have the most impact, followed by P1, P2, and P3.',
  },
  {
    question: 'Can I export reports?',
    answer:
      'Yes! You can export reports as JSON. PDF export is coming soon.',
  },
  {
    question: 'What is the Lovable.dev prompt?',
    answer:
      'It\'s an AI-generated prompt that you can paste directly into Lovable.dev to generate a redesigned website that addresses the audit findings.',
  },
];

export default function HelpPage() {
  return (
    <div className="max-w-4xl mx-auto py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Help & Documentation</h1>
        <p className="text-gray-600 mt-1">
          Learn how to get the most out of ProofKit
        </p>
      </div>

      {/* Features */}
      <Card>
        <CardHeader>
          <CardTitle>Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            {FEATURES.map((feature) => {
              const Icon = feature.icon;
              return (
                <div key={feature.title} className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Icon className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{feature.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {feature.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Quick Start */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Start</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="space-y-4">
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-medium">
                1
              </span>
              <div>
                <h3 className="font-medium text-gray-900">Start the API Server</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Run <code className="bg-gray-100 px-2 py-0.5 rounded">proofkit serve</code> in your terminal
                </p>
              </div>
            </li>
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-medium">
                2
              </span>
              <div>
                <h3 className="font-medium text-gray-900">Configure API Key</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Get your API key with <code className="bg-gray-100 px-2 py-0.5 rounded">proofkit api-key show</code> and add it in Settings
                </p>
              </div>
            </li>
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-medium">
                3
              </span>
              <div>
                <h3 className="font-medium text-gray-900">Create Your First Audit</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Click &quot;New Audit&quot;, enter a URL, and select your audit options
                </p>
              </div>
            </li>
            <li className="flex gap-4">
              <span className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-medium">
                4
              </span>
              <div>
                <h3 className="font-medium text-gray-900">Review Results</h3>
                <p className="text-sm text-gray-600 mt-1">
                  View scores, findings, and AI-generated recommendations
                </p>
              </div>
            </li>
          </ol>
        </CardContent>
      </Card>

      {/* FAQ */}
      <Card>
        <CardHeader>
          <CardTitle>Frequently Asked Questions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {FAQ.map((item) => (
              <div key={item.question}>
                <h3 className="font-medium text-gray-900">{item.question}</h3>
                <p className="text-sm text-gray-600 mt-1">{item.answer}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Support */}
      <Card>
        <CardHeader>
          <CardTitle>Need More Help?</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">
            For bug reports and feature requests, visit our{' '}
            <a
              href="https://github.com/mimik/proofkit/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              GitHub Issues
            </a>
            .
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
