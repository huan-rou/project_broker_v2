export interface DemoCase {
  id: number
  name: string
  status: string
  notes: string | null
  created_at: string
  updated_at: string
}

export interface DemoDocument {
  id: number
  case_id: number
  original_filename: string
  storage_path: string
  status: string
  document_category: string | null
  ocr_text: string | null
  evidence_json: Record<string, unknown> | null
  fact_find_preview: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface JobTrace {
  id: number
  document_id: number
  stage: string
  status: string
  retryable: boolean
  error_code: string | null
  message: string
  log_summary: string | null
  created_at: string
}

export interface FactFindSnapshot {
  id: number
  case_id: number
  version: number
  is_current: boolean
  form_data: Record<string, unknown>
  created_at: string
}

export interface CalculatorResult {
  id: number
  case_id: number
  lender: string
  status: string
  max_borrowing_capacity: number
  monthly_surplus: number
  assessment_rate: number
  notes: Record<string, unknown>
  created_at: string
}
