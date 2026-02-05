'use client';

import { AuditForm } from '@/components/audit/AuditForm';

export default function NewAuditPage() {
  return (
    <div className="max-w-2xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">New Audit</h1>
        <p className="text-gray-600 mt-1">
          Enter your website URL to start a comprehensive audit
        </p>
      </div>

      <AuditForm />
    </div>
  );
}
