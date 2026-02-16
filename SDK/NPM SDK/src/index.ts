// Main client
export { Servo } from './client';

// Context management
export { Conversation, Message, Role } from './context';

// Types
export {
  ClassificationResult,
  ClassificationCategory,
  ChunkMetadata,
  ProcessingResult,
  RouteResponse,
  TiersResponse,
  CategoriesResponse,
  ServoConfig,
  SendOptions,
} from './types';

// Errors
export {
  ServoSDKError,
  ServoAPIError,
  ServoConnectionError,
} from './errors';
