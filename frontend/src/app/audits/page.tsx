'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { AuditList } from '@/components/audit/AuditList';
import { Plus } from 'lucide-react';

export default function AuditsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audits</h1>
          <p className="text-gray-600 mt-1">View and manage your website audits</p>
        </div>
        <Link href="/audits/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Audit
          </Button>
        </Link>
      </div>

      <AuditList />
    </div>
  );
}
