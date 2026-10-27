export type ProjectStatus =
  | "active"
  | "idle"
  | "running"
  | "error"
  | "ready"
  | "discovering"
  | "discovered"
  | "failed"
  | string;

export interface Project {
  id: string;
  name: string;
  url: string;
  status: ProjectStatus;
  description?: string;
  testCount: number;
  lastRunAt?: string;
  createdAt: string;
  updatedAt: string;
  pageCount?: number;
  elementCount?: number;
  siteMap?: SiteMapNode[];
  page_elements?: any;
  site_map?: any;
}

export interface SiteMapNode {
  url: string;
  title: string;
  depth: number;
  children?: SiteMapNode[];
  elementCount?: number;
  status?: "discovered" | "analyzed" | "pending";
}

export interface TestCase {
  id: string;
  projectId: string;
  name: string;
  description?: string;
  category: TestCategory;
  priority: "low" | "medium" | "high" | "critical";
  steps: TestStep[];
  expectedResult?: string;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
}

export type TestCategory =
  | "functional"
  | "ui"
  | "navigation"
  | "form"
  | "authentication"
  | "search"
  | "accessibility"
  | "performance";

export interface TestStep {
  order: number;
  action: string;
  selector?: string;
  value?: string;
  assertion?: string;
}

export interface TestRun {
  id: string;
  projectId: string;
  projectName?: string;
  status: RunStatus;
  totalTests: number;
  passedTests: number;
  failedTests: number;
  skippedTests: number;
  duration?: number;
  startedAt?: string;
  completedAt?: string;
  createdAt: string;
  triggeredBy?: string;
  environment?: string;
  browserName?: string;
  currentStep?: ExecutionStep;
  progress?: number;
  results?: TestResult[];
}

export type RunStatus =
  | "pending"
  | "running"
  | "passed"
  | "failed"
  | "cancelled"
  | "completed"
  | "error";

export type ExecutionStep =
  | "discovery"
  | "analysis"
  | "generation"
  | "execution"
  | "reporting"
  | "completed";

export interface TestResult {
  id: string;
  runId: string;
  testCaseId?: string;
  testName: string;
  status: TestStatus;
  category?: TestCategory;
  duration?: number;
  errorMessage?: string;
  stackTrace?: string;
  aiAnalysis?: string;
  screenshotUrl?: string;
  videoUrl?: string;
  logs?: string[];
  steps?: StepResult[];
  startedAt?: string;
  completedAt?: string;
}

export type TestStatus = "passed" | "failed" | "skipped" | "running";

export interface StepResult {
  order: number;
  action: string;
  status: "passed" | "failed" | "skipped";
  duration?: number;
  errorMessage?: string;
  screenshotUrl?: string;
}

export interface Defect {
  id: string;
  runId: string;
  testResultId: string;
  title: string;
  description: string;
  severity: DefectSeverity;
  category?: TestCategory;
  status: "open" | "in-progress" | "resolved" | "wont-fix";
  aiAnalysis?: string;
  screenshotUrl?: string;
  createdAt: string;
  updatedAt: string;
}

export type DefectSeverity = "critical" | "high" | "medium" | "low";

export interface Report {
  id: string;
  runId: string;
  projectId: string;
  projectName: string;
  generatedAt: string;
  summary: ReportSummary;
  downloadUrls: {
    excel?: string;
    pdf?: string;
    allure?: string;
  };
  charts?: ReportChart[];
}

export interface ReportSummary {
  totalTests: number;
  passedTests: number;
  failedTests: number;
  skippedTests: number;
  passRate: number;
  duration: number;
  environment?: string;
  browser?: string;
}

export interface ReportChart {
  type: "pie" | "bar" | "line";
  title: string;
  data: Record<string, number | string>[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  metadata?: ChatMessageMetadata;
  isTyping?: boolean;
}

export interface ChatMessageMetadata {
  projectId?: string;
  runId?: string;
  discoveredPages?: number;
  testCasesCount?: number;
  passRate?: number;
  action?: string;
}

export interface WebSocketEvent {
  type: WebSocketEventType;
  payload: Record<string, unknown>;
  timestamp: string;
  runId?: string;
  projectId?: string;
}

export type WebSocketEventType =
  | "run:started"
  | "run:progress"
  | "run:step-changed"
  | "run:test-result"
  | "run:completed"
  | "run:failed"
  | "run:cancelled"
  | "discovery:progress"
  | "agent:log"
  | "heartbeat"
  | "pipeline_started"
  | "stage_started"
  | "stage_completed"
  | "test_case_progress"
  | "pipeline_completed";

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
  timestamp?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface DashboardStats {
  totalProjects: number;
  totalRuns: number;
  passRate: number;
  activeTests: number;
  recentTrend: TrendPoint[];
  runsByStatus: {
    passed: number;
    failed: number;
    running: number;
    pending: number;
  };
}

export interface TrendPoint {
  date: string;
  passed: number;
  failed: number;
  total: number;
}

export interface FilterState {
  status?: string;
  category?: string;
  priority?: string;
  search?: string;
  page?: number;
  pageSize?: number;
}
