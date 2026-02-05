'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AuditList } from '@/components/audit/AuditList';
import { useAudits } from '@/lib/hooks/useAudit';
import { Plus, FileSearch, TrendingUp, AlertCircle } from 'lucide-react';

export default function DashboardPage() {
  const { data } = useAudits({ limit: 5 });

  // Calculate stats
  const totalAudits = data?.total ?? 0;
  const completedAudits =
    data?.audits?.filter((a) => a.status === 'complete').length ?? 0;
  const avgScore =
    completedAudits > 0
      ? Math.round(
          data!.audits
            .filter((a) => a.status === 'complete' && a.scorecard?.OVERALL)
            .reduce((sum, a) => sum + (a.scorecard?.OVERALL ?? 0), 0) /
            completedAudits
        )
      : 0;
  const totalFindings =
    data?.audits?.reduce((sum, a) => sum + (a.finding_count ?? 0), 0) ?? 0;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Welcome to Mimik ProofKit - Your Website Audit QA Engine
          </p>
        </div>
        <Link href="/audits/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Audit
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <FileSearch className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Audits</p>
                <p className="text-2xl font-bold">{totalAudits}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Avg. Score</p>
                <p className="text-2xl font-bold">{avgScore || '-'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <AlertCircle className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Findings</p>
                <p className="text-2xl font-bold">{totalFindings}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <FileSearch className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Completed</p>
                <p className="text-2xl font-bold">{completedAudits}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Audits */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Audits</CardTitle>
          <Link href="/audits">
            <Button variant="outline" size="sm">
              View All
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          <AuditList limit={5} />
        </CardContent>
      </Card>
    </div>
  );
}
