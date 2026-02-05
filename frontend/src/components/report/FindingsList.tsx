'use client';

import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  getSeverityColor,
  getSeverityLabel,
  getEffortLabel,
  cn,
} from '@/lib/utils';
import { ChevronDown, ChevronUp, Filter } from 'lucide-react';
import type { Finding } from '@/lib/api';

interface FindingsListProps {
  findings: Finding[];
}

export function FindingsList({ findings }: FindingsListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string | null>(null);

  // Get unique categories and severities
  const categories = [...new Set(findings.map((f) => f.category))];
  const severities = ['P0', 'P1', 'P2', 'P3'];

  // Filter findings
  const filteredFindings = findings.filter((f) => {
    if (categoryFilter && f.category !== categoryFilter) return false;
    if (severityFilter && f.severity !== severityFilter) return false;
    return true;
  });

  // Group by category
  const groupedFindings: Record<string, Finding[]> = {};
  filteredFindings.forEach((finding) => {
    if (!groupedFindings[finding.category]) {
      groupedFindings[finding.category] = [];
    }
    groupedFindings[finding.category].push(finding);
  });

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={categoryFilter === null ? 'default' : 'outline'}
          size="sm"
          onClick={() => setCategoryFilter(null)}
        >
          All Categories
        </Button>
        {categories.map((cat) => (
          <Button
            key={cat}
            variant={categoryFilter === cat ? 'default' : 'outline'}
            size="sm"
            onClick={() => setCategoryFilter(cat)}
          >
            {cat}
          </Button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          variant={severityFilter === null ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSeverityFilter(null)}
        >
          All Severities
        </Button>
        {severities.map((sev) => (
          <Button
            key={sev}
            variant={severityFilter === sev ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSeverityFilter(sev)}
          >
            {getSeverityLabel(sev)}
          </Button>
        ))}
      </div>

      {/* Findings by category */}
      {Object.entries(groupedFindings).map(([category, categoryFindings]) => (
        <div key={category} className="space-y-2">
          <h3 className="text-lg font-semibold text-gray-700 flex items-center gap-2">
            {category}
            <Badge variant="secondary">{categoryFindings.length}</Badge>
          </h3>

          {categoryFindings.map((finding) => (
            <FindingCard
              key={finding.id}
              finding={finding}
              isExpanded={expandedId === finding.id}
              onToggle={() =>
                setExpandedId(expandedId === finding.id ? null : finding.id)
              }
            />
          ))}
        </div>
      ))}

      {filteredFindings.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No findings match the selected filters
        </div>
      )}
    </div>
  );
}

interface FindingCardProps {
  finding: Finding;
  isExpanded: boolean;
  onToggle: () => void;
}

function FindingCard({ finding, isExpanded, onToggle }: FindingCardProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <div
          className="flex items-start justify-between cursor-pointer"
          onClick={onToggle}
        >
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Badge className={getSeverityColor(finding.severity)}>
                {getSeverityLabel(finding.severity)}
              </Badge>
              <Badge variant="outline">{getEffortLabel(finding.effort)}</Badge>
            </div>
            <h4 className="font-medium text-gray-900">{finding.title}</h4>
            <p className="text-sm text-gray-600 mt-1">{finding.summary}</p>
          </div>

          <Button variant="ghost" size="icon" className="ml-2">
            {isExpanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </Button>
        </div>

        {isExpanded && (
          <div className="mt-4 pt-4 border-t space-y-4">
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-1">
                Business Impact
              </h5>
              <p className="text-sm text-gray-600">{finding.impact}</p>
            </div>

            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-1">
                Recommendation
              </h5>
              <p className="text-sm text-gray-600">{finding.recommendation}</p>
            </div>

            {finding.tags && finding.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {finding.tags.map((tag) => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
