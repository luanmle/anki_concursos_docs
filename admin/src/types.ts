export type UserRole = 'admin' | 'curator' | 'reviewer' | 'student'

export interface User {
  user_id: string
  email: string
  display_name: string
  role: UserRole
  is_active: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: User
}

export interface Paginated<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  pages: number
}

export interface Discipline {
  discipline_id: string
  name: string
  parent_id: string | null
}

export interface Topic {
  topic_id: string
  discipline_id: string
  name: string
  parent_id: string | null
}

export interface DisciplineList {
  items: Discipline[]
  total: number
}

export interface TopicList {
  discipline: Discipline
  items: Topic[]
  total: number
}

export interface CardVersion {
  card_version_id: string
  version_number: number
  front_text: string
  back_text: string
  answer_text: string
  explanation_text: string
  change_reason: string
  created_by: string
  status: string
  content_hash: string
  created_at: string
}

export interface CardSummary {
  card_id: string
  public_id: string
  canonical_key: string
  card_kind: 'basic' | 'cloze'
  note_type: string
  discipline_id: string
  topic_id: string
  status: string
  current_version: CardVersion | null
  created_at: string
  updated_at: string
}

export interface CardDetail extends CardSummary {
  versions: CardVersion[]
}

export interface CardCsvImportRowResult {
  row_number: number
  status: 'created' | 'ready' | 'duplicate' | 'error' | string
  message: string
  card_kind: 'basic' | 'cloze' | null
  public_id: string | null
  card_id: string | null
  card_version_id: string | null
}

export interface CardCsvImportResponse {
  dry_run: boolean
  total_rows: number
  created: number
  duplicates: number
  errors: number
  items: CardCsvImportRowResult[]
}

export interface DeckSummary {
  deck_id: string
  name: string
  discipline_id: string | null
  description: string | null
  status: string
  active_card_count: number
  created_at: string
  updated_at: string
}

export interface DeckCard {
  card_id: string
  public_id: string
  card_version_id: string
  version_number: number
  added_at: string
}

export interface DeckDetail {
  deck_id: string
  name: string
  discipline_id: string | null
  description: string | null
  status: string
  cards: DeckCard[]
  created_at: string
  updated_at: string
}

export interface ReleaseActionCounts {
  added: number
  updated: number
  removed: number
  deprecated: number
}

export interface ReleaseSummary {
  release_id: string
  deck_id: string
  release_number: number
  published_at: string
  description: string | null
  item_count: number
  actions: ReleaseActionCounts
}

export interface ReleaseList extends Paginated<ReleaseSummary> {
  latest_release: number
}

export interface SyncChange {
  release_id: string
  release_number: number
  published_at: string
  action: string
  card_id: string
  public_id: string
  old_card_version_id: string | null
  new_card_version_id: string | null
}

export interface DeckSync {
  deck_id: string
  from_release: number
  to_release: number
  has_changes: boolean
  changes: SyncChange[]
}

export interface SubscribableDeck extends DeckSummary {
  latest_release: number
  subscribed: boolean
}

export type SubscribableDeckList = Paginated<SubscribableDeck>

export interface DeckSubscription {
  subscription_id: string
  deck_id: string
  deck_name: string
  latest_release: number
  active_card_count: number
  subscribed_at: string
  unsubscribed_at: string | null
}

export interface DeckSubscriptionList {
  items: DeckSubscription[]
  total: number
}

export interface AnkiDeckManifest {
  deck_id: string
  name: string
  description: string | null
  latest_release: number
  note_type: string
  fields: string[]
  field_mapping: Record<string, string>
  supported_note_types: Record<
    string,
    {
      note_type: string
      fields: string[]
      field_mapping: Record<string, string>
    }
  >
  tags: string[]
}

export interface AnkiSyncChange {
  release_id: string
  release_number: number
  published_at: string
  action: string
  card_id: string
  public_id: string
  old_card_version_id: string | null
  new_card_version_id: string | null
  card_kind: 'basic' | 'cloze' | null
  note_type: string | null
  fields: Record<string, string> | null
  tags: string[]
}

export interface AnkiDeckSync {
  deck_id: string
  from_release: number
  to_release: number
  has_changes: boolean
  changes: AnkiSyncChange[]
}

export interface ReviewTask {
  review_task_id: string
  status: string
  assigned_to: string | null
  decision: string | null
  admin_comment: string | null
  evidence_reviewed: boolean
  resulting_card_version_id: string | null
  reviewed_at: string | null
  created_at: string
  updated_at: string
}

export interface Report {
  report_id: string
  card_id: string
  public_id: string
  card_version_id: string
  version_number: number
  reporter_reference: string | null
  report_type: string
  message: string
  status: string
  review_task: ReviewTask
  created_at: string
  updated_at: string
}

export interface OperationStatus {
  service: 'online' | 'offline'
  database: 'online' | 'offline' | 'checking'
  checkedAt: Date
}
