import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getScoreColor(score: number): string {
  if (score >= 90) return 'text-green-600';
  if (score >= 70) return 'text-lime-600';
  if (score >= 50) return 'text-yellow-600';
  if (score >= 30) return 'text-orange-600';
  return 'text-red-600';
}

export function getScoreBgColor(score: number): string {
  if (score >= 90) return 'bg-green-100';
  if (score >= 70) return 'bg-lime-100';
  if (score >= 50) return 'bg-yellow-100';
  if (score >= 30) return 'bg-orange-100';
  return 'bg-red-100';
}

export function getScoreGrade(score: number): string {
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'P0':
      return 'bg-red-100 text-red-800';
    case 'P1':
      return 'bg-orange-100 text-orange-800';
    case 'P2':
      return 'bg-yellow-100 text-yellow-800';
    case 'P3':
      return 'bg-blue-100 text-blue-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function getSeverityLabel(severity: string): string {
  switch (severity) {
    case 'P0':
      return 'Critical';
    case 'P1':
      return 'High';
    case 'P2':
      return 'Medium';
    case 'P3':
      return 'Low';
    default:
      return severity;
  }
}

export function getEffortLabel(effort: string): string {
  switch (effort) {
    case 'S':
      return 'Quick Fix';
    case 'M':
      return 'Medium Effort';
    case 'L':
      return 'Major Project';
    default:
      return effort;
  }
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
