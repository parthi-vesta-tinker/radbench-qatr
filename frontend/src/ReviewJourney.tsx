import { Check, AlertTriangle, CircleX, LoaderCircle, Minus } from 'lucide-react';
import type { ClassificationData } from './useClassification';
import type {Review} from './types';

type JourneyProps = {review:Review|null; edited:boolean; busy:boolean; disconnected:boolean; classification?: ClassificationData; classificationEnabled?: boolean};
export function ReviewJourney({review, edited, busy, disconnected, classification, classificationEnabled = false}: JourneyProps) {
  const labels = ['Input','Validate','AI review','Results', ...(classificationEnabled ? ['Classification'] : [])];
  const steps = review?.steps ?? [];
  const issue = !edited && (review?.execution_status === 'failed' || review?.execution_status === 'needs_input');
  const activeStep = steps.find(s => ['running','failed','needs_input'].includes(s.status));
  let current = !review || edited ? 0 : review.execution_status === 'queued' ? 1 :
    activeStep?.step_id === 'input_validation' ? 1 : activeStep?.step_id === 'combined_review' ? 2 : 3;
  if (!review && busy) current = 1;
  const completed = !edited && review?.execution_status === 'completed';
  const noCriticalFindings = completed && review?.result?.critical_comments.length === 0;
  return <nav className="review-journey" aria-label="Review progress">
    <ol style={{gridTemplateColumns: labels.length === 5 ? 'repeat(4, minmax(0, 1fr)) minmax(60px, 1.7fr)' : 'repeat(4, minmax(0, 1fr))'}}>{labels.map((label, i) => {
      const done = i < current || (completed && i === current);
      const isClassification = i === 4;
      const active = !isClassification && i === current;
      const classificationState = !completed ? 'pending' : noCriticalFindings ? 'not-applicable' : classification?.error ? 'unknown' : classification?.loading ? 'current' : classification?.runs.some(run => run.execution_status === 'failed') ? 'blocked' : classification?.runs.length ? 'complete' : 'unavailable';
      const state = isClassification ? (disconnected && completed ? 'unknown' : classificationState) : active && disconnected ? 'unknown' : active && issue ? 'blocked' : done ? 'complete' : active ? 'current' : 'pending';
      return <li key={label} className={state} title={state === 'not-applicable' ? 'Not applicable — no critical findings reported' : undefined} aria-current={state === 'current' ? 'step' : undefined}>
        <span className="journey-node" aria-hidden="true">{state === 'not-applicable' ? <Minus/> : state === 'unknown' ? <AlertTriangle/> : state === 'blocked' ? review?.execution_status === 'needs_input' ? <AlertTriangle/> : <CircleX/> : state === 'complete' ? <Check/> : (isClassification ? state === 'current' : active && busy) ? <LoaderCircle className="journey-spinner"/> : null}</span>
        <span>{label}</span><span className="sr-only">{state === 'not-applicable' ? ': not applicable — no critical findings reported' : state === 'blocked' ? review?.execution_status === 'needs_input' ? ': needs input' : ': failed' : `: ${state}`}</span>
      </li>;
    })}</ol>

  </nav>;
}

export function ReviewContext({review, hasText, edited, disconnected, pasted, uncertain, restore, error}: {
  review:Review|null; hasText:boolean; edited:boolean; disconnected:boolean; pasted:boolean; uncertain:boolean; restore:()=>void; error:string;
}) {
  const issue = !edited && (review?.execution_status === 'failed' || review?.execution_status === 'needs_input');
  const completed = !edited && review?.execution_status === 'completed';
  const activeStep = review?.steps.find(s => ['running','failed','needs_input'].includes(s.status));
  const detail = error || (uncertain ? 'Submission not confirmed. Retry to check its status.' : disconnected ? 'Connection lost. Reconnecting to confirm progress.' : issue ? review?.error?.message :
    edited ? 'Changes haven’t been reviewed. Comments below refer to the previous text.' : !review ? (hasText ? pasted ? 'Report pasted. Ready for review.' : 'Ready for review.' : 'Paste a report to begin.') :
    completed ? 'Results ready.' : activeStep?.step_id === 'output_validation' ? 'Validating output.' :
    activeStep?.step_id === 'comment_assembly' ? 'Assembling comments.' : review.execution_status === 'queued' ? 'Waiting to validate input.' : 'Review in progress.');
  return <p className="meta review-context" id="input-help" role={issue || error ? "alert" : "status"}>{detail}{edited && <> <button className="linklike" type="button" onClick={restore}>Restore reviewed text</button></>}</p>;
}
