// ---------------------------------------------------------------------
// Shared envelope types — mirrors app/schemas/common.py
// ---------------------------------------------------------------------

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: PaginationMeta;
}

export interface ErrorDetail {
  message: string;
  code: string;
}

export interface ApiErrorBody {
  detail: ErrorDetail;
}

// ---------------------------------------------------------------------
// Auth — mirrors app/schemas/auth.py
// ---------------------------------------------------------------------

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in_minutes: number;
}

export type RefreshResponse = LoginResponse;

export interface CurrentUser {
  username: string;
  user_id: number;
  is_superadmin: boolean;
}

// ---------------------------------------------------------------------
// Admin — mirrors app/schemas/admin.py
// ---------------------------------------------------------------------

export interface UserSummary {
  id: number;
  username: string;
  is_superadmin: boolean;
  is_active: boolean;
  created_at: string;
}

export interface UserListResponse {
  users: UserSummary[];
}

// ---------------------------------------------------------------------
// Filters — mirrors app/schemas/filters.py
// ---------------------------------------------------------------------

export interface DateRange {
  earliest_event: string;
  latest_event: string;
}

export interface FilterOptionsResponse {
  funnel_steps: string[];
  event_names: string[];
  traffic_sources: string[];
  date_range: DateRange;
}

// ---------------------------------------------------------------------
// Traffic & Overview — mirrors app/schemas/traffic.py
// ---------------------------------------------------------------------

export interface TopPage {
  path: string;
  title: string | null;
  views: number;
}

export interface DeviceBreakdown {
  mobile: number;
  desktop: number;
  unknown: number;
}

export interface PlatformBreakdown {
  platform: string;
  views: number;
}

export interface TrafficOverviewResponse {
  total_page_views: number;
  unique_visitors: number;
  top_pages: TopPage[];
  device_breakdown: DeviceBreakdown;
  platform_breakdown: PlatformBreakdown[];
}

// ---------------------------------------------------------------------
// Interactions — mirrors app/schemas/interactions.py
// ---------------------------------------------------------------------

export const INTERACTION_TYPES = [
  "cta_click",
  "nav_click",
  "menu_click",
  "footer_click",
  "service_card_click",
  "blog_card_click",
  "sitemap_card_click",
  "work_card_click",
  "blog_click",
  "case_study_click",
  "case_study_cta_click",
  "operating_ring_click",
  "social_click",
  "tag_filter_click",
  "pagination_click",
  "carousel_click",
] as const;

export type InteractionType = (typeof INTERACTION_TYPES)[number];

export interface InteractionTypeCount {
  interaction_type: string;
  count: number;
}

export interface InteractionLeaderboardResponse {
  total_interactions: number;
  by_type: InteractionTypeCount[];
}

export interface InteractionEvent {
  interaction_type: string;
  label: string | null;
  page_path: string | null;
  timestamp: string;
}

// ---------------------------------------------------------------------
// Navigation — mirrors app/schemas/navigation.py
// ---------------------------------------------------------------------

export interface NavigationPath {
  steps: string[];
  visitor_count: number;
  percentage: number;
}

export interface ExitRateByPage {
  path: string;
  exits: number;
  exit_rate_pct: number;
}

export interface NavigationOverviewResponse {
  top_paths: NavigationPath[];
  average_pages_per_session: number;
  exit_rates: ExitRateByPage[];
}

// ---------------------------------------------------------------------
// User Journey — mirrors app/schemas/journey.py
// ---------------------------------------------------------------------

export interface ResolvedIdentity {
  email: string | null;
  name: string | null;
}

export type JourneyEventCategory = "page_view" | "click" | "form_activity";

export interface JourneyEvent {
  event_category: JourneyEventCategory;
  event_type: string;
  label: string | null;
  page_path: string | null;
  timestamp: string;
}

export interface UserJourneyResponse {
  anonymous_id: string;
  resolved_identity: ResolvedIdentity | null;
  total_events: number;
  session_count: number;
  first_seen: string;
  last_seen: string;
  has_converted: boolean;
  events: JourneyEvent[];
}

export interface VisitorSummary {
  anonymous_id: string;
  email: string | null;
  name: string | null;
  first_seen: string;
  last_seen: string;
}

// ---------------------------------------------------------------------
// Engagement — mirrors app/schemas/engagement.py
// ---------------------------------------------------------------------

export interface PageEngagement {
  path: string;
  views: number;
  avg_scroll_depth_pct: number;
  median_scroll_depth_pct: number;
  engaged_visit_count: number;
}

export interface EngagementMilestoneBucket {
  milestone_seconds: number;
  visit_count: number;
}

export interface ContentEngagementItem {
  content_type: "blog" | "case_study";
  label: string;
  url: string | null;
  clicks: number;
}

export interface ServicesContentEngagementResponse {
  page_engagement: PageEngagement[];
  milestone_breakdown: EngagementMilestoneBucket[];
  content_engagement: ContentEngagementItem[];
}

// ---------------------------------------------------------------------
// Conversion Funnel — mirrors app/schemas/conversion.py
// ---------------------------------------------------------------------

export interface ConversionFunnelStep {
  step_name: string;
  users: number;
  dropoff_pct: number;
  conversion_from_top: number;
}

export interface ConversionFunnelResponse {
  steps: ConversionFunnelStep[];
}

// ---------------------------------------------------------------------
// Form Field Drop-off — mirrors app/schemas/form_dropoff.py
// ---------------------------------------------------------------------

export interface FieldDropoff {
  field_name: string;
  focus_count: number;
  complete_count: number;
  error_count: number;
  dropoff_pct: number;
  avg_time_seconds: number | null;
}

export interface FormFieldDropoffResponse {
  fields: FieldDropoff[];
  most_common_dropoff_field: string | null;
}

// ---------------------------------------------------------------------
// Drop-off Explorer — mirrors app/schemas/dropoff_explorer.py
// ---------------------------------------------------------------------

export interface DropoffVisitor {
  anonymous_id: string;
  last_known_action: string;
  last_seen: string;
}

export interface DropoffSummary {
  from_step: string;
  to_step: string;
  total_dropoff: number;
}

// FUNNEL_STEPS — mirrors app/core/constants.py, fixed order (used for the
// step-picker and for validating from_step precedes to_step client-side,
// matching the same rule dropoff_explorer_service.py enforces server-side).
export const FUNNEL_STEPS = [
  "contact_us_page_view",
  "form_start",
  "form_field_complete",
  "form_submit",
  "form_submit_success",
] as const;

export type FunnelStep = (typeof FUNNEL_STEPS)[number];

export const FUNNEL_STEP_LABELS: Record<FunnelStep, string> = {
  contact_us_page_view: "Contact Us — Page View",
  form_start: "Form Start",
  form_field_complete: "Field Completed",
  form_submit: "Form Submit",
  form_submit_success: "Form Submit — Success",
};
