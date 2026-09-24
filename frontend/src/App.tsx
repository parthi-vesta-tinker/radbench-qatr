import { ReviewJourney, ReviewContext } from "./ReviewJourney";
import { useEffect, useState } from "react";
import { FileText, History, Plus, MessageSquare, ChartNoAxesColumn, BookOpen, FlaskConical, Moon, Sun, X, Share2, Settings, RefreshCw } from "lucide-react";
import { useReview } from "./useReview";
import { ReviewOutput } from "./ReviewOutput";
import { SystemStatus } from "./SystemStatus";
import { ReviewHistory } from "./ReviewHistory";
import { FeedbackInbox } from "./FeedbackInbox";
import { AnalyticsView } from "./AnalyticsView";
import { SkillsKnowledge } from "./SkillsKnowledge";
import { Studio } from "./Studio";
import { Playground } from "./Playground";
import { TooltipButton } from "./TooltipButton";
import { usePanels } from "./usePanels";
import { PanelIcon } from "./PanelIcon";
import { FeatureNotice } from "./FeatureNotice";

function railTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf())
    ? value
    : date.toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

export default function App() {
  const qa = useReview();
  const panels = usePanels();
  const reportsCollapsed = panels.isCollapsed("reports");
  const studioCollapsed = panels.isCollapsed("studio");
  const modal = panels.size === "mobile" && panels.drawer !== null;
  const [view, setView] = useState<"current" | "history" | "feedback" | "analytics" | "skills" | "playground">("current");
  const [skillsVisited, setSkillsVisited] = useState(false);
  const [playgroundVisited, setPlaygroundVisited] = useState(false);
  const openSkills = () => { setSkillsVisited(true); setView("skills"); panels.close(); };
  const [theme, setTheme] = useState(() => { try { return localStorage.getItem("vesta.theme") === "dark" ? "dark" : "light"; } catch { return "light"; } });
  useEffect(() => { document.documentElement.dataset.theme = theme; try { localStorage.setItem("vesta.theme", theme); } catch { /* Theme still works when persistence is blocked. */ } }, [theme]);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  useEffect(() => setFeedbackOpen(false), [qa.selected]);
  const open = (id: string) => { qa.openReview(id); setView("current"); panels.close(); };
  const showCurrent = () => { if (qa.drafts[0]) qa.openReview(qa.drafts[0].id); setView("current"); panels.close(); };
  const create = () => { qa.newReview(); setView("current"); panels.close(); };
  const active = qa.rows.filter(r => ["queued", "running"].includes(r.execution_status)).slice(0, 20);
  const recent = qa.rows.filter(r => !["queued", "running"].includes(r.execution_status)).slice(0, 20);
  const [pasted, setPasted] = useState(false);
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const refreshWorkspace = () => { qa.refresh(); setHistoryRefresh(value => value + 1); };
  return <>
    <header className="app-header" inert={modal}>
      <div className="brand"><img src="/brand/vestaicon.jpeg" alt="" width="36" height="36"/><div className="brand-titles"><span>Vesta</span><strong>Radiology Report Review</strong></div></div>
      <div className="header-controls" role="group" aria-label="Application controls">
        <TooltipButton className="icon-button" side="bottom" label="Share — coming soon" aria-disabled="true"><Share2 size={19}/></TooltipButton>
        <TooltipButton className="icon-button" side="bottom" label="Settings — coming soon" aria-disabled="true"><Settings size={19}/></TooltipButton>
        <TooltipButton className="icon-button" side="bottom" label="Refresh current data" onClick={refreshWorkspace}><RefreshCw size={19}/></TooltipButton>
        <SystemStatus configurationError={qa.configurationError} retryConfiguration={qa.retryConfiguration}/>
        <TooltipButton className="icon-button" side="bottom" label={`Switch to ${theme === "light" ? "dark" : "light"} theme`} onClick={() => setTheme(theme === "light" ? "dark" : "light")}>{theme === "light" ? <Moon size={19}/> : <Sun size={19}/>}</TooltipButton>
      </div>
    </header>
    <nav className="mobile-panel-controls" aria-label="Workspace panels" inert={modal}>
      <TooltipButton label="Open Report reviews" side="bottom" aria-controls="reports-panel" aria-expanded={panels.drawer === "reports"} onClick={() => panels.toggle("reports")}><PanelIcon side="left" collapsed/><span>Report reviews</span></TooltipButton>
      <TooltipButton label="Open QA Studio" side="bottom" aria-controls="studio-panel" aria-expanded={panels.drawer === "studio"} onClick={() => panels.toggle("studio")}><PanelIcon side="right" collapsed/><span>QA Studio</span></TooltipButton>
    </nav>
    {modal && <div className="panel-backdrop" onClick={panels.close} aria-hidden="true"/>}
    <div className={`workspace panel-workspace ${view !== "current" ? "history-open" : ""} ${reportsCollapsed ? "reports-collapsed" : ""} ${studioCollapsed ? "studio-collapsed" : ""}`}>

      <aside id="reports-panel" className={`scope side-panel ${panels.drawer === "reports" ? "drawer-open" : ""}`}
        role={panels.drawer === "reports" ? "dialog" : undefined} aria-modal={panels.drawer === "reports" ? true : undefined}
        inert={modal && panels.drawer !== "reports"} aria-label="Report reviews">
        <div className="panel-heading"><h2 className="scope-label" hidden={reportsCollapsed}>Report reviews</h2>
          <TooltipButton className="icon-button" side={panels.size === "mobile" ? "left" : "right"} aria-controls="reports-content" aria-expanded={!reportsCollapsed}
            label={panels.size === "mobile" ? "Close Report reviews" : reportsCollapsed ? "Expand Report reviews" : "Collapse Report reviews"}
            onClick={() => panels.size === "mobile" ? panels.close() : panels.toggle("reports")}>
            {panels.size === "mobile" ? <X size={18}/> : <PanelIcon side="left" collapsed={reportsCollapsed}/>}
          </TooltipButton>
        </div>
        {reportsCollapsed && <TooltipButton className={view === "current" ? "selected rail-button" : "rail-button"} label="Current review" side="right" onClick={showCurrent}><FileText size={18}/></TooltipButton>}
        <div id="reports-content" className="reports-content" hidden={reportsCollapsed}>
        <nav className="scope-nav" aria-label="Report reviews">
          <button className={view === "current" ? "selected" : ""} onClick={showCurrent}><FileText size={17}/>Current review</button>
          {[["Active", active], ["Recent", recent]] .map(([title, items]) => <section key={title as string}><p className="report-group-label">{title as string}</p>{(items as typeof qa.rows).map(r => <button className={"report-row " + (qa.selected === r.id && view === "current" ? "selected" : "")} key={r.id} onClick={() => open(r.id)} title={`${r.display_id} · ${r.execution_status.replaceAll("_", " ")} · ${r.preview}`}><span className="rail-preview"><b className="rail-id">{r.display_id}</b><span className="rail-summary">{r.preview}</span></span><time className="rail-time" dateTime={r.created_at}>{railTime(r.created_at)}</time></button>)}</section>)}
        </nav>
        {qa.listError && <p className="error" role="status">Report list unavailable. Reconnecting…</p>}
        <p className="scope-footer">Unsubmitted text stays in this tab.<br/>Submitted reviews are saved.</p>
        </div>
      </aside>
      <div className="work-content" inert={modal}>
      {view === "history" && <ReviewHistory busy={false} openReview={open} refreshToken={historyRefresh}/>}
      {view === "feedback" && <FeedbackInbox openReview={open}/>}
      {view === "analytics" && <AnalyticsView/>}
      {skillsVisited && <SkillsKnowledge active={view === "skills"}/>}
      {playgroundVisited && <Playground active={view === "playground"} openSkills={openSkills}/>}
      <main className="review-workspace" hidden={view !== "current"}>
        <div className="input-pane">
          <div className="section-heading"><h1>{qa.draft ? "New review" : "Report review"}</h1></div>
          <ReviewContext review={qa.review} hasText={Boolean(qa.report.trim())} edited={qa.edited} disconnected={qa.disconnected} pasted={pasted} uncertain={qa.locked && !qa.busy} restore={qa.restore} error={qa.error}/>
          <form className="input-section" onSubmit={e => {e.preventDefault(); if (qa.draft) void qa.submit(); else qa.reviewAgain();}}>
            <textarea id="report-text" aria-label="Report text" value={qa.report} readOnly={qa.locked || qa.busy} onPaste={() => setPasted(true)} onChange={e => {if (e.nativeEvent instanceof InputEvent && e.nativeEvent.inputType !== "insertFromPaste") setPasted(false); qa.editReport(e.target.value);}} maxLength={40000} rows={7} spellCheck={false} aria-describedby="input-help" placeholder="Paste your report, including Findings and Impression."/>
            <div className="input-actions"><ReviewJourney review={qa.review} edited={qa.edited} busy={qa.busy} disconnected={qa.disconnected}/>
              {qa.draft ? <button className="primary" disabled={qa.busy || !qa.config?.ready || !qa.report.trim()}>{qa.busy ? "Submitting…" : qa.draft.key ? "Retry submission" : "Review"}</button> : <button className="primary" disabled={!qa.canReviewAgain || qa.busy || !qa.config?.ready || !qa.report.trim()}>{qa.busy ? "Reviewing…" : qa.locked ? "Retry submission" : "Review again"}</button>}
            </div>
            {qa.configurationError && <div className="notice" role="alert"><p>{qa.configurationError}</p><button type="button" onClick={qa.retryConfiguration}>Retry connection</button></div>}
            {qa.config && !qa.config.ready && <p className="notice">Live review is not configured. Set the backend model and OpenAI key, then restart.</p>}
          </form>
        </div>
        <div className="output-pane">
          <ReviewOutput key={`${qa.review?.id ?? qa.selected}-${qa.review?.input_version ?? 0}`} review={qa.review} stale={qa.stale} disconnected={qa.disconnected} restore={qa.restore} feedbackOpen={feedbackOpen} setFeedbackOpen={setFeedbackOpen}/></div>
      </main>
      </div>
      <aside id="studio-panel" className={`studio-panel side-panel ${panels.drawer === "studio" ? "drawer-open" : ""}`}
        role={panels.drawer === "studio" ? "dialog" : undefined} aria-modal={panels.drawer === "studio" ? true : undefined}
        inert={modal && panels.drawer !== "studio"} aria-label="QA Studio">
        <div className="studio-column">
          <div className="panel-heading"><h2 hidden={studioCollapsed}>QA Studio</h2>
            <TooltipButton className="icon-button" aria-controls="studio-content studio-details" aria-expanded={!studioCollapsed}
              label={panels.size === "mobile" ? "Close QA Studio" : studioCollapsed ? "Expand QA Studio" : "Collapse QA Studio"}
              onClick={() => panels.size === "mobile" ? panels.close() : panels.toggle("studio")}>
              {panels.size === "mobile" ? <X size={18}/> : <PanelIcon side="right" collapsed={studioCollapsed}/>}
            </TooltipButton>
          </div>
          <FeatureNotice hidden={studioCollapsed}/>
          <nav id="studio-content" className="studio-tools" aria-label="QA Studio tools">
            <TooltipButton side={panels.size === "mobile" ? "bottom" : "left"} label="New review" onClick={create}><Plus/><span className="tool-label">New review</span></TooltipButton>
            <TooltipButton side={panels.size === "mobile" ? "bottom" : "left"} label="Review history" aria-pressed={view === "history"} onClick={() => {setView("history"); panels.close();}}><History/><span className="tool-label">Review history</span></TooltipButton>
            <TooltipButton side={panels.size === "mobile" ? "bottom" : "left"} label="Feedbacks" aria-pressed={view === "feedback"} onClick={() => {setView("feedback"); panels.close();}}><MessageSquare/><span className="tool-label">Feedbacks</span></TooltipButton>
            <TooltipButton side={panels.size === "mobile" ? "bottom" : "left"} label="Analytics" aria-pressed={view === "analytics"} onClick={() => {setView("analytics"); panels.close();}}><ChartNoAxesColumn/><span className="tool-label">Analytics</span></TooltipButton>
            <TooltipButton side={panels.size === "mobile" ? "bottom" : "left"} label="Skills" aria-pressed={view === "skills"} onClick={openSkills}><BookOpen/><span className="tool-label">Skills</span></TooltipButton>
            <TooltipButton side={panels.size === "mobile" ? "bottom" : "left"} label="Playground" aria-pressed={view === "playground"} onClick={() => {setPlaygroundVisited(true);setView("playground"); panels.close();}}><FlaskConical/><span className="tool-label">Playground</span></TooltipButton>
          </nav>
        </div>
        <div id="studio-details" className="studio-details" hidden={studioCollapsed || view !== "current"}><Studio review={qa.review} stale={qa.stale || qa.disconnected}/></div>
      </aside>
    </div>
  </>;
}
