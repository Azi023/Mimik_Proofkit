'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCreateAudit } from '@/lib/hooks/useAudit';
import { Loader2 } from 'lucide-react';

const BUSINESS_TYPES = [
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'ecommerce', label: 'E-Commerce' },
  { value: 'saas', label: 'SaaS' },
  { value: 'hospitality', label: 'Hospitality' },
  { value: 'restaurant', label: 'Restaurant' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'agency', label: 'Agency' },
  { value: 'other', label: 'Other' },
];

export function AuditForm() {
  const router = useRouter();
  const createAudit = useCreateAudit();

  const [url, setUrl] = useState('');
  const [mode, setMode] = useState<'fast' | 'full'>('fast');
  const [businessType, setBusinessType] = useState<string>('');
  const [conversionGoal, setConversionGoal] = useState('');
  const [generateConcept, setGenerateConcept] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const result = await createAudit.mutateAsync({
        url,
        mode,
        business_type: businessType || undefined,
        conversion_goal: conversionGoal || undefined,
        generate_concept: generateConcept,
      });

      // Navigate to audit detail page
      router.push(`/audits/${result.audit_id}`);
    } catch (error) {
      console.error('Failed to create audit:', error);
    }
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Create New Audit</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* URL Input */}
          <div className="space-y-2">
            <Label htmlFor="url">Website URL</Label>
            <Input
              id="url"
              type="url"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
            <p className="text-sm text-gray-500">
              Enter the full URL including https://
            </p>
          </div>

          {/* Audit Mode */}
          <div className="space-y-2">
            <Label>Audit Mode</Label>
            <Select value={mode} onValueChange={(v) => setMode(v as 'fast' | 'full')}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="fast">
                  Fast (Homepage only, ~1 min)
                </SelectItem>
                <SelectItem value="full">
                  Full (Crawl site, ~3 min)
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Business Type */}
          <div className="space-y-2">
            <Label>Business Type (Optional)</Label>
            <Select value={businessType} onValueChange={setBusinessType}>
              <SelectTrigger>
                <SelectValue placeholder="Select business type..." />
              </SelectTrigger>
              <SelectContent>
                {BUSINESS_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-sm text-gray-500">
              Helps tailor recommendations to your industry
            </p>
          </div>

          {/* Conversion Goal */}
          <div className="space-y-2">
            <Label htmlFor="goal">Conversion Goal (Optional)</Label>
            <Input
              id="goal"
              placeholder="e.g., Property inquiries, Demo requests"
              value={conversionGoal}
              onChange={(e) => setConversionGoal(e.target.value)}
            />
          </div>

          {/* Generate Concept */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Generate Lovable Prompt</Label>
              <p className="text-sm text-gray-500">
                Create a redesign prompt for Lovable.dev
              </p>
            </div>
            <Switch
              checked={generateConcept}
              onCheckedChange={setGenerateConcept}
            />
          </div>

          {/* Submit */}
          <Button
            type="submit"
            className="w-full"
            disabled={createAudit.isPending || !url}
          >
            {createAudit.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Creating Audit...
              </>
            ) : (
              'Start Audit'
            )}
          </Button>

          {createAudit.isError && (
            <p className="text-sm text-red-600 text-center">
              Failed to create audit. Please check your API key and try again.
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
