import { useEffect, useRef, useState } from "react";
import { api, ApiError, describeError } from "./api";
import type { Config, Review, ReviewSummary } from "./types";
export type Draft = { id: string; text: string; key?: string; submitting?: boolean; error?: string };
const ACTIVE = "vesta.qa.v05.activeReview";
const makeDraft = (text = ""): Draft => ({ id: "draft-" + crypto.randomUUID(), text });
export function useReview() {
  const [config, setConfig] = useState<Config | null>(null);
  const [configurationError, setConfigurationError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [drafts, setDrafts] = useState<Draft[]>(() => sessionStorage.getItem(ACTIVE) ? [] : [makeDraft()]);
  const [selected, setSelected] = useState(() => sessionStorage.getItem(ACTIVE) || "");
  const selectedRef = useRef(selected); selectedRef.current = selected;
  const [review, setReview] = useState<Review | null>(null);
  const [disconnected, setDisconnected] = useState(false);
  const [error, setError] = useState("");
  const [rows, setRows] = useState<ReviewSummary[]>([]);
  const [listError, setListError] = useState("");
  const [revision, setRevision] = useState(0);
  // Local edits to an already submitted report. Never mutates the accepted review.
  const [edits, setEdits] = useState<Record<string, string>>({});
  const editedText = edits[selected] ?? null;
  const setEditedText = (text: string | null) => setEdits(old => {
    const next = {...old}; if (text === null) delete next[selected]; else next[selected] = text; return next;
  });
  const [replacements, setReplacements] = useState<Record<string, {text:string; key:string; version:number; busy:boolean; error?:string}>>({});
  const replacement = replacements[selected];
  const submittingIds = useRef(new Set<string>());
  const draft = selected ? drafts.find(d => d.id === selected) : drafts[0];
  const active = draft ? null : selected;
  const visibleReview = !draft && review?.id === active ? review : null;
  const submittedText = visibleReview?.input.report_text ?? "";
  const report = draft?.text ?? editedText ?? submittedText;
  const edited = !draft && editedText !== null && editedText !== submittedText;
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (drafts.some(d => d.text.trim()) || Object.keys(edits).length) { event.preventDefault(); event.returnValue = ""; } };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [drafts, edits]);
  const retryConfiguration = () => setAttempt(n => n + 1);
  useEffect(() => {
    let stopped = false; setConfig(null); setConfigurationError("");
    api.config().then(c => { if (!stopped) setConfig(c); })
      .catch(e => { if (!stopped) setConfigurationError(describeError(e)); });
    return () => { stopped = true; };
  }, [attempt]);
  useEffect(() => {
    let stopped = false; let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        // Active work is fetched independently so older queued reviews cannot disappear behind recent results.
        const [recent, running, queued] = await Promise.all([
          api.history("limit=20"), api.history("status=running&limit=100"), api.history("status=queued&limit=100")
        ]);
        if (stopped) return;
        setRows([...new Map([...running.items, ...queued.items, ...recent.items].map(r => [r.id, r])).values()]);
        setListError("");
      } catch(e) { if (!stopped) setListError(describeError(e)); }
      if (!stopped) timer = setTimeout(poll, 3000);
    }
    void poll(); return () => { stopped = true; clearTimeout(timer); };
  }, [revision]);
  useEffect(() => {
    setReview(old => old?.id === active ? old : null); setDisconnected(false); setError("");
    if (!active) return;
    let stopped = false; let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const data = await api.get(active!); if (stopped) return;
        setReview(data); setDisconnected(false); setError("");
        if (["queued", "running"].includes(data.execution_status)) timer = setTimeout(poll, 750);
      } catch(e) {
        if (stopped) return;
        setDisconnected(true); setError(describeError(e));
        if (!(e instanceof ApiError && e.status === 404)) timer = setTimeout(poll, 2000);
      }
    }
    void poll(); return () => { stopped = true; clearTimeout(timer); };
  }, [active, revision]);
  function select(id: string) {
    selectedRef.current = id; setSelected(id); setError("");
    if (id.startsWith("draft-")) sessionStorage.removeItem(ACTIVE);
    else sessionStorage.setItem(ACTIVE, id);
  }
  function newReview() {
    // One unfinished review per tab, including an uncertain submission awaiting retry.
    const existing = drafts[0];
    const next = existing || makeDraft();
    if (!existing) setDrafts([next]);
    select(next.id);
  }
  function editReport(text: string) {
    if (draft) {
      if (draft.submitting || draft.key) return;
      setDrafts(old => old.map(d => d.id === draft.id ? {...d, text, error: ""} : d));
      return;
    }
    // A submitted report stays editable; reviewing again replaces its latest saved state.
    if (visibleReview && !replacement?.key && !["queued", "running"].includes(visibleReview.execution_status)) setEditedText(text === submittedText ? null : text);
  }

  async function submit(target?: Draft) {
    const item = target ?? draft;
    if (!item || item.submitting || submittingIds.current.has(item.id) || !item.text.trim() || !config?.ready) return;
    submittingIds.current.add(item.id);
    const id = item.id, key = item.key || crypto.randomUUID();
    const wasSelected = () => selectedRef.current === id || (!selectedRef.current && drafts[0]?.id === id);
    setDrafts(old => old.map(d => d.id === id ? {...d, key, submitting: true, error: ""} : d));
    try {
      const data = await api.create({report_text: item.text}, key);
      setDrafts(old => old.filter(d => d.id !== id));
      if (wasSelected()) { select(data.id); setReview(data); }
      setRevision(n => n + 1);
    } catch(e) {
      // Ambiguous failure retains the exact input and idempotency key for retry.
      const definitive = e instanceof ApiError && e.status >= 400 && e.status < 500;
      setDrafts(old => old.map(d => d.id === id ? {...d, submitting: false, key: definitive ? undefined : key, error: describeError(e)} : d));
    } finally { submittingIds.current.delete(id); }
  }
  const canReviewAgain = Boolean(visibleReview && (edited || ['failed','needs_input'].includes(visibleReview.execution_status) || replacement));
  async function reviewAgain() {
    if (!visibleReview || !canReviewAgain || !config?.ready || !report.trim() || submittingIds.current.has(selected)) return;
    const id = selected;
    const item = replacement?.key ? replacement : {text: report, key: crypto.randomUUID(), version: visibleReview.input_version, busy:false};
    submittingIds.current.add(id);
    setReplacements(old => ({...old, [id]: {...item, busy:true, error:''}}));
    try {
      const data = await api.replace(id, item.text, item.version, item.key);
      setEdits(old => {const next = {...old}; delete next[id]; return next;});
      setReplacements(old => {const next = {...old}; delete next[id]; return next;});
      if (selectedRef.current === id) setReview(data);
      setRevision(n => n + 1);
    } catch(e) {
      const definitive = e instanceof ApiError && e.status >= 400 && e.status < 500;
      setReplacements(old => ({...old, [id]: {...item, key:definitive ? '' : item.key, busy:false, error:describeError(e)}}));
    } finally {submittingIds.current.delete(id);}
  }
  const currentRows = visibleReview ? [{
    ...rows.find(row => row.id === visibleReview.id),
    id:visibleReview.id, created_at:visibleReview.created_at,
    execution_status:visibleReview.execution_status,
    preview:visibleReview.input.report_text.replace(/\s+/g,' ').slice(0,140),
    outcome:visibleReview.result?.outcome ?? null,
    general_count:visibleReview.result?.general_comments.length ?? 0,
    critical_count:visibleReview.result?.critical_comments.length ?? 0,
    feedback_count:rows.find(row => row.id === visibleReview.id)?.feedback_count ?? null,
    mode:String(visibleReview.provenance.mode),
  }, ...rows.filter(row => row.id !== visibleReview.id)].sort((a,b) => b.created_at.localeCompare(a.created_at)) : rows;
  return {config, configurationError, retryConfiguration,
    report, review: visibleReview, draft, drafts, rows:currentRows, listError,
    selected: draft?.id || selected, openReview: select, newReview, editReport, submit,
    edited, reviewAgain, canReviewAgain,
    busy: Boolean(draft?.submitting || replacement?.busy || (visibleReview && ["queued", "running"].includes(visibleReview.execution_status))), locked: Boolean(draft?.key || replacement?.key), stale: edited,
    disconnected, error: draft?.error || replacement?.error || error, inputError: "", restore: () => setEditedText(null)};
}
