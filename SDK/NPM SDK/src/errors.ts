/**
 * Base error class for all Servo SDK errors.
 */
export class ServoSDKError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ServoSDKError';
    Object.setPrototypeOf(this, ServoSDKError.prototype);
  }
}

/**
 * Error thrown when the Servo API returns an error response.
 */
export class ServoAPIError extends ServoSDKError {
  public readonly statusCode: number;
  public readonly body: any;

  constructor(message: string, statusCode: number, body?: any) {
    super(message);
    this.name = 'ServoAPIError';
    this.statusCode = statusCode;
    this.body = body;
    Object.setPrototypeOf(this, ServoAPIError.prototype);
  }
}

/**
 * Error thrown when connection to the Servo backend fails.
 */
export class ServoConnectionError extends ServoSDKError {
  public readonly cause?: Error;

  constructor(message: string, cause?: Error) {
    super(message);
    this.name = 'ServoConnectionError';
    this.cause = cause;
    Object.setPrototypeOf(this, ServoConnectionError.prototype);
  }
}
