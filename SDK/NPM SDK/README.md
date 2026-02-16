# Servo SDK (JavaScript/TypeScript)

JavaScript/TypeScript SDK for the Servo backend (routing/classification).

## Features

✅ **Simple 3-step API** - Initialize, send, receive  
✅ **TypeScript support** - Full type definitions included  
✅ **Conversation management** - Built-in chat history handling  
✅ **Modern JavaScript** - ES modules + CommonJS support  
✅ **Zero dependencies** - Uses native fetch API (Node.js 18+)

## Installation

```bash
npm install servo-sdk
```

## Quick Start

```javascript
const { Servo } = require('servo-sdk');

// 1. Initialize client
const client = new Servo({
  apiKey: 'your-api-key',
  baseUrl: 'http://localhost:8000',
  defaultUserId: 'default_user'
});

// 2. Send request
const result = await client.send('Who was the first president of the United States?');

// 3. Receive response
console.log(result.classification.category_id);  // e.g., 'simple' or 'complex'
console.log(result.target_model);                // e.g., 'gemma-3-27b-it'
console.log(result.llm_response);                // actual LLM response
```

## Usage

### Basic Usage

```javascript
import { Servo } from 'servo-sdk';

const client = new Servo({
  apiKey: 'ADAWODWA',
  baseUrl: 'http://localhost:8000',  // optional, defaults to localhost:8000
  timeout: 30000,                     // optional, defaults to 30000ms
  defaultUserId: 'default_user',      // optional, defaults to 'default_user'
});

const result = await client.send('What is machine learning?');
console.log(result);
```

### With Conversation Context

```javascript
import { Servo, Conversation } from 'servo-sdk';

const client = new Servo({ apiKey: 'your-key' });

// Create a conversation with system prompt
const conversation = new Conversation('You are a helpful AI assistant.');

// Or use the client's built-in conversation
const conv = client.withConversation();
conv.addUser('Hello!');
conv.addAssistant('Hi there!');

// Send with conversation context
const result = await client.send('What did we just discuss?', {
  conversation: conv
});
```

### Step-by-Step Processing

```javascript
// Step 1: Classify the prompt
const classification = await client.classify(
  'Explain quantum computing',
  undefined,  // userId (optional, uses defaultUserId)
  false       // useQuick (default: false)
);

console.log(classification.category_id);         // e.g., 'simple' or 'complex'
console.log(classification.category_name);       // e.g., 'Simple' or 'Complex'
console.log(classification.confidence);          // 0.0 - 1.0
console.log(classification.requires_chunking);   // boolean

// Step 2: Route to appropriate model
const routing = await client.route(classification);
console.log(routing.target_model);  // e.g., 'gemini-2.5-flash'
```

### Health Check & Tiers

```javascript
// Check backend health
const health = await client.health();
console.log(health);

// Get available model tiers
const tiers = await client.tiers();
console.log(tiers.tiers);  // { simple: 'gemma-3-27b-it', complex: 'gemini-2.5-flash' }

// Get available categories with full metadata
const categories = await client.categories();
console.log(categories.user_id);             // 'default_user'
console.log(categories.default_category_id); // 'simple'
console.log(categories.categories);          // array of ClassificationCategory
```

## API Reference

### `Servo`

Main client class for interacting with the Servo backend.

#### Constructor

```typescript
new Servo(config?: ServoConfig)
```

**ServoConfig:**
- `apiKey?: string` - API key for authentication
- `baseUrl?: string` - Backend URL (default: `'http://localhost:8000'`)
- `timeout?: number` - Request timeout in ms (default: `30000`)
- `defaultUserId?: string` - Default user ID for requests (default: `'default_user'`)

#### Methods

##### `send(requestMessage: string, userId?: string, options?: SendOptions): Promise<ProcessingResult>`

Main method for sending requests. Returns full processing result including classification, routing, and LLM response.

**Parameters:**
- `requestMessage: string` - The user's prompt
- `userId?: string` - User ID (optional, uses defaultUserId if not provided)
- `options?: SendOptions` - Additional options

**Options:**
- `useQuickClassify?: boolean` - Use quick classification (default: `false`)
- `conversation?: Conversation` - Conversation context for multi-turn chat

##### `classify(prompt: string, userId?: string, useQuick?: boolean): Promise<ClassificationResult>`

Classify a prompt to determine category.

##### `route(classification: ClassificationResult, userId?: string): Promise<RouteResponse>`

Route a classification to determine the target model.

##### `health(): Promise<Record<string, any>>`

Check backend health status.

##### `tiers(userId?: string): Promise<TiersResponse>`

Get available model tiers (category_id -> model_id mapping).

##### `categories(userId?: string): Promise<CategoriesResponse>`

Get full category metadata for a user.

##### `withConversation(conversation?: Conversation): Conversation`

Initialize or retrieve a conversation for context management.

### `Conversation`

Manages chat history and builds formatted prompts.

#### Constructor

```typescript
new Conversation(systemPrompt?: string, maxTurns?: number)
```

#### Methods

- `addUser(content: string): void` - Add a user message
- `addAssistant(content: string): void` - Add an assistant message
- `buildPrompt(nextUserMessage?: string): string` - Build formatted prompt
- `getMessages(): Message[]` - Get all messages
- `clear(): void` - Clear conversation history

### Types

#### `ProcessingResult`

```typescript
interface ProcessingResult {
  classification: ClassificationResult;
  target_model: string;
  selected_category: ClassificationCategory;
  llm_response: string | null;
  chunks?: string[];
  chunk_metadata?: ChunkMetadata[];
  requires_aggregation?: boolean;
}
```

#### `ClassificationResult`

```typescript
interface ClassificationResult {
  category_id: string;
  category_name: string;
  reasoning: string;
  requires_chunking: boolean;
  confidence: number;  // 0.0 - 1.0
}
```

#### `ClassificationCategory`

```typescript
interface ClassificationCategory {
  id: string;
  name: string;
  description: string;
  provider: string;
  endpoint: string;
  model_id: string;
  request_defaults?: Record<string, any>;
}
```

#### `CategoriesResponse`

```typescript
interface CategoriesResponse {
  user_id: string;
  default_category_id: string;
  categories: ClassificationCategory[];
}
```

#### `TiersResponse`

```typescript
interface TiersResponse {
  tiers: Record<string, string>;  // { category_id: model_id }
}
```

## Error Handling

```javascript
import { ServoAPIError, ServoConnectionError } from 'servo-sdk';

try {
  const result = await client.send('test');
} catch (error) {
  if (error instanceof ServoAPIError) {
    console.error('API Error:', error.statusCode, error.body);
  } else if (error instanceof ServoConnectionError) {
    console.error('Connection Error:', error.message);
  } else {
    console.error('Unknown Error:', error);
  }
}
```

## Requirements

- **Node.js 18+** (for native fetch API)
- **TypeScript 5+** (if using TypeScript)

## Building from Source

```bash
# Install dependencies
npm install

# Build the package
npm run build

# Output will be in dist/ folder
```

## License

UNLICENSED

## Contributing

Servo SDK Contributors
