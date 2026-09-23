export type ReportReadiness = {
  hasText: boolean;
  hasFindings: boolean;
  hasImpression: boolean;
  findingLabels: number;
  impressionLabels: number;
  hasHistoryOrComparison: boolean;
};

export type Precheck = { level: 'ready' | 'warning'; message: string };

function labelCount(reportText: string, label: 'findings' | 'impression') {
  const inline = label === 'findings'
    ? /(?:^|[^\w])findings?\s*:/gi
    : /(?:^|[^\w])(?:impressions?|conclusions?)\s*:/gi;
  const standalone = label === 'findings'
    ? /^[ \t]*findings?[ \t]*$/gim
    : /^[ \t]*(?:impressions?|conclusions?)[ \t]*$/gim;
  const uppercase = label === 'findings'
    ? /^[ \t]*FINDINGS(?=[ \t])/gm
    : /^[ \t]*(?:IMPRESSION|IMPRESSIONS|CONCLUSION|CONCLUSIONS)(?=[ \t])/gm;
  return [...reportText.matchAll(inline)].length
    + [...reportText.matchAll(standalone)].length
    + [...reportText.matchAll(uppercase)].length;
}

// This is an operator aid only. It never changes the pasted report; backend
// input validation remains the authority before any model request can run.
export function assessReportText(reportText: string): ReportReadiness {
  const hasText = Boolean(reportText.trim());
  const findingLabels = labelCount(reportText, 'findings');
  const impressionLabels = labelCount(reportText, 'impression');
  return {
    hasText,
    hasFindings: findingLabels > 0,
    hasImpression: impressionLabels > 0,
    findingLabels,
    impressionLabels,
    hasHistoryOrComparison: /(?:^|\n)\s*(?:clinical\s+history|history|comparison)\s*(?::|$)/im.test(reportText),
  };
}

export function precheck(readiness: ReportReadiness, pasted: boolean): Precheck {
  if (!readiness.hasText) return { level: 'ready', message: 'Paste a report to begin.' };
  const missing = [
    !readiness.hasFindings && 'Findings',
    !readiness.hasImpression && 'Impression',
  ].filter(Boolean).join(' and ');
  if (missing) {
    return {
      level: 'warning',
      message: `Input check needs attention: add an identifiable ${missing} section before selecting Review.`,
    };
  }
  if ((readiness.findingLabels > 1 || readiness.impressionLabels > 1) && !readiness.hasHistoryOrComparison) {
    return {
      level: 'warning',
      message: 'Input check needs attention: repeated Findings or Impression labels need a History or Comparison heading for the earlier review.',
    };
  }
  if (readiness.findingLabels > 1 || readiness.impressionLabels > 1) {
    return {
      level: 'ready',
      message: 'Input check: prior-review labels detected. The server will verify the current Findings and Impression pair.',
    };
  }
  return {
    level: 'ready',
    message: pasted ? 'Input check: Findings and Impression detected. Ready for review.' : 'Input check: Findings and Impression detected.',
  };
}
