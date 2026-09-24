import { Check, AlertTriangle, CircleX, LoaderCircle, Minus } from 'lucide-react';
import type { CSSProperties } from 'react';
import type { ClassificationData } from './useClassification';
import type {Review} from './types';

type JourneyProps = {
  review: Review|null; edited: boolean; busy: boolean; disconnected: boolean;
  classification?: ClassificationData; classificationEnabled?: boolean;
  hasText: boolean; pasted: boolean; uncertain: boolean; restore: () => void; error: string;
  configurationError?: string; configurationUnavailable?: boolean; retryConfiguration?: () => void;
};

function reviewStage(step?: string) {
  return step === 'input_validation' ? 1 : step === 'combined_review' ? 2 :
    step === 'output_validation' || step === 'comment_assembly' ? 3 : 1;
}

function requestStage(code: string) {
  if (code === 'REVIEW_CONTEXT_TOO_LARGE') return 1;
  return /^(SKILL_|MODEL_|OPENAI_|PROVIDER_)/.test(code) ? 2 : 0;
}

function messageOnly(value: string) {
  return value.replace(/\s*\[[A-Z][A-Z0-9_]*(?:[^\]]*)\]\s*$/, '').trim();
}

export function ReviewJourney({review, edited, busy, disconnected, classification, classificationEnabled = false, hasText, pasted, uncertain, restore, error, configurationError = '', configurationUnavailable = false, retryConfiguration}: JourneyProps) {
  const labels = ['Input','Validate','AI review','Results', ...(classificationEnabled ? ['Classification'] : [])];
  const steps = review?.steps ?? [];
  const setupProblem = Boolean(configurationError || configurationUnavailable);
  const submissionError = Boolean(error && !disconnected);
  const issue = !edited && !submissionError && !setupProblem && (review?.execution_status === 'failed' || review?.execution_status === 'needs_input');
  const activeStep = steps.find(s => ['running','failed','needs_input'].includes(s.status));
  const requestError = configurationError || error;
  const requestErrorCode = requestError.match(/\[([A-Z][A-Z0-9_]*)/)?.[1] || '';
  const requestErrorStage = requestStage(requestErrorCode);
  let current = !review || edited || submissionError ? 0 : review.execution_status === 'queued' ? 1 :
    activeStep ? reviewStage(activeStep.step_id) : review.execution_status === 'completed' ? 3 : 1;
  if (!review && busy) current = 1;
  const completed = !edited && review?.execution_status === 'completed';
  const noCriticalFindings = completed && review?.result?.critical_comments.length === 0;
  const classificationActive = classificationEnabled && completed && !noCriticalFindings;
  const failedClassification = classification?.runs.find(run => run.execution_status === 'failed');
  const classificationIssue = classificationActive &&
    (classification?.error || (failedClassification && (failedClassification.error?.message || 'Classification failed.')));
  const classificationDetail = classificationActive && (classification?.loading ? 'Classifying critical findings.' :
    classification?.runs.length ? 'Classification ready.' : 'Classification unavailable.');
  const messageStage = configurationUnavailable ? 2 : configurationError || submissionError ? requestErrorStage :
    edited || (!review && !busy) ? 0 : classificationActive ? 4 : current;
  const detail = messageOnly(requestError || (configurationUnavailable ? 'Live review is not configured. Set the backend model and OpenAI key, then restart.' :
    uncertain ? 'Submission not confirmed. Retry to check its status.' :
    disconnected ? 'Connection lost. Reconnecting to confirm progress.' :
    classificationIssue || classificationDetail || (issue ? review?.error?.message || 'Review could not finish.' :
    edited ? 'Review again. Changes not reviewed' :
    !review ? hasText ? pasted ? 'Report pasted. Ready for review.' : 'Ready for review.' : 'Paste a report to begin.' :
    completed ? 'Results ready.' : activeStep?.step_id === 'output_validation' ? 'Validating output.' :
    activeStep?.step_id === 'comment_assembly' ? 'Assembling comments.' :
    review.execution_status === 'queued' ? 'Waiting to validate input.' : 'Review in progress.')));
  const problem = Boolean(setupProblem || classificationIssue || error || issue || disconnected || uncertain);
  const messagePosition = labels.length === 5 ? (messageStage < 4 ? (messageStage + 0.5) / 5.7 : 4.85 / 5.7) : (messageStage + 0.5) / 4;
  return <nav className="review-journey" aria-label="Review progress" style={{'--message-position': `${messagePosition * 100}%`} as CSSProperties}>
    <ol style={{gridTemplateColumns: labels.length === 5 ? 'repeat(4, minmax(0, 1fr)) minmax(60px, 1.7fr)' : 'repeat(4, minmax(0, 1fr))'}}>{labels.map((label, i) => {
      const done = Boolean(review) && (i < current || (completed && i === current));
      const isClassification = i === 4;
      const active = !isClassification && i === current;
      const classificationState = !completed ? 'pending' : noCriticalFindings ? 'not-applicable' : classification?.error ? 'unknown' : classification?.loading ? 'current' : classification?.runs.some(run => run.execution_status === 'failed') ? 'blocked' : classification?.runs.length ? 'complete' : 'unavailable';
      const state = isClassification ? (disconnected && completed ? 'unknown' : classificationState) : i === messageStage && (setupProblem || submissionError) ? 'blocked' : active && setupProblem ? 'pending' : active && (disconnected || uncertain) ? 'unknown' : active && issue ? 'blocked' : done ? 'complete' : active ? 'current' : 'pending';
      return <li key={label} className={state} title={state === 'not-applicable' ? 'Not applicable — no critical findings reported' : undefined} aria-current={state === 'current' ? 'step' : undefined} aria-describedby={i === messageStage ? 'input-help' : undefined}>
        <span className="journey-node" aria-hidden="true">{state === 'not-applicable' ? <Minus/> : state === 'unknown' ? <AlertTriangle/> : state === 'blocked' ? review?.execution_status === 'needs_input' ? <AlertTriangle/> : <CircleX/> : state === 'complete' ? <Check/> : (isClassification ? state === 'current' : active && busy) ? <LoaderCircle className="journey-spinner"/> : null}</span>
        <span>{label}</span><span className="sr-only">{state === 'not-applicable' ? ': not applicable — no critical findings reported' : state === 'blocked' ? review?.execution_status === 'needs_input' ? ': needs input' : ': failed' : `: ${state}`}</span>
      </li>;
    })}</ol>
    <div className={`journey-message${problem ? ' journey-message-problem' : ''}${edited ? ' journey-message-edited' : ''}`} id="input-help" role={problem ? 'alert' : 'status'}>
      <span className="sr-only">{labels[messageStage]}: </span>{detail}
      {edited && <button className="linklike" type="button" onClick={restore}>Restore change</button>}
      {configurationError && retryConfiguration && <> <button className="linklike" type="button" onClick={retryConfiguration}>Retry connection</button></>}
    </div>
  </nav>;
}
