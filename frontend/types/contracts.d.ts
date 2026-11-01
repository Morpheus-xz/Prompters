/** Public API contracts consumed by browser modules; no runtime dependency. */
export type EventType = 'wedding' | 'birthday' | 'community';
export type Currency = 'INR' | 'USD' | 'EUR' | 'GBP';
export type VendorStatus = 'to_contact' | 'contacted' | 'booked';
export type IdeaFocus =
  | 'overall'
  | 'theme'
  | 'food'
  | 'entertainment'
  | 'decor'
  | 'activities'
  | 'saving_money';
export type BudgetState = 'on_track' | 'warning' | 'over';
export interface Task {
  id: string;
  title: string;
  category: string;
  due_date: string;
  done: boolean;
}
export interface Vendor {
  id: string;
  name: string;
  category: string;
  essential: boolean;
  status: VendorStatus;
}
export interface Expense {
  id: string;
  category: string;
  amount: number;
  description: string;
  logged_at: string;
}
export interface BudgetLine {
  category: string;
  label: string;
  allocated: number;
  spent: number;
  remaining: number;
  percent_used: number;
  state: BudgetState;
}
export interface BudgetStatus {
  lines: BudgetLine[];
  total_allocated: number;
  total_spent: number;
  total_remaining: number;
  percent_used: number;
  state: BudgetState;
}
export interface Progress {
  tasks_total: number;
  tasks_done: number;
  overdue_count: number;
  essential_vendors_total: number;
  essential_vendors_booked: number;
  readiness_score: number;
  days_until_event: number;
}
export interface PlanSummary {
  id: string;
  title: string;
  event_type: EventType;
  event_date: string;
}
export interface PlanDetail extends PlanSummary {
  guest_count: number;
  total_budget: number;
  currency: Currency;
  city: string | null;
  preferences: string | null;
  created_at: string;
  timeline_compressed: boolean;
  allocations: Record<string, number>;
  tasks: Task[];
  vendors: Vendor[];
  expenses: Expense[];
  per_guest_budget: number;
  budget: BudgetStatus;
  progress: Progress;
}
export interface Idea {
  title: string;
  description: string;
  budget_category: string;
  cost_level: 'low' | 'medium' | 'high';
}
export interface IdeasResponse {
  ideas: Idea[];
  pro_tip: string;
  focus: IdeaFocus;
  from_cache: boolean;
}
export interface SplitInfo {
  category: string;
  label: string;
  percent: number;
}
export interface EventTypeInfo {
  key: EventType;
  label: string;
  description: string;
  budget_split: SplitInfo[];
}
export interface CreatePlanInput {
  title: string;
  event_type: EventType;
  event_date: string;
  guest_count: number;
  total_budget: number;
  currency: Currency;
  city: string | null;
  preferences: string | null;
}
export interface ExpenseInput {
  category: string;
  amount: number;
  description: string;
}
export interface ValidationIssue {
  loc: (string | number)[];
  msg: string;
}
export interface ErrorBody {
  detail?: string | ValidationIssue[];
}
export interface FieldError {
  field: string;
  message: string;
}
export interface AppState {
  types: EventTypeInfo[];
  plans: PlanSummary[];
  plan: PlanDetail | null;
  ideas: IdeasResponse | null;
  busy: boolean;
}
export type DomChild = Node | string | number | null | undefined | false | DomChild[];
export type DomProps = Record<
  string,
  string | number | boolean | EventListener | null | undefined
>;
export type FormControl = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
export type Choice = readonly [string, string];
