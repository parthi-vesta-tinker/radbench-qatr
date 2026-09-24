import { useEffect, useState } from 'react';
import { api, describeError } from './api';
import type { ClassificationConfig, ClassificationResource, Review } from './types';

export type ClassificationData = {
  runs: ClassificationResource[];
  config: ClassificationConfig | null;
  loading: boolean;
  error: string;
  refresh: () => void;
};

// One subscription shared by the journey, summary and analysis tool.
export function useClassification(review: Review | null, enabled: boolean, stale: boolean): ClassificationData {
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState<{source: string; runs: ClassificationResource[]; loading: boolean; error: string}>({source: '', runs: [], loading: false, error: ''});
  const [config, setConfig] = useState<ClassificationConfig | null>(null);
  const id = review?.id;
  const version = review?.input_version;
  const source = `${id}:${version}`;
  const eligible = enabled && !stale && review?.execution_status === 'completed' && Boolean(review.result?.critical_comments.length);
  const expected = review?.result?.critical_comments.length ?? 0;
  const automatic = Boolean(review?.provenance.jev_enabled_at_acceptance);
  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    api.classificationConfig().then(value => { if (!cancelled) setConfig(value); }).catch(() => { if (!cancelled) setConfig(null); });
    return () => { cancelled = true; };
  }, [enabled, revision]);
  useEffect(() => {
    if (!eligible || !id) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    setState({source, runs: [], loading: true, error: ''});
    async function poll() {
      try {
        const values = await api.classificationsForReview(id!);
        if (cancelled) return;
        const current = values.filter(run => run.review_id === id && run.input_version === version && run.source_status === 'current');
        const latest = new Map(current.map(run => [run.observation_id, run]));
        const runs = [...latest.values()];
        const pending = runs.some(run => ['queued', 'running'].includes(run.execution_status)) || (automatic && runs.length < expected);
        setState({source, runs, loading: pending, error: ''});
        if (pending) timer = setTimeout(poll, 1500);
      } catch (error) {
        if (!cancelled) setState({source, runs: [], loading: false, error: describeError(error)});
      }
    }
    void poll();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [eligible, id, version, source, revision, automatic, expected]);
  const current = eligible && state.source === source;
  return {runs: current ? state.runs : [], config, loading: Boolean(eligible && (!current || state.loading)), error: current ? state.error : '', refresh: () => setRevision(value => value + 1)};
}
