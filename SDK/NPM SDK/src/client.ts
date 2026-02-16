import { HTTPClient } from './http';
import { Conversation } from './context';
import {
  ClassificationResult,
  ProcessingResult,
  RouteResponse,
  TiersResponse,
  CategoriesResponse,
  ServoConfig,
  SendOptions,
} from './types';

/**
 * Minimal JavaScript client for the Servo backend.
 *
 * 3-step flow:
 *   1) init client
 *   2) send prompt (optionally with context)
 *   3) receive typed response
 */
export class Servo {
  private http: HTTPClient;
  private defaultConversation?: Conversation;
  private defaultUserId: string;

  constructor(config: ServoConfig = {}) {
    const {
      apiKey,
      baseUrl = 'http://localhost:8000',
      timeout = 30000,
      defaultUserId = 'default_user',
    } = config;

    this.http = new HTTPClient(baseUrl, apiKey, timeout);
    this.defaultUserId = defaultUserId;
  }

  /**
   * Initialize or retrieve a conversation for managing chat history.
   */
  withConversation(conversation?: Conversation): Conversation {
    if (conversation) {
      this.defaultConversation = conversation;
      return conversation;
    }

    if (!this.defaultConversation) {
      this.defaultConversation = new Conversation();
    }

    return this.defaultConversation;
  }

  /**
   * Check backend health.
   */
  async health(): Promise<Record<string, any>> {
    return await this.http.requestJson('GET', '/health');
  }

  /**
   * Get available model tiers for a specific user.
   */
  async tiers(userId?: string): Promise<TiersResponse> {
    const user = userId || this.defaultUserId;
    return await this.http.requestJson('GET', `/tiers?user_id=${encodeURIComponent(user)}`);
  }

  /**
   * Get available categories for a specific user.
   */
  async categories(userId?: string): Promise<CategoriesResponse> {
    const user = userId || this.defaultUserId;
    return await this.http.requestJson('GET', `/categories?user_id=${encodeURIComponent(user)}`);
  }

  /**
   * Classify a prompt to determine category and routing.
   */
  async classify(
    prompt: string,
    userId?: string,
    useQuick: boolean = false
  ): Promise<ClassificationResult> {
    const user = userId || this.defaultUserId;
    return await this.http.requestJson('POST', '/classify', {
      user_id: user,
      prompt,
      use_quick: useQuick,
    });
  }

  /**
   * Route a classification result to determine the target model.
   */
  async route(
    classification: ClassificationResult,
    userId?: string
  ): Promise<RouteResponse> {
    const user = userId || this.defaultUserId;
    return await this.http.requestJson('POST', '/route', {
      user_id: user,
      classification,
    });
  }

  /**
   * Send a request to the backend for processing.
   *
   * This is the main method that combines classification, routing,
   * and model invocation in a single call.
   */
  async send(
    requestMessage: string,
    userId?: string,
    options: SendOptions = {}
  ): Promise<ProcessingResult> {
    const { useQuickClassify = false, conversation } = options;
    const user = userId || this.defaultUserId;

    const conv = conversation || this.defaultConversation;
    const prompt = conv ? conv.buildPrompt(requestMessage) : requestMessage;

    return await this.http.requestJson('POST', '/process', {
      user_id: user,
      prompt,
      use_quick_classify: useQuickClassify,
    });
  }
}
