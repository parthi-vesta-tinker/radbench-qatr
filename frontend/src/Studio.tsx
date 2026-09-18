import {
  Check,
  FileText,
  MessageSquare,
  Minus,
  AlertCircle,
} from "lucide-react";
import type { Review } from "./types";
const stages = [
  ["input_validation", "Input validation"],
  ["language_review", "Language review"],
  ["consistency_review", "Consistency review"],
  ["critical_finding_review", "Critical finding review"],
  ["comment_assembly", "Comment assembly"],
];
export function Studio({
  review,
  stale,
  openFeedback,
}: {
  review: Review | null;
  stale: boolean;
  openFeedback: () => void;
}) {
  const state = review?.execution_status;
  const complete = state === "completed";
  let next = "Paste a report containing findings and impression.";
  if (stale)
    next =
      "Review the changed input, or restore the input that produced these results.";
  else if (state === "running" || state === "queued")
    next =
      "The submitted report is being reviewed. Results will appear when all checks finish.";
  else if (state === "needs_input")
    next =
      "Provide the missing minimum information, then request review again.";
  else if (state === "failed")
    next = "Check the error and retry the report when ready.";
  else if (complete && review?.result?.critical_finding_detected)
    next =
      "Copy the QA review for the radiologist. Ask them to confirm the critical designation and follow the applicable communication pathway.";
  else if (complete)
    next =
      review?.result?.outcome === "observations"
        ? "Copy the QA review into your reporting system for radiologist review."
        : "No comments to copy. Use feedback if an observation was missed.";
  return (
    <aside className="studio" aria-label="Review Studio">
      <section className="studio-section">
        <h3>Review steps</h3>
        <ol className="steps">
          {stages.map(([id, label]) => {
            const status =
              review?.steps.find((s) => s.step_id === id)?.status ?? "pending";
            return (
              <li key={id}>
                <span className={"step-icon " + status}>
                  {status === "completed" ? (
                    <Check />
                  ) : status === "failed" || status === "needs_input" ? (
                    <AlertCircle />
                  ) : (
                    <Minus />
                  )}
                </span>
                <span>
                  {label}
                  <small>
                    {status === "running"
                      ? "In progress"
                      : status === "needs_input"
                        ? "Needs input"
                        : status === "failed"
                          ? "Failed"
                          : status === "skipped"
                            ? "Not run"
                            : ""}
                  </small>
                </span>
                <span className="sr-only">{status}</span>
              </li>
            );
          })}
        </ol>
      </section>
      <div className="tool-list">
        <button
          className="tool selected"
          onClick={() =>
            document
              .getElementById("output-title")
              ?.scrollIntoView({ block: "nearest" })
          }
        >
          <FileText />
          QA comments
        </button>
        <button
          className="tool"
          disabled={!complete || stale}
          onClick={openFeedback}
        >
          <MessageSquare />
          Feedback
        </button>
      </div>
      <section className="studio-section">
        <h3>Next step</h3>
        <p>{next}</p>
        <p className="scope-note">
          Report text only.
          <br />
          No image or communication verification.
        </p>
      </section>
    </aside>
  );
}
