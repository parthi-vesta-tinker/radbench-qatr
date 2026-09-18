import { useState } from "react";
import { Copy, FileCheck2 } from "lucide-react";
import type { Review } from "./types";
import { ProgressSummary } from "./ProgressSummary";
import { Feedback } from "./Feedback";
import { OutcomeLog } from "./OutcomeLog";
export function ReviewOutput({
  review,
  stale,
  disconnected,
  restore,
  feedbackOpen,
  setFeedbackOpen,
}: {
  review: Review | null;
  stale: boolean;
  disconnected: boolean;
  restore: () => void;
  feedbackOpen: boolean;
  setFeedbackOpen: (v: boolean) => void;
}) {
  const [copyStatus, setCopyStatus] = useState(""),
    [fallback, setFallback] = useState("");
  const result =
    review?.execution_status === "completed" ? review.result : null;
  async function copy(text: string) {
    if (!result || stale || disconnected || !text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus("Copied.");
      setFallback("");
    } catch {
      setFallback(text);
      setCopyStatus("Clipboard unavailable. Select the text below to copy.");
    }
  }
  return (
    <section className="output" aria-labelledby="output-title">
      <div className="section-heading">
        <div><h2 id="output-title">QA comments</h2><p className="meta">For radiologist review</p></div>
        {result?.outcome === "observations" && (
          <button
            type="button"
            disabled={stale || disconnected || !result.comments_copy_text}
            onClick={() => void copy(result.comments_copy_text ?? "")}
          >
            <Copy size={16} />
            Copy all comments
          </button>
        )}
      </div>
      <ProgressSummary review={review} stale={stale} disconnected={disconnected} />
      {disconnected && (
        <div className="notice" role="status">
          Connection lost. The current review status is unknown; reconnecting…
        </div>
      )}
      {stale && (
        <div className="notice">
          These results belong to the previous input.{" "}
          <button className="text-button" type="button" onClick={restore}>
            Restore reviewed input
          </button>
        </div>
      )}
      {!review && (
        <div className="empty">
          <FileCheck2 size={26} strokeWidth={1.4} />
          <p>Your QA review will appear here.</p>
          <span className="meta">
            Paste findings and impression, then request review.
          </span>
        </div>
      )}
      {review && ["queued", "running"].includes(review.execution_status) && (
        <div className="empty" role="status">
          <p>Review in progress</p>
          <span className="meta">
            {review.provenance.mode === "demo"
              ? "Running controlled examples through the review workflow."
              : "Reviewing the submitted report."}
          </span>
        </div>
      )}
      {review &&
        ["needs_input", "failed"].includes(review.execution_status) && (
          <div className="notice" role="alert">
            <h3>
              {review.execution_status === "needs_input"
                ? "More information needed"
                : "Review could not finish"}
            </h3>
            <p>{review.error?.message}</p>
            <p className="meta">
              {review.execution_status === "needs_input"
                ? "Select Revise as new draft, update the report, then select Review report."
                : "No completed result is available. Select Revise as new draft to start a new review."}
            </p>
          </div>
        )}
      {result && (
        <>
          {result.outcome === "no_observations" ? (
            <div className="empty clean">
              <FileCheck2 size={26} strokeWidth={1.4} />
              <h3>No actionable observations</h3>
              <p className="meta">In the supplied report.</p>
            </div>
          ) : (
            <div className="comment-document">
              <div className="comment-section">
                <div className="group-heading"><h3>General comments</h3><button type="button" disabled={stale || disconnected || !result.general_copy_text} onClick={() => void copy(result.general_copy_text ?? "")}><Copy size={14} />Copy general</button></div>
                {result.general_comments.length ? (
                  <ol>
                    {result.general_comments.map((o) => (
                      <li key={o.observation_id}>{o.comment}</li>
                    ))}
                  </ol>
                ) : (
                  <p className="meta">No comments.</p>
                )}
              </div>
              <div className="comment-section">
                <div className="group-heading"><h3>Critical findings</h3><button type="button" disabled={stale || disconnected || !result.critical_comments_copy_text} onClick={() => void copy(result.critical_comments_copy_text ?? "")}><Copy size={14} />Copy critical</button></div>
                {result.critical_comments.length ? (
                  <ol>
                    {result.critical_comments.map((o) => (
                      <li key={o.observation_id}>{o.comment}</li>
                    ))}
                  </ol>
                ) : (
                  <p className="meta">No comments.</p>
                )}
              </div>
            </div>
          )}
          {result.outcome === "observations" && (
            <p className="meta copy-note">
              <span role="status">{copyStatus}</span>
            </p>
          )}
          {fallback && !stale && !disconnected && (
            <textarea
              aria-label="Exact copy text"
              className="copy-fallback"
              readOnly
              value={fallback}
              onFocus={(e) => e.target.select()}
              rows={8}
            />
          )}
          <Feedback
            key={review!.id}
            review={review!}
            open={feedbackOpen}
            setOpen={setFeedbackOpen}
            disabled={stale || disconnected}
          />
          <OutcomeLog key={`outcomes-${review!.id}`} reviewId={review!.id} resultVersion={result.result_version} disabled={stale || disconnected}/>
        </>
      )}
    </section>
  );
}
