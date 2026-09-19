import { useEffect, useState } from "react";
import { FileText, History, Plus, Trash2, MessageSquare, ChartNoAxesColumn, BookOpen, Moon, Sun, X } from "lucide-react";
import { useReview } from "./useReview";
import { ReviewOutput } from "./ReviewOutput";
import { SystemStatus } from "./SystemStatus";
import { ReviewHistory } from "./ReviewHistory";
import { FeedbackInbox } from "./FeedbackInbox";
import { AnalyticsView } from "./AnalyticsView";
import { SkillsKnowledge } from "./SkillsKnowledge";
import { Studio } from "./Studio";
export default function App() {
  const qa = useReview();
  const [view, setView] = useState<"current" | "history" | "feedback" | "analytics" | "skills">("current");
  const [skillsVisited, setSkillsVisited] = useState(false);
  const [theme, setTheme] = useState(() => { try { return localStorage.getItem("vesta.theme") === "dark" ? "dark" : "light"; } catch { return "light"; } });
  useEffect(() => { document.documentElement.dataset.theme = theme; try { localStorage.setItem("vesta.theme", theme); } catch { /* Theme still works when persistence is blocked. */ } }, [theme]);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  useEffect(() => setFeedbackOpen(false), [qa.selected]);
  const open = (id: string) => { qa.openReview(id); setView("current"); };
  const create = () => { qa.newReview(); setView("current"); };
  const active = qa.rows.filter(r => ["queued", "running"].includes(r.execution_status));
  const recent = qa.rows.filter(r => !["queued", "running"].includes(r.execution_status));
  return <>
    <header className="app-header">
      <div className="brand"><strong>Vesta</strong><span>/</span><span>Report QA</span></div>
      <div className="header-controls">
        <SystemStatus configurationError={qa.configurationError} retryConfiguration={qa.retryConfiguration}/>
        <button className="icon-button" aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`} title={`${theme === "light" ? "Dark" : "Light"} theme`} onClick={() => setTheme(theme === "light" ? "dark" : "light")}>{theme === "light" ? <Moon size={17}/> : <Sun size={17}/>}</button>
      </div>
    </header>
    {qa.deleted && <div className="undo-bar" role="status"><span>Draft deleted</span><button onClick={qa.undoDelete}>Undo</button><button className="icon-button" aria-label="Dismiss undo" onClick={qa.dismissDelete}><X size={16}/></button></div>}
    <div className={"workspace " + (view !== "current" ? "history-open" : "")}>
      <aside className="scope" aria-label="Reports">
        <h2 className="scope-label">Reports</h2>
        <nav className="scope-nav" aria-label="Reports">
          <button className={view === "current" ? "selected" : ""} onClick={() => setView("current")}><FileText size={17}/>Current report</button>
          {qa.drafts.length > 0 && <p className="report-group-label">Drafts</p>}
          {qa.drafts.map((d, i) => <div className="draft-row" key={d.id}>
            <button className={qa.selected === d.id && view === "current" ? "selected" : ""} onClick={() => open(d.id)}><span>Draft {i + 1}<small>Draft{d.submitting ? " · Submitting" : d.key ? " · Retry needed" : ""}</small></span></button>
            <button className="icon-button delete-draft" disabled={Boolean(d.key || d.submitting)} title="Delete draft" aria-label={`Delete draft ${i + 1}`} onClick={() => qa.deleteDraft(d.id)}><Trash2 size={16}/></button>
          </div>)}
          {[["Active", active], ["Recent", recent]] .map(([title, items]) => <section key={title as string}><p className="report-group-label">{title as string}</p>{(items as typeof qa.rows).map(r => <button className={"report-row " + (qa.selected === r.id && view === "current" ? "selected" : "")} key={r.id} onClick={() => open(r.id)}><span>{r.preview.slice(0, 52)}<small>{r.execution_status.replaceAll("_", " ")} · {r.mode === "demo" ? "Legacy fixture" : "AI"}</small></span></button>)}</section>)}
        </nav>
        {qa.listError && <p className="error" role="status">Report list unavailable. Reconnecting…</p>}
        <p className="scope-footer">Drafts stay in this tab.<br/>Submitted reviews are saved.</p>
      </aside>
      {view === "history" && <ReviewHistory busy={false} openReview={open}/>}
      {view === "feedback" && <FeedbackInbox openReview={open}/>}
      {view === "analytics" && <AnalyticsView/>}
      {skillsVisited && <SkillsKnowledge active={view === "skills"}/>}
      <main className="review-workspace" hidden={view !== "current"}>
        <div className="input-pane">
          <div className="section-heading"><h1>{qa.draft ? "New report" : "Current report"}</h1><span className="badge">Report text only</span></div>
          <form className="input-section" onSubmit={e => {e.preventDefault(); if (qa.draft) void qa.submit(); else qa.reviewAgain();}}>
            <textarea id="report-text" aria-label="Report text" value={qa.report} readOnly={qa.locked || qa.busy} onChange={e => qa.editReport(e.target.value)} maxLength={40000} rows={7} spellCheck={false} aria-describedby="input-help" placeholder={"Findings:\nPaste findings here.\n\nImpression:\nPaste impression here."}/>
            <div className="input-actions"><p className="meta" id="input-help">{qa.draft ? "Include findings and impression in the pasted report." : qa.edited ? "Edited. Reviewing again starts a new review; the current one is unchanged." : "Submitted report. Edit it to review again."}</p>
              {qa.draft ? <button className="primary" disabled={qa.busy || !qa.config?.ready || !qa.report.trim()}>{qa.busy ? "Submitting…" : qa.draft.key ? "Retry submission" : "Review"}</button> : <button className="primary" disabled={!qa.edited || !qa.config?.ready || !qa.report.trim()}>Review again</button>}
            </div>
            {qa.error && <p className="error" role="alert">{qa.error}</p>}
            {qa.configurationError && <div className="notice" role="alert"><p>{qa.configurationError}</p><button type="button" onClick={qa.retryConfiguration}>Retry connection</button></div>}
            {qa.config && !qa.config.ready && <p className="notice">Live review is not configured. Set the backend model and OpenAI key, then restart.</p>}
          </form>
        </div>
        <div className="output-pane"><ReviewOutput key={qa.review?.id ?? qa.selected} review={qa.review} stale={false} disconnected={qa.disconnected} restore={qa.restore} feedbackOpen={feedbackOpen} setFeedbackOpen={setFeedbackOpen}/></div>
      </main>
      <aside className="studio-column"><h2>QA Studio</h2><nav className="studio-tools" aria-label="QA Studio tools">
        <button onClick={create}><Plus/><span>New report</span></button>
        <button aria-pressed={view === "history"} onClick={() => setView("history")}><History/><span>Review history</span></button>
        <button aria-pressed={view === "feedback"} onClick={() => setView("feedback")}><MessageSquare/><span>Feedbacks</span></button>
        <button aria-pressed={view === "analytics"} onClick={() => setView("analytics")}><ChartNoAxesColumn/><span>Analytics</span></button>
        <button className="studio-knowledge-tool" aria-pressed={view === "skills"} onClick={() => {setSkillsVisited(true);setView("skills");}}><BookOpen/><span>Skills &amp; knowledge</span></button>
      </nav></aside>
      {view === "current" && <Studio review={qa.review} stale={qa.disconnected}/>}
    </div>
  </>;
}
