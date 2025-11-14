/**
 * Confidence color utilities for detections.
 * Centralizes confidence thresholds and color mappings.
 */

export const CONFIDENCE_THRESHOLDS = {
  HIGH: 0.8,
  MEDIUM: 0.6,
} as const;

export type ConfidenceLevel = 'high' | 'medium' | 'low';

/**
 * Get confidence level based on confidence score.
 */
export function getConfidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= CONFIDENCE_THRESHOLDS.HIGH) return 'high';
  if (confidence >= CONFIDENCE_THRESHOLDS.MEDIUM) return 'medium';
  return 'low';
}

/**
 * Get Tailwind CSS class for confidence badge.
 */
export function getConfidenceBadgeClass(confidence: number): string {
  const level = getConfidenceLevel(confidence);

  switch (level) {
    case 'high':
      return 'bg-green-900/50 text-green-200 border-green-700';
    case 'medium':
      return 'bg-yellow-900/50 text-yellow-200 border-yellow-700';
    case 'low':
      return 'bg-red-900/50 text-red-200 border-red-700';
  }
}

/**
 * Get Tailwind CSS text color class for confidence.
 */
export function getConfidenceTextClass(confidence: number): string {
  const level = getConfidenceLevel(confidence);

  switch (level) {
    case 'high':
      return 'text-confidence-high';
    case 'medium':
      return 'text-confidence-medium';
    case 'low':
      return 'text-confidence-low';
  }
}

/**
 * Get color for Leaflet marker based on confidence.
 */
export function getConfidenceMarkerColor(confidence: number): string {
  const level = getConfidenceLevel(confidence);

  switch (level) {
    case 'high':
      return '#22c55e'; // green-500
    case 'medium':
      return '#eab308'; // yellow-500
    case 'low':
      return '#ef4444'; // red-500
  }
}
