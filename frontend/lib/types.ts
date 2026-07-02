// Mirrors the backend's Pydantic schemas (app/schemas/*.py) so the
// frontend has a single source of truth for API shapes.

export type ApiResponse<T> = {
  success: boolean;
  data: T | null;
  error: string | null;
};

export type MessageCategory = "spam" | "genuine" | "recruiter" | "collaboration" | "general" | "needs_review";

export type Message = {
  id: string;
  sender_name: string;
  content: string;
  category: MessageCategory | null;
  priority_score: number | null;
  summary: string | null;
  received_at: string | null;
  imported_at: string;
};

export type ImportFileResult = {
  filename: string;
  status: "success" | "partial" | "failed";
  rows_imported: number;
  errors: string[];
};

export type ImportSummary = {
  files: ImportFileResult[];
  total_messages_imported: number;
  total_posts_imported: number;
  total_connections_imported: number;
};

export type PostingFrequencyPoint = { period: string; post_count: number };
export type TopPost = {
  content: string;
  posted_at: string | null;
  views: number | null;
  likes: number | null;
  comments: number | null;
};
export type CategoryBreakdownPoint = { category: string; count: number };

export type AnalyticsResponse = {
  posting_frequency: PostingFrequencyPoint[];
  top_posts: TopPost[];
  category_breakdown: CategoryBreakdownPoint[];
  total_posts: number;
  total_messages: number;
  avg_views: number | null;
};

export type WeeklyReport = {
  id: string;
  period_start: string;
  period_end: string;
  content: string;
  generated_at: string;
};

export type UserProfile = {
  id: string;
  email: string;
  name: string | null;
  bio_context: string | null;
};
