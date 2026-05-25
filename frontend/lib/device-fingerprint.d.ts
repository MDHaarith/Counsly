export function buildDeviceFingerprintSource(env?: {
  navigator?: {
    hardwareConcurrency?: number;
    language?: string;
    platform?: string;
    userAgent?: string;
  };
  screen?: {
    colorDepth?: number;
    height?: number;
    width?: number;
  };
  timezone?: string;
}): string;

export function createDeviceFingerprint(env?: Record<string, unknown>): Promise<string>;

export function isSha256Hex(value?: string): boolean;
