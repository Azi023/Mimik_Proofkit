# Frontend Agent (Continued)

### API Client (continued from `src/lib/api.ts`)

```tsx
  completed_at?: string;
  scorecard?: Record<string, number>;
  finding_count?: number;
}

interface ReportResponse {
  audit_id: string;
  url: string;
  scorecard: Record<string, number>;
  findings: Finding[];
  narrative: {
    executive_summary: string;
    quick_wins: string[];
    strategic_priorities: string[];
    rebuild_concept: string[];
  };
  lovable_prompt?: string;
}

interface Finding {
  id: string;
  category: string;
  severity: 'P0' | 'P1' | 'P2' | 'P3';
  title: string;
  summary: string;
  impact: string;
  recommendation: string;
  effort: 'S' | 'M' | 'L';
  tags?: string[];
}

interface ListAuditsParams {
  limit?: number;
  offset?: number;
  status?: string;
}

interface AuditListResponse {
  audits: AuditResponse[];
  total: number;
  limit: number;
  offset: number;
}
```

### Custom Hooks

```tsx
// src/lib/hooks/useAudit.ts
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAudit, getAuditReport, createAudit, listAudits } from '@/lib/api';

export function useAudit(id: string) {
  return useQuery({
    queryKey: ['audit', id],
    queryFn: () => getAudit(id),
    refetchInterval: (data) => {
      // Poll while processing
      if (data?.status === 'queued' || data?.status === 'processing') {
        return 5000; // 5 seconds
      }
      return false;
    },
  });
}

export function useAuditReport(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['audit', id, 'report'],
    queryFn: () => getAuditReport(id),
    enabled,
  });
}

export function useAudits(params?: { limit?: number; status?: string }) {
  return useQuery({
    queryKey: ['audits', params],
    queryFn: () => listAudits(params),
  });
}

export function useCreateAudit() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: createAudit,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audits'] });
    },
  });
}
```

### Report View Page

```tsx
// src/app/audits/[id]/page.tsx
'use client';

import { useParams } from 'next/navigation';
import { useAudit, useAuditReport } from '@/lib/hooks/useAudit';
import { ScoreCard } from '@/components/audit/ScoreCard';
import { FindingsList } from '@/components/report/FindingsList';
import { NarrativeSection } from '@/components/report/NarrativeSection';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Download, Copy, ExternalLink } from 'lucide-react';

const SCORE_CATEGORIES = [
  'OVERALL',
  'PERFORMANCE',
  'SEO',
  'CONVERSION',
  'UX',
  'SECURITY',
  'MAINTENANCE',
];

export default function AuditDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: audit, isLoading: auditLoading } = useAudit(id);
  const { data: report, isLoading: reportLoading } = useAuditReport(
    id,
    audit?.status === 'complete'
  );
  
  if (auditLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }
  
  if (!audit) {
    return <div>Audit not found</div>;
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
            <p className="text-gray-600">
              Analyzing {audit.url}...
            </p>
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
              <span className="text-2xl">❌</span>
            </div>
            <h2 className="text-xl font-semibold mb-2 text-red-600">
              Audit Failed
            </h2>
            <p className="text-gray-600">
              We couldn't complete the audit for {audit.url}
            </p>
            <Button className="mt-4" variant="outline">
              Try Again
            </Button>
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
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </Button>
          <Button variant="outline" size="sm">
            <Copy className="w-4 h-4 mr-2" />
            Copy JSON
          </Button>
        </div>
      </div>
      
      {/* Score Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        {SCORE_CATEGORIES.map((category) => (
          <ScoreCard
            key={category}
            category={category === 'OVERALL' ? 'Overall' : category}
            score={report?.scorecard?.[category] ?? 0}
            className={category === 'OVERALL' ? 'col-span-2 md:col-span-1' : ''}
          />
        ))}
      </div>
      
      {/* Executive Summary */}
      {report?.narrative && (
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
      
      {/* Rebuild Concept */}
      {report?.narrative?.rebuild_concept?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>💡 What We Can Build</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {report.narrative.rebuild_concept.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-green-500 mt-1">✓</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
      
      {/* Lovable Prompt */}
      {report?.lovable_prompt && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>🚀 Lovable.dev Prompt</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                navigator.clipboard.writeText(report.lovable_prompt!);
              }}
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy Prompt
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
          <CardTitle>
            Findings ({report?.findings?.length ?? 0})
          </CardTitle>
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
```

### Narrative Section Component

```tsx
// src/components/report/NarrativeSection.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface NarrativeSectionProps {
  title: string;
  items: string[];
  icon?: string;
}

export function NarrativeSection({ title, items, icon }: NarrativeSectionProps) {
  if (!items || items.length === 0) return null;
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {icon && <span>{icon}</span>}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {items.map((item, index) => (
            <li key={index} className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium">
                {index + 1}
              </span>
              <span className="text-gray-700">{item}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
```

### Dashboard Layout

```tsx
// src/app/layout.tsx
import { Inter } from 'next/font/google';
import { QueryProvider } from '@/lib/providers';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import '@/styles/globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'Mimik ProofKit',
  description: 'Website Audit QA Engine',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <QueryProvider>
          <div className="min-h-screen bg-gray-50">
            <Header />
            <div className="flex">
              <Sidebar />
              <main className="flex-1 p-6">
                {children}
              </main>
            </div>
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
```

### Header Component

```tsx
// src/components/layout/Header.tsx
'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Plus, Settings } from 'lucide-react';

export function Header() {
  return (
    <header className="h-16 border-b bg-white px-6 flex items-center justify-between">
      <Link href="/" className="flex items-center gap-2">
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
```

### Sidebar Component

```tsx
// src/components/layout/Sidebar.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  FileSearch,
  Settings,
  HelpCircle,
} from 'lucide-react';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/audits', label: 'Audits', icon: FileSearch },
  { href: '/settings', label: 'Settings', icon: Settings },
  { href: '/help', label: 'Help', icon: HelpCircle },
];

export function Sidebar() {
  const pathname = usePathname();
  
  return (
    <aside className="w-64 border-r bg-white min-h-[calc(100vh-4rem)]">
      <nav className="p-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || 
            (item.href !== '/' && pathname.startsWith(item.href));
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              )}
            >
              <Icon className="w-5 h-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
```

## Setup Commands

```bash
# Create Next.js app
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir

# Install dependencies
cd frontend
npm install @tanstack/react-query axios lucide-react recharts
npm install -D @types/node

# Install shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input badge select switch
```

## Environment Variables

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/v1
```

## Your Tasks (Phase 3)

1. [ ] Set up Next.js project with TypeScript + Tailwind
2. [ ] Install and configure shadcn/ui components
3. [ ] Implement API client with React Query
4. [ ] Create dashboard home page
5. [ ] Create audit list page with filtering
6. [ ] Create new audit form
7. [ ] Create audit detail/report view
8. [ ] Implement score visualization (charts)
9. [ ] Add findings list with expandable cards
10. [ ] Add Lovable prompt copy feature
11. [ ] Add PDF export functionality
12. [ ] Add settings page for API key management
13. [ ] Add loading and error states
14. [ ] Make responsive for mobile

## Design Guidelines

- **Color Scheme:**
  - Primary: Blue (#3B82F6)
  - Success/Good: Green (#22C55E)
  - Warning/Medium: Yellow (#EAB308)
  - Error/Poor: Red (#EF4444)
  - Background: Gray (#F9FAFB)

- **Typography:**
  - Font: Inter
  - Headings: Bold, Gray-900
  - Body: Regular, Gray-700
  - Captions: Gray-500

- **Components:**
  - Rounded corners (lg)
  - Subtle shadows
  - Clear visual hierarchy
  - Generous whitespace

## Interface Contract

### Input (from API Agent)
- REST API responses
- JSON data for audits and reports

### Output
- User interface for creating audits
- Visual display of audit results
- Export capabilities (PDF, JSON)
