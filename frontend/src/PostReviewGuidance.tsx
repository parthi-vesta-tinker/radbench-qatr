import type { Review } from "./types";
import { derivePostReviewGuidance } from "./postReviewGuidance.ts";
import { StudioDisclosure } from "./StudioDisclosure";

function GuidanceSteps({ steps }: { steps: string[] }) {
  return <ol className="guidance">{steps.map((step, index) => <li key={step}>
    <span className="guidance-number" aria-hidden="true">{index + 1}</span><span>{step}</span>
  </li>)}</ol>;
}

export function PostReviewGuidance({ review, stale }: { review: Review | null; stale: boolean }) {
  const content = derivePostReviewGuidance(review, stale);
  return <StudioDisclosure key={`${review?.id}:${review?.input_version}:${stale}:${content.kind}`}
    title="Post-review Guidance" expandable={content.kind === "ready" && content.steps.length > 2}
    preview={content.kind === "unavailable" ? <p className="meta">{content.message}</p> : <GuidanceSteps steps={content.steps.slice(0, 2)}/>}
  >
    {content.kind === "ready" && <GuidanceSteps steps={content.steps}/>}
  </StudioDisclosure>;
}
