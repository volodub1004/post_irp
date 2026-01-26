import { NextRequest, NextResponse } from "next/server";

/**
 * @file route.ts
 * @description
 * Next.js API route that acts as a proxy between the frontend UI
 * and the FastAPI backend running the CatBoost email prediction model.
 *
 * Route: /api/predict
 */

/**
 * Handles POST requests from the frontend to the `/api/predict` endpoint.
 */
export async function POST(req: NextRequest) {
  try {
    // Parse frontend input
    const body = await req.json();
    const { investor, firm, domain } = body;

    // Forward the request to FastAPI backend (CatBoost model)
    const res = await fetch("http://127.0.0.1:8000/predict/catboost_verified", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: investor,
        firm: firm,
        domain: domain || null,
        top_k: 3, // limit top-k predictions
      }),
    });

    // Handle backend errors
    if (!res.ok) {
      const errorText = await res.text();
      return NextResponse.json({ error: errorText }, { status: res.status });
    }

    // Transform backend response for frontend consumption
    const data = await res.json();

    // Backend returns: [{ email: string, score: float }]
    // Convert to frontend format: [{ email, confidence }]
    const predictions = data.map((item: any) => ({
      email: item.email,
      confidence: item.score, // Convert to percentage
    }));

    // Return standardized JSON response
    return NextResponse.json({ predictions });
  } catch (err: any) {
    // Catch unexpected runtime/network errors
    console.error("Prediction route error:", err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
