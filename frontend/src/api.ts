import type { Review, ReviewInput, Config, FeedbackPayload, FeedbackRecord, ReviewSummary, Page, FeedbackInboxItem, Analytics, OutcomeInput, OutcomeRecord } from "./types";
import type { KnowledgeCatalog, KnowledgeDetail, KnowledgeDraft, KnowledgeDraftInput } from './types';
import type { PlaygroundCatalog, PlaygroundRun, PlaygroundRunInput } from './types';
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public requestId?: string,
    public retryable?: boolean,
  ) {
    super(message);
  }
}
async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      signal: AbortSignal.timeout(15000),
      headers: { "QA-Version": "2026-09-18", ...init?.headers },
    });
  } catch (error) {
    throw new ApiError(0, "QA_CONNECTION_FAILED", window.location.protocol === "file:"
      ? "Open the app at http://127.0.0.1:8000 after starting the backend; do not open the HTML file directly."
      : `Cannot reach ${window.location.origin}${url}. Check that the backend is running on this address, then refresh status.`, undefined, true);
  }
  let data;
  try { data = await response.json(); }
  catch { throw new ApiError(response.status, "INVALID_API_RESPONSE", `The QA endpoint returned a non-JSON response (HTTP ${response.status}). Open the URL printed by the local launcher; check the frontend proxy if using Vite.`); }
  if (!response.ok)
    throw new ApiError(
      response.status,
      data.error?.code ?? data.code ?? "REQUEST_FAILED",
      data.error?.message ?? data.message ?? "Request failed.",
      response.headers.get("Request-Id") ?? undefined,
      data.error?.retryable ?? data.retryable,
    );
  return data as T;
}
export function describeError(error: unknown): string {
  if (error instanceof ApiError) return `${error.message} [${error.code}${error.status ? ` · HTTP ${error.status}` : ""}${error.requestId ? ` · ${error.requestId}` : ""}]`;
  return error instanceof Error ? error.message : "The QA service request failed.";
}
export const api = {
  playground: () => request<PlaygroundCatalog>('/api/v1/playground'),
  startPlaygroundRun: (payload: PlaygroundRunInput, key: string) =>
    request<PlaygroundRun>('/api/v1/playground/runs', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Idempotency-Key': key }, body: JSON.stringify(payload) }),
  playgroundRun: (id: string) => request<PlaygroundRun>('/api/v1/playground/runs/' + encodeURIComponent(id)),
  knowledgeCatalog: () => request<KnowledgeCatalog>('/api/v1/knowledge'),
  knowledgeDetail: (id: string) => request<KnowledgeDetail>('/api/v1/knowledge/' + encodeURIComponent(id)),
  saveKnowledgeDraft: (id: string, payload: KnowledgeDraftInput, key: string) => request<KnowledgeDraft>('/api/v1/knowledge/' + encodeURIComponent(id) + '/drafts', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Idempotency-Key': key }, body: JSON.stringify(payload) }),
  exportKnowledgeDraft: (id: string, revision: number) => request<unknown>(`/api/v1/knowledge/${encodeURIComponent(id)}/drafts/${revision}/export`),
  outcomes: (id: string, cursor?: string) => request<Page<OutcomeRecord>>(`/api/v1/reviews/${encodeURIComponent(id)}/outcomes?limit=20${cursor ? '&starting_after=' + encodeURIComponent(cursor) : ''}`),
  saveOutcome: (id: string, payload: OutcomeInput, key: string) => request<OutcomeRecord>(`/api/v1/reviews/${encodeURIComponent(id)}/outcomes`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Idempotency-Key': key }, body: JSON.stringify(payload) }),
  feedbackInbox: (query: string) => request<Page<FeedbackInboxItem>>("/api/v1/feedback?" + query),
  analytics: (query: string) => request<Analytics>("/api/v1/analytics?" + query),
  history: (query: string) => request<Page<ReviewSummary>>("/api/v1/reviews?" + query),
  feedbackHistory: (id: string, cursor?: string) => request<Page<FeedbackRecord>>(`/api/v1/reviews/${encodeURIComponent(id)}/feedback?limit=20${cursor ? "&starting_after=" + encodeURIComponent(cursor) : ""}`),
  status: () => request<{status: string; checked_at: string; components: Record<string, {status:string;message:string;code?:string}>;readiness_scope:string}>("/api/v1/status"),
  checkOpenAI: () => request<{status:string;message:string;code?:string}>("/api/v1/diagnostics/openai", {method:"POST"}),
  config: () => request<Config>("/api/v1/config"),
  get: (id: string) =>
    request<Review>("/api/v1/reviews/" + encodeURIComponent(id)),
  create: (input: ReviewInput, key: string) =>
    request<Review>("/api/v1/reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": key },
      body: JSON.stringify(input),
    }),
  feedback: (id: string, payload: FeedbackPayload, key: string) =>
    request<FeedbackRecord>(
      "/api/v1/reviews/" + encodeURIComponent(id) + "/feedback",
      {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": key },
        body: JSON.stringify(payload),
      },
    ),
};
