'use client';

import { useParams } from 'next/navigation';
import { useAudit, useAuditReport } from '@/lib/hooks/useAudit';
import { ScoreCard } from '@/components/audit/ScoreCard';
import { FindingsList } from '@/components/report/FindingsList';
import { NarrativeSection } from '@/components/report/NarrativeSection';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Download, Copy, ExternalLink, Check } from 'lucide-react';
import { useState } from 'react';
import { downloadReportJson } from '@/lib/api';

const SCORE_CATEGORIES = [
  'OVERALL',
  'PERFORMANCE',
  'SEO',
  'CONVERSION',
  'UX',
  'SECURITY',
];

export default function AuditDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: audit, isLoading: auditLoading } = useAudit(id);
  const { data: report, isLoading: reportLoading } = useAuditReport(
    id,
    audit?.status === 'complete'
  );
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJson = async () => {
    try {
      const blob = await downloadReportJson(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${id}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  if (auditLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (!audit) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Audit not found</h2>
        <p className="text-gray-600 mt-2">
          The requested audit could not be found.
        </p>
      </div>
    );
  }

  // Show processing state
  if (audit.status === 'queued' || audit.status === 'processing') {
    return (
      <div className="max-w-2xl mx-auto py-12">
        <Card>
          <CardContent className="py-12 text-center">
            <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-500" />
            <h2 className="text-xl font-semibold mb-2">
              {audit.status === 'queued' ? 'Audit Queued' : 'Audit in Progress'}
            </h2>
            <p className="text-gray-600">Analyzing {audit.url}...</p>
            <p className="text-sm text-gray-500 mt-2">
              This usually takes 1-3 minutes.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show error state
  if (audit.status === 'failed') {
    return (
      <div className="max-w-2xl mx-auto py-12">
        <Card className="border-red-200">
          <CardContent className="py-12 text-center">
            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">!</span>
            </div>
            <h2 className="text-xl font-semibold mb-2 text-red-600">
              Audit Failed
            </h2>
            <p className="text-gray-600">
              We could not complete the audit for {audit.url}
            </p>
            {audit.error && (
              <p className="text-sm text-red-500 mt-2">{audit.error}</p>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show complete report
  return (
    <div className="max-w-6xl mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold mb-2">Website Audit Report</h1>
          <div className="flex items-center gap-3">
            <a
              href={audit.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline flex items-center gap-1"
            >
              {audit.url}
              <ExternalLink className="w-4 h-4" />
            </a>
            <Badge variant="secondary">
              {new Date(audit.completed_at!).toLocaleDateString()}
            </Badge>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleDownloadJson}>
            <Download className="w-4 h-4 mr-2" />
            Export JSON
          </Button>
        </div>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {SCORE_CATEGORIES.map((category) => (
          <ScoreCard
            key={category}
            category={category === 'OVERALL' ? 'Overall' : category}
            score={report?.scorecard?.[category] ?? audit.scorecard?.[category] ?? 0}
          />
        ))}
      </div>

      {/* Executive Summary */}
      {report?.narrative?.executive_summary && (
        <Card>
          <CardHeader>
            <CardTitle>Executive Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 leading-relaxed">
              {report.narrative.executive_summary}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Quick Wins & Strategic Priorities */}
      {report?.narrative && (
        <div className="grid md:grid-cols-2 gap-6">
          <NarrativeSection
            title="Quick Wins"
            items={report.narrative.quick_wins}
            icon="⚡"
          />
          <NarrativeSection
            title="Strategic Priorities"
            items={report.narrative.strategic_priorities}
            icon="🎯"
          />
        </div>
      )}

      {/* Lovable Prompt */}
      {report?.lovable_prompt && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>🚀 Lovable.dev Prompt</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyToClipboard(report.lovable_prompt!)}
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 mr-2" />
                  Copy Prompt
                </>
              )}
            </Button>
          </CardHeader>
          <CardContent>
            <pre className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-wrap overflow-x-auto">
              {report.lovable_prompt}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Findings */}
      <Card>
        <CardHeader>
          <CardTitle>Findings ({report?.findings?.length ?? 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {reportLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          ) : (
            <FindingsList findings={report?.findings ?? []} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
