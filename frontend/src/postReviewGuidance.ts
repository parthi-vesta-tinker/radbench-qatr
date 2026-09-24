import type { Review } from "./types";

export type PostReviewGuidanceContent =
  | { kind: "unavailable"; message: string }
  | { kind: "ready"; steps: string[] };

// Derive advice from the current completed result, never from execution progress.
// Future classification and workflow rules belong here, separate from rendering.
export function derivePostReviewGuidance(
  review: Review | null,
  stale: boolean,
): PostReviewGuidanceContent {
  if (stale)
    return { kind: "unavailable", message: "Next steps are available only for a completed review matching the current report with confirmed status." };
  if (review?.execution_status !== "completed" || !review.result)
    return { kind: "unavailable", message: "Next steps will appear after the review is complete." };

  if (review.result.critical_finding_detected)
    return { kind: "ready", steps: [
      "Read the critical findings first.",
      "Confirm the critical designation.",
      "Follow the applicable communication pathway.",
      "Copy the comments into the report.",
      "Rate the review.",
    ] };
  if (review.result.outcome === "observations")
    return { kind: "ready", steps: [
      "Read the comments.",
      "Copy them into the report.",
      "Rate the review.",
    ] };
  return { kind: "ready", steps: [
    "No QA comments to copy.",
    "Rate the review if something was missed.",
  ] };
}
