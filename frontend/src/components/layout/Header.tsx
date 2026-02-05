'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Plus, Settings } from 'lucide-react';

export function Header() {
  return (
    <header className="h-16 border-b bg-white px-6 flex items-center justify-between">
      <Link href="/" className="flex items-center gap-2">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-sm">PK</span>
        </div>
        <span className="text-xl font-bold text-gray-900">
          Mimik ProofKit
        </span>
      </Link>

      <div className="flex items-center gap-4">
        <Link href="/audits/new">
          <Button size="sm">
            <Plus className="w-4 h-4 mr-2" />
            New Audit
          </Button>
        </Link>
        <Link href="/settings">
          <Button variant="ghost" size="icon">
            <Settings className="w-5 h-5" />
          </Button>
        </Link>
      </div>
    </header>
  );
}
