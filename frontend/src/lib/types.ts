export interface Profile {
  headline: string | null;
  bio: string | null;
  education_level: string | null;
  experience_level: string | null;
  career_goal: string | null;
  target_role: string | null;
  weekly_minutes_goal: number | null;
  timezone: string;
  onboarding_step: number;
  onboarding_completed_at: string | null;
}

export interface Preferences {
  learning_style: string;
  session_minutes: number;
  prefers_projects: boolean;
  prefers_theory_first: boolean;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  xp_total: number;
  is_verified: boolean;
  onboarding_completed: boolean;
  created_at: string;
  profile: Profile | null;
  preferences: Preferences | null;
}

export interface Subject {
  id: string;
  slug: string;
  name: string;
  description: string;
  category: string;
  accent: string;
  icon: string;
}

export interface Skill {
  id: string;
  slug: string;
  name: string;
  description: string;
  subject_id: string;
}

export interface UserSkill {
  skill_id: string;
  slug: string;
  name: string;
  proficiency: number;
  confidence: number;
  source: string;
  last_assessed_at: string | null;
}

export interface MeResponse {
  user: User;
  interests: Subject[];
  skills: UserSkill[];
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface DashboardResponse {
  user: {
    id: string;
    first_name: string;
    full_name: string;
    initials: string;
    career_goal: string | null;
    experience_level: string | null;
    streak_days: number;
    subjects: Subject[];
  };
  profile: Profile | null;
  preferences: Preferences | null;
  level: {
    level: number;
    xp_total: number;
    xp_into_level: number;
    xp_for_next_level: number;
    progress_percent: number;
  };
  weekly_goal: { target_minutes: number; completed_minutes: number; percent: number };
  stats: {
    total_learning_minutes: number;
    lessons_completed: number;
    skills_acquired: number;
    active_paths: number;
  };
  current_path: {
    id: string;
    title: string;
    subject_name: string;
    subject_accent: string;
    rationale: string;
    estimated_weeks: number;
    target_level: string;
    items_total: number;
    items_completed: number;
    progress_percent: number;
    next_item: {
      id: string;
      title: string;
      status: string;
      is_project: boolean;
      estimated_minutes: number;
      position: number;
    } | null;
    items: {
      id: string;
      title: string;
      status: string;
      is_project: boolean;
      estimated_minutes: number;
      position: number;
    }[];
  } | null;
  activity_series: { day: string; minutes: number; xp: number }[];
  top_skills: { name: string; proficiency: number; subject_name: string }[];
  achievements: {
    code: string;
    name: string;
    description: string;
    icon: string;
    xp_reward: number;
    unlocked_at: string;
  }[];
  upcoming_assessments: {
    id: string;
    title: string;
    kind: string;
    level: string;
    subject_name: string;
    estimated_minutes: number;
  }[];
  recommendations: {
    id: string;
    kind: string;
    title: string;
    description: string;
    reason: string;
    target_url: string | null;
  }[];
}

export interface AssessmentSubjectSummary {
  subject_id: string;
  subject_slug: string;
  subject_name: string;
  subject_description: string;
  accent: string;
  assessment_id: string | null;
  title: string | null;
  estimated_minutes: number | null;
  question_count: number;
  in_progress_attempt_id: string | null;
  last_attempt_id: string | null;
  last_score: number | null;
  last_completed_at: string | null;
}

export interface AssessmentOverview {
  subjects: AssessmentSubjectSummary[];
}

export interface SavedResponse {
  index?: number;
  text?: string;
}

export interface AttemptQuestion {
  id: string;
  kind: string;
  prompt: string;
  options: string[] | null;
  position: number;
  difficulty: number;
  saved_response: SavedResponse | null;
}

export interface AssessmentAttempt {
  id: string;
  assessment_id: string;
  title: string;
  subject_name: string;
  subject_slug: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  questions: AttemptQuestion[];
  answered_count: number;
  total_questions: number;
}

export interface SkillResult {
  skill_id: string;
  slug: string;
  name: string;
  score: number;
  proficiency: number;
  confidence: number;
}

export interface AttemptResult {
  attempt_id: string;
  score_percent: number;
  correct_count: number;
  partial_count: number;
  total_questions: number;
  proficiency_estimate: number;
  weak_skills: string[];
  skill_results: SkillResult[];
  roadmap_id: string | null;
  xp_awarded: number;
  generated_by: string | null;
}

export interface ReviewQuestion {
  id: string;
  prompt: string;
  kind: string;
  options: string[] | null;
  response: SavedResponse | null;
  correct_answer: string | null;
  is_correct: boolean | null;
  score: number | null;
  feedback: string | null;
  explanation: string | null;
  skill_name: string | null;
}

export interface AttemptReview {
  attempt_id: string;
  title: string;
  subject_name: string;
  subject_slug: string;
  score_percent: number | null;
  proficiency_estimate: number | null;
  weak_skills: string[];
  completed_at: string | null;
  roadmap_id: string | null;
  skills: SkillResult[];
  questions: ReviewQuestion[];
}

export interface RoadmapItem {
  id: string;
  title: string;
  objective: string;
  position: number;
  status: string;
  is_project: boolean;
  estimated_minutes: number;
  completed_at: string | null;
}

export interface RoadmapData {
  id: string;
  title: string;
  subject_id: string;
  subject_slug: string;
  subject_name: string;
  accent: string;
  rationale: string;
  target_level: string;
  status: string;
  estimated_weeks: number;
  generated_by: string;
  created_at: string;
  items_total: number;
  items_completed: number;
  progress_percent: number;
  items: RoadmapItem[];
}

export interface OnboardingPayload {
  education_level: string;
  experience_level: string;
  learning_style: string;
  session_minutes: number;
  weekly_minutes_goal: number;
  career_goal: string;
  target_role?: string | null;
  subject_slugs: string[];
  prefers_projects: boolean;
  prefers_theory_first: boolean;
  timezone?: string;
}

export interface TutorStatusResponse {
  available: boolean;
  provider: string;
  model: string | null;
  message: string;
}

export interface TutorConversationSummary {
  id: string;
  title: string;
  subject_id: string | null;
  subject_name: string | null;
  subject_slug: string | null;
  accent: string | null;
  level: string;
  status: string;
  message_count: number;
  last_message_preview: string;
  created_at: string;
  updated_at: string;
}

export interface TutorMessage {
  id: string;
  role: string;
  content: string;
  mode: string;
  hint_level: number;
  provider: string;
  sources: string[];
  created_at: string;
}

export interface TutorConversationDetail extends TutorConversationSummary {
  messages: TutorMessage[];
}

export interface TutorReply {
  conversation: TutorConversationSummary;
  messages: TutorMessage[];
  suggestions: string[];
}

export interface AnalyticsTotals {
  minutes: number;
  xp: number;
  streak_days: number;
  assessments_completed: number;
  roadmap_items_completed: number;
  lessons_completed: number;
}

export interface AnalyticsActivityPoint {
  day: string;
  minutes: number;
  xp: number;
}

export interface AnalyticsStudyKind {
  kind: string;
  minutes: number;
}

export interface AnalyticsSubject {
  subject_id: string;
  subject_name: string;
  accent: string;
  average_proficiency: number;
  skills_tracked: number;
  minutes: number;
}

export interface AnalyticsAssessmentPoint {
  attempt_id: string;
  subject_name: string;
  score_percent: number;
  completed_at: string;
}

export interface AnalyticsWeakSkill {
  skill_id: string;
  name: string;
  subject_name: string;
  proficiency: number;
  confidence: number;
}

export interface AnalyticsResponse {
  range_days: number;
  totals: AnalyticsTotals;
  activity: AnalyticsActivityPoint[];
  study_by_kind: AnalyticsStudyKind[];
  subjects: AnalyticsSubject[];
  assessment_trend: AnalyticsAssessmentPoint[];
  weak_skills: AnalyticsWeakSkill[];
  revision_suggestions: string[];
}

export interface CareerRoleSummary {
  id: string;
  slug: string;
  title: string;
  summary: string;
  level: string;
  version: number;
  skill_count: number;
  met_count: number;
  readiness_score: number;
  readiness_label: string;
}

export interface CareerRoleSkill {
  skill_id: string | null;
  skill_slug: string;
  name: string;
  subject_name: string;
  target: number;
  importance: number;
  proficiency: number;
  confidence: number;
  gap: number;
  status: string;
  evidence_source: string;
}

export interface CareerRecommendation {
  kind: string;
  title: string;
  description: string;
  reason: string;
  target_url: string | null;
}

export interface PortfolioBrief {
  title: string;
  brief: string;
  skills: string[];
  missing_skills: string[];
}

export interface CareerRoleDetail extends CareerRoleSummary {
  skills: CareerRoleSkill[];
  recommendations: CareerRecommendation[];
  portfolio_briefs: PortfolioBrief[];
  strengths: string[];
  priorities: string[];
  generated_by: string;
  disclaimer: string;
}

export interface CareerRoleList {
  items: CareerRoleSummary[];
  disclaimer: string;
}

export interface InterviewQuestion {
  id: string;
  kind: string;
  prompt: string;
  difficulty: number;
  position: number;
  skill_name: string | null;
  answer: string | null;
  score: number | null;
  matched_points: string[];
  feedback: string | null;
  model_answer: string | null;
}

export interface MockInterview {
  id: string;
  role_slug: string;
  role_title: string;
  status: string;
  overall_score: number | null;
  readiness: string | null;
  feedback: string[];
  started_at: string;
  completed_at: string | null;
  answered: number;
  total: number;
  questions: InterviewQuestion[];
  disclaimer: string;
}

export interface MockInterviewSummary {
  id: string;
  role_slug: string;
  role_title: string;
  status: string;
  overall_score: number | null;
  readiness: string | null;
  feedback: string[];
  started_at: string;
  completed_at: string | null;
  answered: number;
  total: number;
}

export interface MockInterviewList {
  items: MockInterviewSummary[];
}

export interface ResumeSkill {
  id: string;
  label: string;
  claimed_level: string;
  skill_id: string | null;
  skill_slug: string | null;
  skill_name: string | null;
  subject_name: string | null;
  measured_proficiency: number | null;
  verified: boolean;
  evidence: string;
}

export interface ResumeSkillList {
  items: ResumeSkill[];
}
