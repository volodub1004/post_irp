/**
 * @file route.ts
 * @description
 * API route handler for fuzzy-searching firms by name.
 *
 * This endpoint powers the firm autocomplete in the investor email prediction UI.
 * The frontend queries this route dynamically as the user types to retrieve
 * matching firms from the database using a case-insensitive substring match.
 *
 * Route: /api/firms?query=<string>
 * Example: /api/firms?query=sequoia
 *
 * Method: GET
 * Response: JSON array of objects [{ id: number, name: string }]
 */

import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

/**
 * GET /api/firms?query=<string>
 *
 * Returns a list of firms whose names contain the given query string.
 * Querying is case-insensitive and limited to 20 results for performance.
 */
export async function GET(req: Request) {
    try {
        // Extract and validate query string
        const url = new URL(req.url);
        const query = url.searchParams.get("query")?.trim() ?? "";

        // Short-circuit empty or too-short queries
        if (query.length < 2) {
            return NextResponse.json([], { status: 200 });
        }

        // Fetch matching firms from Prisma
        const firms = await prisma.firm.findMany({
            where: {
                name: {
                    contains: query,
                    mode: "insensitive", // case-insensitive search
                },
            },
            select: {
                id: true,
                name: true,
            },
            take: 20, // limit autocomplete results
        });

        // Return clean JSON response
        return NextResponse.json(firms, { status: 200 });
    } catch (err) {
        console.error("Error fetching firms:", err);
        return NextResponse.json(
            { error: "Internal server error while fetching firms" },
            { status: 500 }
        );
    }
}
