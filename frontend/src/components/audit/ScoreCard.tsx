'use client';

import { Card, CardContent } from '@/components/ui/card';
import { cn, getScoreColor, getScoreBgColor, getScoreGrade } from '@/lib/utils';

interface ScoreCardProps {
  category: string;
  score: number;
  className?: string;
}

export function ScoreCard({ category, score, className }: ScoreCardProps) {
  const grade = getScoreGrade(score);
  const colorClass = getScoreColor(score);
  const bgClass = getScoreBgColor(score);

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardContent className="p-4">
        <div className="flex flex-col items-center">
          <span className="text-xs text-gray-500 uppercase tracking-wider mb-2">
            {category}
          </span>
          <div
            className={cn(
              'w-16 h-16 rounded-full flex items-center justify-center',
              bgClass
            )}
          >
            <span className={cn('text-2xl font-bold', colorClass)}>{score}</span>
          </div>
          <span className={cn('text-lg font-semibold mt-2', colorClass)}>
            {grade}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

interface ScoreBarProps {
  category: string;
  score: number;
  className?: string;
}

export function ScoreBar({ category, score, className }: ScoreBarProps) {
  const colorClass = getScoreColor(score);

  const getBarColor = (score: number) => {
    if (score >= 90) return 'bg-green-500';
    if (score >= 70) return 'bg-lime-500';
    if (score >= 50) return 'bg-yellow-500';
    if (score >= 30) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className={cn('space-y-1', className)}>
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">{category}</span>
        <span className={cn('font-medium', colorClass)}>{score}</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', getBarColor(score))}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
