// UI-friendly names only. Wire shapes live in generated-api.ts, never here.
export type {
  ReviewInput, ResultObservation as Observation, ReviewResult as Result,
  StepState as Step, ReviewResource as Review, ConfigResource as Config,
  FeedbackInput as FeedbackPayload, FeedbackResource as FeedbackRecord,
  ReviewSummary, ReviewComments, FeedbackInboxItem, AnalyticsResource as Analytics,
  Document as KnowledgeDocument, Draft as KnowledgeDraft, Catalog as KnowledgeCatalog,
  Detail as KnowledgeDetail, DraftInput as KnowledgeDraftInput,
  PlaygroundCatalog, PlaygroundRun, PlaygroundRunInput, PlaygroundSample,
  ClassificationConfig, ClassificationInput, ClassificationResource, ClassificationLabels,
  ClassificationFeedbackInput, ClassificationFeedbackResource, ClassificationFeedbackList,
} from './generated-api';
export type Page<T> = { items: T[]; has_more: boolean; next_cursor: string | null };
