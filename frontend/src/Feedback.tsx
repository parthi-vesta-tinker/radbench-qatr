import { useEffect, useRef, useState } from "react";
import { ThumbsDown, ThumbsUp } from "lucide-react";
import { api, describeError } from "./api";
import type { Review, FeedbackPayload, FeedbackRecord } from "./types";
export function Feedback({
  review,
  open,
  setOpen,
  disabled,
}: {
  review: Review;
  open: boolean;
  setOpen: (v: boolean) => void;
  disabled: boolean;
}) {
  const [reason, setReason] = useState(""),
    [explanation, setExplanation] = useState("");
  const [saving, setSaving] = useState(false),
    [message, setMessage] = useState(""),
    [error, setError] = useState("");
  const [entries, setEntries] = useState<FeedbackRecord[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState("");
  const [historyBusy, setHistoryBusy] = useState(false);
  const [historyAttempt, setHistoryAttempt] = useState(0);
  useEffect(() => {
    let stopped = false;
    setHistoryBusy(true);
    api.feedbackHistory(review.id).then(page => {
      if (!stopped) { setEntries(page.items); setCursor(page.next_cursor); setHistoryError(""); }
    }).catch(e => { if (!stopped) setHistoryError(describeError(e)); })
      .finally(() => { if (!stopped) setHistoryBusy(false); });
    return () => { stopped = true; };
  }, [review.id, historyAttempt]);
  async function loadMore() {
    if (!cursor || historyBusy) return;
    setHistoryBusy(true);
    try { const page = await api.feedbackHistory(review.id, cursor); setEntries(old => [...old, ...page.items]); setCursor(page.next_cursor); setHistoryError(""); }
    catch (e) { setHistoryError(describeError(e)); }
    finally { setHistoryBusy(false); }
  }
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    // happy-dom and older engines lack showModal; fall back to the plain open state.
    if (typeof node.showModal !== "function") { node.open = open; return; }
    if (open && !node.open) node.showModal();
    if (!open && node.open) node.close();
  }, [open]);
  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    // close does not bubble, so Escape never reaches a React synthetic handler.
    // Without this the dialog would shut while state still believed it was open.
    const sync = () => { setOpen(false); setError(""); };
    node.addEventListener("close", sync);
    return () => node.removeEventListener("close", sync);
  }, [setOpen]);
  const pending = useRef<{ payload: string; key: string } | null>(null);
  const result = review.result!;
  async function save(rating: "up" | "down") {
    if (disabled || saving) return;
    if (rating === "down" && !reason) {
      setError("Select a reason.");
      return;
    }
    const payload: FeedbackPayload = {
      result_version: result.result_version,
      rating,
      target: "result",
    };
    if (rating === "down") {
      payload.reason = reason as NonNullable<FeedbackPayload["reason"]>;
      if (explanation.trim()) payload.explanation = explanation.trim();
    }
    const serialized = JSON.stringify(payload);
    if (pending.current?.payload !== serialized)
      pending.current = { payload: serialized, key: crypto.randomUUID() };
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await api.feedback(review.id, payload, pending.current.key);
      pending.current = null;
      setMessage("Feedback saved.");
      setHistoryAttempt(n => n + 1);
      setOpen(false);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Feedback could not be saved. Please retry.",
      );
    } finally {
      setSaving(false);
    }
  }
  return (
    <section
      className="feedback"
      id="feedback-area"
      aria-label="Review feedback"
    >
      <div className="feedback-bar">
        <span>Was this review useful?</span>
        <button
          type="button"
          className="icon-button"
          disabled={disabled || saving}
          aria-label="Thumbs up"
          onClick={() => void save("up")}
        >
          <ThumbsUp />
        </button>
        <button
          type="button"
          className={"icon-button " + (open ? "selected" : "")}
          disabled={disabled || saving}
          aria-label="Thumbs down"
          aria-expanded={open}
          onClick={() => {
            setOpen(!open);
            setMessage("");
          }}
        >
          <ThumbsDown />
        </button>
        <span className="meta" role="status">
          {message}
        </span>
      </div>
      <dialog
        className="feedback-dialog"
        ref={dialog}
        aria-labelledby="feedback-dialog-title"
      >
        <form
          className="feedback-form"
          onSubmit={(e) => {
            e.preventDefault();
            void save("down");
          }}
        >
          <h3 id="feedback-dialog-title">What should we improve?</h3>
          <label htmlFor="feedback-reason">
            What was wrong? <span className="required">Required</span>
          </label>
          <select
            id="feedback-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            required
            disabled={saving || disabled}
          >
            <option value="">Select a reason</option>
            {[
              ["missed_observation", "Missed observation"],
              ["unnecessary_observation", "Unnecessary observation"],
              ["incorrect_observation", "Incorrect observation"],
              ["wrong_grouping", "Wrong grouping"],
              ["unclear_wording", "Unclear wording"],
              ["other", "Other"],
            ].map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <label htmlFor="feedback-details">
            Tell us more <span className="meta">Optional</span>
          </label>
          <textarea
            id="feedback-details"
            rows={3}
            maxLength={2000}
            value={explanation}
            onChange={(e) => setExplanation(e.target.value)}
            disabled={saving || disabled}
          />
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <div className="form-actions">
            <button className="primary" disabled={saving || disabled}>
              {saving ? "Saving…" : "Save"}
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => { setOpen(false); setError(""); }}
            >
              Cancel
            </button>
          </div>
        </form>
      </dialog>
      <details className="feedback-history">
        <summary>Saved feedback{entries.length ? ` · ${entries.length}${cursor ? "+" : ""}` : ""}</summary>
        {historyBusy && <p className="meta" role="status">Loading feedback…</p>}
        {!historyBusy && !entries.length && !historyError && <p className="meta">No feedback recorded.</p>}
        {historyError && <p className="error" role="alert">{historyError} <button type="button" onClick={() => setHistoryAttempt(n => n + 1)}>Retry feedback history</button></p>}
        <ol>{entries.map(entry => <li key={entry.id}>
          <div className="saved-feedback-heading"><strong>{entry.rating === "up" ? "Useful" : "Needs improvement"}</strong><time dateTime={entry.created_at}>{new Date(entry.created_at).toLocaleString()}</time></div>
          <p className="meta">Result v{entry.result_version} · {entry.observation_id ? `Comment ${entry.observation_id.replace('obs-', '')}` : entry.target === 'result' ? 'Whole review' : 'Historical flag feedback'}{entry.reason ? ` · ${entry.reason.replaceAll('_', ' ')}` : ''}</p>
          {entry.explanation && <p>{entry.explanation}</p>}
          {entry.suggested_comment && <p><strong>Suggested wording:</strong> {entry.suggested_comment}</p>}
        </li>)}</ol>
        {cursor && <button type="button" disabled={historyBusy} onClick={() => void loadMore()}>Load more feedback</button>}
      </details>
    </section>
  );
}
