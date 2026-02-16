import { ServoAPIError, ServoConnectionError } from './errors';

/**
 * Internal HTTP client for making requests to the Servo backend.
 */
export class HTTPClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;

  constructor(baseUrl: string, apiKey?: string, timeout: number = 30000) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
    this.timeout = timeout;
  }

  /**
   * Make a JSON request to the backend.
   */
  async requestJson(method: string, path: string, jsonBody?: any): Promise<any> {
    const url = this.joinUrl(this.baseUrl, path);
    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const options: RequestInit = {
      method: method.toUpperCase(),
      headers,
      signal: AbortSignal.timeout(this.timeout),
    };

    if (jsonBody !== undefined) {
      options.body = JSON.stringify(jsonBody);
      headers['Content-Type'] = 'application/json';
    }

    let response: Response;
    try {
      response = await fetch(url, options);
    } catch (error) {
      if (error instanceof Error) {
        throw new ServoConnectionError(
          `Failed to connect to ${url}: ${error.message}`,
          error
        );
      }
      throw new ServoConnectionError(`Failed to connect to ${url}`);
    }

    const contentType = response.headers.get('content-type') || '';
    let data: any;

    try {
      if (contentType.includes('application/json')) {
        const text = await response.text();
        data = text ? JSON.parse(text) : null;
      } else {
        data = await response.text();
      }
    } catch (error) {
      data = null;
    }

    if (!response.ok) {
      throw new ServoAPIError(
        `Servo API error (${response.status}) for ${method} ${path}`,
        response.status,
        data
      );
    }

    return data;
  }

  private joinUrl(base: string, path: string): string {
    return base.replace(/\/$/, '') + '/' + path.replace(/^\//, '');
  }
}
