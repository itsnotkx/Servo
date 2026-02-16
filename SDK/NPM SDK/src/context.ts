/**
 * Role types for messages in a conversation.
 */
export type Role = 'system' | 'user' | 'assistant';

/**
 * A single message in a conversation.
 */
export interface Message {
  role: Role;
  content: string;
}

/**
 * Simple conversation buffer for managing chat history.
 *
 * The Servo backend currently accepts a single `prompt` string,
 * so this class compiles message history into a formatted prompt.
 */
export class Conversation {
  private systemPrompt?: string;
  private maxTurns: number;
  private messages: Message[];

  constructor(systemPrompt?: string, maxTurns: number = 10) {
    this.systemPrompt = systemPrompt;
    this.maxTurns = maxTurns;
    this.messages = [];
  }

  /**
   * Add a user message to the conversation.
   */
  addUser(content: string): void {
    this.messages.push({ role: 'user', content });
    this.trim();
  }

  /**
   * Add an assistant message to the conversation.
   */
  addAssistant(content: string): void {
    this.messages.push({ role: 'assistant', content });
    this.trim();
  }

  /**
   * Build a formatted prompt string from the conversation history.
   */
  buildPrompt(nextUserMessage?: string): string {
    const parts: string[] = [];

    if (this.systemPrompt) {
      parts.push(`System:\n${this.systemPrompt}\n`);
    }

    for (const message of this.messages) {
      const label = message.role === 'user' ? 'User' : 'Assistant';
      parts.push(`${label}:\n${message.content}\n`);
    }

    if (nextUserMessage) {
      parts.push(`User:\n${nextUserMessage}\n`);
    }

    return parts.join('\n').trim();
  }

  /**
   * Trim messages to respect maxTurns limit.
   */
  private trim(): void {
    if (this.messages.length > this.maxTurns * 2) {
      this.messages = this.messages.slice(-this.maxTurns * 2);
    }
  }

  /**
   * Get all messages in the conversation.
   */
  getMessages(): Message[] {
    return [...this.messages];
  }

  /**
   * Clear all messages from the conversation.
   */
  clear(): void {
    this.messages = [];
  }
}
