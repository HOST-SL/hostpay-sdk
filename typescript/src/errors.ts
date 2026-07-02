/** Exception hierarchy for the HostPay SDK. */

export class HostPayError extends Error {
  status?: number;
  detail?: unknown;
  constructor(message: string, status?: number, detail?: unknown) {
    super(message);
    this.name = new.target.name;
    this.status = status;
    this.detail = detail;
  }
}

/** Invalid or missing api-key / secret-key (401, 403). */
export class AuthenticationError extends HostPayError {}
/** Bad request, not found, or validation error (400, 404, 422). */
export class InvalidRequestError extends HostPayError {}
/** Too many requests (429). */
export class RateLimitError extends HostPayError {}
/** Server-side error (5xx). */
export class APIError extends HostPayError {}
/** Network problem reaching the API. */
export class APIConnectionError extends HostPayError {}
/** A webhook signature could not be verified. */
export class SignatureVerificationError extends HostPayError {}

export function errorFromStatus(
  status: number,
  message: string,
  detail: unknown,
): HostPayError {
  if (status === 401 || status === 403)
    return new AuthenticationError(message, status, detail);
  if (status === 429) return new RateLimitError(message, status, detail);
  if (status >= 400 && status < 500)
    return new InvalidRequestError(message, status, detail);
  return new APIError(message, status, detail);
}
