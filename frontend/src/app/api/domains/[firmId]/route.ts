/**
 * @file route.ts
 * @description
 * Dynamic API route handler for retrieving all email domains associated
 * with a specific investment firm. Used by the frontend's domain dropdown
 * once a firm is selected in the investor email prediction UI.
 *
 * Route: /api/domains/[firmId]
 * Example: /api/domains/42
 *
 * Method: GET
 * Response: JSON array of domain strings for the given firm ID
 *
 * @returns {Promise<Response>} JSON response containing firm domains
 */

import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

/**
 * GET /api/domains/[firmId]
 * 
 * Fetches all domains belonging to a firm by numeric ID.
 * Handles invalid IDs gracefully and returns empty arrays
 * for valid firms with no associated domains.
 */
export async function GET(
  _: Request,
  context: { params: Promise<{ firmId: string }> }
) {
  // Extract and validate path parameters
  const { firmId } = await context.params;  // Await required in Next.js 14+
  const id = parseInt(firmId);

  if (isNaN(id)) {
    // Invalid firm ID (non-numeric, malformed, etc.)
    return NextResponse.json(
      { error: "Invalid firm ID" },
      { status: 400 }
    );
  }

  // Query Prisma for all domains linked to this firm
  try {
    const domains = await prisma.domain.findMany({
      where: { firmId: id },
      select: { domain: true },
    });

    // Extract plain string array
    const domainList = domains.map((d) => d.domain);

    return NextResponse.json(domainList, { status: 200 });
  } catch (err) {
    console.error("Database query failed:", err);
    return NextResponse.json(
      { error: "Internal server error while fetching domains" },
      { status: 500 }
    );
  }
}
