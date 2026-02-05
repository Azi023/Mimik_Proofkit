'use client';

import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useAudits, useDeleteAudit } from '@/lib/hooks/useAudit';
import { formatDateTime, getScoreColor } from '@/lib/utils';
import {
  Loader2,
  ExternalLink,
  Trash2,
  ChevronRight,
  AlertCircle,
} from 'lucide-react';
import type { AuditResponse } from '@/lib/api';

interface AuditListProps {
  status?: string;
  limit?: number;
}

export function AuditList({ status, limit = 20 }: AuditListProps) {
  const { data, isLoading, error } = useAudits({ status, limit });
  const deleteAudit = useDeleteAudit();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
          <p className="text-gray-600">Failed to load audits</p>
          <p className="text-sm text-gray-500 mt-2">
            Check your API key and connection
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!data?.audits?.length) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">🔍</span>
          </div>
          <p className="text-gray-600">No audits yet</p>
          <p className="text-sm text-gray-500 mt-2">
            Create your first audit to get started
          </p>
          <Link href="/audits/new">
            <Button className="mt-4">Create Audit</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {data.audits.map((audit) => (
        <AuditListItem
          key={audit.audit_id}
          audit={audit}
          onDelete={() => deleteAudit.mutate(audit.audit_id)}
          isDeleting={deleteAudit.isPending}
        />
      ))}
    </div>
  );
}

interface AuditListItemProps {
  audit: AuditResponse;
  onDelete: () => void;
  isDeleting: boolean;
}

function AuditListItem({ audit, onDelete, isDeleting }: AuditListItemProps) {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'complete':
        return <Badge variant="success">Complete</Badge>;
      case 'processing':
        return <Badge variant="warning">Processing</Badge>;
      case 'queued':
        return <Badge variant="secondary">Queued</Badge>;
      case 'failed':
        return <Badge variant="error">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const overallScore = audit.scorecard?.OVERALL;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <Link
                href={`/audits/${audit.audit_id}`}
                className="text-lg font-medium text-gray-900 hover:text-blue-600 truncate"
              >
                {audit.url}
              </Link>
              <a
                href={audit.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-gray-600"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-500">
              {getStatusBadge(audit.status)}
              <span>{formatDateTime(audit.created_at)}</span>
              {audit.finding_count !== undefined && (
                <span>{audit.finding_count} findings</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4 ml-4">
            {overallScore !== undefined && (
              <div className="text-center">
                <div
                  className={`text-2xl font-bold ${getScoreColor(overallScore)}`}
                >
                  {overallScore}
                </div>
                <div className="text-xs text-gray-500">Score</div>
              </div>
            )}

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => {
                  e.preventDefault();
                  onDelete();
                }}
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-500" />
                )}
              </Button>

              <Link href={`/audits/${audit.audit_id}`}>
                <Button variant="ghost" size="icon">
                  <ChevronRight className="w-5 h-5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
