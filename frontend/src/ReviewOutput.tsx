import { useState } from "react";
import { Copy, FileCheck2 } from "lucide-react";
import type { Review } from "./types";
import { Feedback } from "./Feedback";
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
      setCopyStatus("");
      setFallback("");
    } catch {
      setFallback(text);
      setCopyStatus("Clipboard unavailable. Select the text below to copy.");
    }
  }
  return (
    <section className="output" aria-labelledby="output-title">
      <div className="section-heading">
        <h2 id="output-title">Quality review</h2>
        {result?.outcome === "observations" && (
          <button
            type="button"
            aria-label="Copy all comments"
            className="copy-action"
            disabled={stale || disconnected || !result.comments_copy_text}
            onClick={() => void copy(result.comments_copy_text ?? "")}
          >
            <Copy size={16} />
            Copy all
          </button>
        )}
      </div>
      {!review && (
        <div className="empty">
          <FileCheck2 size={26} strokeWidth={1.4} />
          <p>The quality review will appear here.</p>
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
                <div className="group-heading"><h3>PACS comments</h3><button type="button" className="copy-action" disabled={stale || disconnected || !result.general_copy_text} aria-label="Copy PACS comments" onClick={() => void copy(result.general_copy_text ?? "")}><Copy size={16} />Copy</button></div>
                {result.general_comments.length ? (
                  <ul className="comment-list" role="list">
                    {result.general_comments.map((o) => (
                      <li key={o.observation_id}>{o.comment}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="meta">No comments.</p>
                )}
              </div>
              <div className="comment-section">
                <div className="group-heading"><h3>Critical findings</h3><button type="button" className="copy-action" disabled={stale || disconnected || !result.critical_comments_copy_text} aria-label="Copy critical" onClick={() => void copy(result.critical_comments_copy_text ?? "")}><Copy size={16} />Copy</button></div>
                {result.critical_comments.length ? (
                  <ul className="comment-list" role="list">
                    {result.critical_comments.map((o) => (
                      <li key={o.observation_id}>{o.comment}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="meta">No comments.</p>
                )}
              </div>
            </div>
          )}
          {copyStatus && (
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
        </>
      )}
    </section>
  );
}
