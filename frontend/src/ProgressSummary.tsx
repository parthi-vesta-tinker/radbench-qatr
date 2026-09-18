import { Check, Circle, AlertCircle } from 'lucide-react';
import type { Review } from './types';
export function ProgressSummary({review, stale, disconnected}: {review: Review | null; stale: boolean; disconnected: boolean}) {
  if (!review) return null;
  const state = review.execution_status;
  const label = disconnected ? 'Connection lost' : stale ? 'Previous input' : state === 'completed' ? 'Completed' : state === 'failed' ? 'Review failed' : state === 'needs_input' ? 'Input needed' : state === 'queued' ? 'Queued' : 'Reviewing';
  return <div className="progress-summary" role="status" aria-label={`QA review: ${label}`}>
    {state === 'completed' && !stale && !disconnected ? <Check size={15}/> : ['failed','needs_input'].includes(state) ? <AlertCircle size={15}/> : <Circle size={13}/>}
    <span>{label}</span>
    <span className="progress-segments" aria-hidden="true">{review.steps.map(step => <i key={step.step_id} className={step.status}/>)}</span>
    {review.provenance.mode === 'demo' && <span className="meta">Demo</span>}
  </div>;
}
