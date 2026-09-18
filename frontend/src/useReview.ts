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
  const [drafts, setDrafts] = useState<Draft[]>(() => [makeDraft()]);
  const [selected, setSelected] = useState(() => sessionStorage.getItem(ACTIVE) || "");
  const selectedRef = useRef(selected); selectedRef.current = selected;
  const [review, setReview] = useState<Review | null>(null);
  const [disconnected, setDisconnected] = useState(false);
  const [error, setError] = useState("");
  const [rows, setRows] = useState<ReviewSummary[]>([]);
  const [listError, setListError] = useState("");
  const [revision, setRevision] = useState(0);
  const [deleted, setDeleted] = useState<Draft | null>(null);
  const submittingIds = useRef(new Set<string>());
  const draft = selected ? drafts.find(d => d.id === selected) : drafts[0];
  const active = draft ? null : selected;
  const visibleReview = !draft && review?.id === active ? review : null;
  const report = draft?.text ?? visibleReview?.input.report_text ?? "";
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (drafts.some(d => d.text.trim())) { event.preventDefault(); event.returnValue = ""; } };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [drafts]);
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
    setReview(null); setDisconnected(false); setError("");
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
  }, [active]);
  function select(id: string) {
    selectedRef.current = id; setSelected(id); setError("");
    if (id.startsWith("draft-")) sessionStorage.removeItem(ACTIVE);
    else sessionStorage.setItem(ACTIVE, id);
  }
  function newReview(text = "") {
    // Reuse an empty draft rather than accumulating placeholders.
    const existing = !text && drafts.find(d => !d.text && !d.key && !d.submitting);
    const next = existing || makeDraft(text);
    if (!existing) setDrafts(old => [...old, next]);
    select(next.id);
  }
  function editReport(text: string) {
    if (!draft || draft.submitting || draft.key) return;
    setDrafts(old => old.map(d => d.id === draft.id ? {...d, text, error: ""} : d));
  }

  function deleteDraft(id: string) {
    const item = drafts.find(d => d.id === id);
    if (!item || item.key || item.submitting) return;
    setDeleted(item);
    const remaining = drafts.filter(d => d.id !== id);
    if (!remaining.length && !rows.length) remaining.push(makeDraft());
    setDrafts(remaining);
    if (draft?.id === id) select(remaining[0]?.id || rows[0].id);
  }
  function undoDelete() {
    if (!deleted) return;
    setDrafts(old => [...old, deleted]); select(deleted.id); setDeleted(null);
  }
  async function submit() {
    if (!draft || draft.submitting || submittingIds.current.has(draft.id) || !draft.text.trim() || !config?.ready) return;
    submittingIds.current.add(draft.id);
    const id = draft.id, key = draft.key || crypto.randomUUID();
    const wasSelected = () => selectedRef.current === id || (!selectedRef.current && drafts[0]?.id === id);
    setDrafts(old => old.map(d => d.id === id ? {...d, key, submitting: true, error: ""} : d));
    try {
      const data = await api.create({report_text: draft.text}, key);
      setDrafts(old => old.filter(d => d.id !== id));
      if (wasSelected()) { select(data.id); setReview(data); }
      setRevision(n => n + 1);
    } catch(e) {
      // Ambiguous failure retains the exact input and idempotency key for retry.
      const definitive = e instanceof ApiError && e.status >= 400 && e.status < 500;
      setDrafts(old => old.map(d => d.id === id ? {...d, submitting: false, key: definitive ? undefined : key, error: describeError(e)} : d));
    } finally { submittingIds.current.delete(id); }
  }
  return {config, configurationError, retryConfiguration,
    report, review: visibleReview, draft, drafts, rows, listError,
    selected: draft?.id || selected, openReview: select, newReview, editReport, submit,
    deleteDraft, deleted, undoDelete, dismissDelete: () => setDeleted(null),
    busy: Boolean(draft?.submitting), locked: !draft || Boolean(draft.key), stale: false,
    disconnected, error: draft?.error || error, inputError: "", restore: () => {}};
}
