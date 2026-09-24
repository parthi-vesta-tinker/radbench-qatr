import type { ClassificationData } from "./useClassification";
import type { Review } from "./types";
import { FindingClassification } from "./FindingClassification";
import { PostReviewGuidance } from "./PostReviewGuidance";

export function Studio({
  review,
  stale,
  classificationEnabled = true,
  classification,
  openClassification,
}: {
  review: Review | null;
  stale: boolean;
  classificationEnabled?: boolean;
  classification?: ClassificationData;
  openClassification?: () => void;
}) {
  return (
    <aside className="studio" aria-label="Review Studio">
      <PostReviewGuidance review={review} stale={stale}/>
      {classificationEnabled && review?.execution_status === "completed" && review.result?.critical_comments.length ?
        <FindingClassification key={`${review.id}:${review.input_version}`} review={review} stale={stale} data={classification} openAnalysis={openClassification}/> : null}
    </aside>
  );
}
