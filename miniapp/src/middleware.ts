import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const rateLimit = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT = 100;
const WINDOW_MS = 60 * 1000;

function getClientIp(request: NextRequest): string {
  return (
    request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ||
    request.headers.get('x-real-ip') ||
    'unknown'
  );
}

export function middleware(request: NextRequest) {
  if (!request.nextUrl.pathname.startsWith('/api/')) {
    return NextResponse.next();
  }

  const ip = getClientIp(request);
  const now = Date.now();
  
  const entry = rateLimit.get(ip);
  
  if (entry && entry.resetTime > now && entry.count >= RATE_LIMIT) {
    return NextResponse.json(
      { error: 'Too many requests. Please try again later.' },
      { status: 429 }
    );
  }
  
  if (entry && entry.resetTime <= now) {
    rateLimit.delete(ip);
  }
  
  const current = rateLimit.get(ip);
  rateLimit.set(ip, {
    count: (current?.count || 0) + 1,
    resetTime: current?.resetTime || now + WINDOW_MS
  });
  
  return NextResponse.next();
}

export const config = {
  matcher: '/api/:path*'
};
