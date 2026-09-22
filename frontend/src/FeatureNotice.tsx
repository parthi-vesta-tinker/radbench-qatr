import { useState } from 'react';
import { Sparkles, X } from 'lucide-react';
import { TooltipButton } from './TooltipButton';

const noticeKey = 'vesta.notice.collapsible-panels.v1';
export function FeatureNotice({ hidden }: { hidden: boolean }) {
  const [dismissed, setDismissed] = useState(() => {
    try { return localStorage.getItem(noticeKey) === 'dismissed'; } catch { return false; }
  });
  if (dismissed) return null;
  return <div className="feature-notice" hidden={hidden} aria-label="New feature">
    <Sparkles size={14} aria-hidden="true"/>
    <span>New: Collapsible panels</span>
    <TooltipButton label="Dismiss feature notice" className="notice-close" onClick={() => {
      setDismissed(true);
      try { localStorage.setItem(noticeKey, 'dismissed'); } catch { /* Dismiss for this session. */ }
    }}><X size={14}/></TooltipButton>
  </div>;
}
