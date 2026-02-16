/**
 * Result from classifying a user prompt.
 */
export interface ClassificationResult {
  category_id: string;
  category_name: string;
  reasoning: string;
  requires_chunking: boolean;
  confidence: number;
}

/**
 * Category metadata for a classification tier.
 */
export interface ClassificationCategory {
  id: string;
  name: string;
  description: string;
  provider: string;
  endpoint: string;
  model_id: string;
  request_defaults?: Record<string, any>;
}

/**
 * Metadata about a single chunk when a prompt is split.
 */
export interface ChunkMetadata {
  chunk_index: number;
  total_chunks: number;
  start_char: number;
  end_char: number;
  token_estimate?: number;
}

/**
 * Complete processing result from the backend.
 */
export interface ProcessingResult {
  classification: ClassificationResult;
  target_model: string;
  selected_category: ClassificationCategory;
  llm_response: string | null;
  chunks?: string[];
  chunk_metadata?: ChunkMetadata[];
  requires_aggregation?: boolean;
}

/**
 * Response from the /route endpoint.
 */
export interface RouteResponse {
  target_model: string;
}

/**
 * Response from the /tiers endpoint.
 */
export interface TiersResponse {
  tiers: Record<string, string>;
}

/**
 * Response from the /categories endpoint.
 */
export interface CategoriesResponse {
  user_id: string;
  default_category_id: string;
  categories: ClassificationCategory[];
}

/**
 * Configuration options for the Servo client.
 */
export interface ServoConfig {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  defaultUserId?: string;
}

/**
 * Options for the send method.
 */
export interface SendOptions {
  useQuickClassify?: boolean;
  conversation?: any; // Will be typed as Conversation in context.ts
}
