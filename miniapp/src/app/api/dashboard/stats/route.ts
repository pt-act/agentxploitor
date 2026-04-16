import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const stats = {
      activeAudits: 2,
      completedToday: 5,
      criticalFindings: 3,
      totalFindings: 27,
    };

    return NextResponse.json(stats);
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
