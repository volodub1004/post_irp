/**
 * @file Home.tsx
 * @description
 * Main page component for the investor email prediction UI.
 *
 * Provides three input controls:
 *  - Investor Name: free-text field
 *  - Firm: autocomplete input powered by the /api/firms endpoint
 *  - Domain: conditional dropdown fetched via /api/domains/[firmId]
 *
 * Both dropdowns (firm + domain) close automatically when the user clicks outside.
 * The component is designed to later integrate with the prediction API.
 *
 * @module Home
 * @returns {JSX.Element} Fully rendered page component
 * 
 * @example
 * // Example usage (Next.js automatically renders this as the index page)
 * export default function Home() {
 *   return <Home />;
 * }
 */

"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import { useClickOutside } from "@/hooks/useClickOutside";

// Firm interface for typed Prisma API responses
interface Firm {
  id: number;
  name: string;
}

export default function Home() {
  // React state variables

  // Form fields
  const [investor, setInvestor] = useState("");               // Investor name (free text)
  const [firm, setFirm] = useState("");                       // Firm name (typed text)
  const [firmId, setFirmId] = useState<number | null>(null);  // Firm ID (used for domain lookups)
  const [domain, setDomain] = useState("");                   // Selected domain for firm

  // API-driven data
  const [firms, setFirms] = useState<Firm[]>([]);             // Fuzzy-matched firm list from /api/firms
  const [domains, setDomains] = useState<string[]>([]);       // Domains belonging to selected firm

  // UI control states
  const [showDropdown, setShowDropdown] = useState(false);    // Controls visibility of firm autocomplete
  const [showDomainDropdown, setShowDomainDropdown] = useState(false); // Controls visibility of domain dropdown
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<{ email: string; confidence: number }[]>([]);

  // Data fetching logic

  /**
   * Fetch firm suggestions as the user types.
   * - Triggers only for 2+ characters to reduce API load.
   * - Cancels previous requests using AbortController to avoid race conditions.
   */
  useEffect(() => {
    if (firm.trim().length < 2) {
      setFirms([]);
      return;
    }

    const controller = new AbortController();

    const fetchFirms = async () => {
      try {
        const res = await fetch(`/api/firms?query=${encodeURIComponent(firm)}`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error("Failed to fetch firms");
        const data = await res.json();
        setFirms(data);
      } catch (err) {
        // Ignore abort errors (these happen when typing quickly)
        if (!(err instanceof DOMException && err.name === "AbortError"))
          console.error(err);
      }
    };

    fetchFirms();
    return () => controller.abort(); // cleanup on re-render or unmount
  }, [firm]);

  /**
   * Fetch domains whenever a firm is selected.
   * - Triggered by firmId changes (set after firm selection).
   * - Sets both the domains list and the default selected domain.
   */
  useEffect(() => {
    if (!firmId) return;

    const fetchDomains = async () => {
      const res = await fetch(`/api/domains/${firmId}`);
      const data = await res.json();
      setDomains(data);
      setDomain(data[0] || ""); // pick the first domain automatically
    };

    fetchDomains();
  }, [firmId]);

  // Event handlers

  /**
   * Handle firm selection from autocomplete list.
   * - Sets both firm name and firmId.
   * - Closes the dropdown once selected.
   */
  const handleFirmSelect = (f: Firm) => {
    setFirm(f.name);
    setFirmId(f.id);
    setShowDropdown(false);
  };

  /**
   * Handles Prediction.
   * 
   */
  const handlePredict = async () => {
    if (!investor || !firm) return alert("Please enter an investor name and firm.");
    setLoading(true);
    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ investor, firm, domain }),
      });
      if (!res.ok) throw new Error("Prediction request failed");
      const data = await res.json();
      setResults(data.predictions || []);
    } catch (err) {
      console.error(err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Dropdown close logic (click outside)

  // Refs for both dropdown wrappers
  const firmRef = useRef<HTMLDivElement | null>(null);
  const domainRef = useRef<HTMLDivElement | null>(null);

  // Attach click-outside handlers to close dropdowns
  useClickOutside(firmRef, () => setShowDropdown(false));
  useClickOutside(domainRef, () => setShowDomainDropdown(false));

  // ---------------------------------------------------------------------------
  // Render JSX
  // ---------------------------------------------------------------------------

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 font-sans">
      {/* Logo header */}
      <Image
        src="/AIP.png"
        alt="AIP logo"
        width={160}
        height={34}
        className="mb-8 dark:invert"
      />

      {/* Main input section */}
      <div className="flex flex-col gap-6 w-full max-w-sm">

        {/* Investor Name Input */}
        <div>
          <label className="block text-sm font-medium mb-1">Investor Name</label>
          <input
            type="text"
            value={investor}
            onChange={(e) => setInvestor(e.target.value)}
            placeholder="e.g. John Smith"
            className="w-full px-3 py-2 border rounded-lg focus:ring focus:ring-blue-400"
          />
        </div>

        {/* Firm Name Autocomplete */}
        <div className="relative w-full max-w-sm" ref={firmRef}>
          <label className="block text-sm font-medium mb-1">Firm</label>

          <input
            type="text"
            value={firm}
            onChange={(e) => {
              setFirm(e.target.value);     // Update input text
              setShowDropdown(true);       // Open dropdown
            }}
            onFocus={() => setShowDropdown(true)} // Reopen on focus
            onBlur={() => setTimeout(() => setShowDropdown(false), 100)} // Delay to allow click selection
            placeholder="Start typing firm name..."
            className="w-full px-3 py-2 border rounded-lg"
          />

          {/* Autocomplete dropdown */}
          {showDropdown && firms.length > 0 && (
            <ul
              className="
                absolute left-0 right-0 top-full z-10
                border rounded-lg mt-1 bg-white shadow
                max-h-40 overflow-auto
              "
            >
              {firms.map((f) => (
                <li
                  key={f.id}
                  onMouseDown={(e) => e.preventDefault()} // Prevent blur before click
                  onClick={() => handleFirmSelect(f)}     // Select firm
                  className="px-3 py-1 hover:bg-gray-100 cursor-pointer"
                >
                  {f.name}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Domain Dropdown */}
        <div className="relative w-full max-w-sm" ref={domainRef}>
          <label className="block text-sm font-medium mb-1">Domain</label>

          {domains.length > 1 ? (
            <>
              {/* Active domain display (click to expand dropdown) */}
              <div
                className="w-full px-3 py-2 border rounded-lg bg-white cursor-pointer"
                onClick={() => setShowDomainDropdown((prev) => !prev)}
              >
                {domain || domains[0]}
              </div>

              {/* Dropdown with multiple domains */}
              {showDomainDropdown && (
                <ul className="absolute left-0 right-0 top-full z-10 border rounded-lg mt-1 bg-white shadow max-h-40 overflow-auto">
                  {domains.map((d) => (
                    <li
                      key={d}
                      onMouseDown={(e) => e.preventDefault()} // Prevent losing focus
                      onClick={() => {
                        setDomain(d);
                        setShowDomainDropdown(false);
                      }}
                      className="px-3 py-1 hover:bg-gray-100 cursor-pointer"
                    >
                      {d}
                    </li>
                  ))}
                </ul>
              )}
            </>
          ) : (
            // Single-domain (readonly) state
            <input
              type="text"
              value={domains[0] || ""}
              readOnly
              placeholder="Select a firm first"
              className="w-full px-3 py-2 border rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
            />
          )}
        </div>
        {/* Predict Button */}
        <button
          onClick={handlePredict}
          disabled={
            loading ||
            investor.trim().length === 0 ||
            firm.trim().length === 0 ||
            domain.trim().length === 0
          }
          className={`mt-4 w-full font-semibold py-2 px-4 rounded-lg transition-colors
    ${loading ||
              !investor.trim() ||
              !firm.trim() ||
              !domain.trim()
              ? "bg-gray-300 text-gray-600 cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700"
            }`}
        >
          {loading ? "Predicting..." : "Predict"}
        </button>

        {/* Results Display */}
        {results.length > 0 && (
          <div className="mt-4 border rounded-lg p-4 bg-gray-50">
            <h3 className="font-semibold mb-2 text-gray-800">Predicted Emails</h3>
            <ul className="list-disc list-inside text-sm text-gray-700">
              {results.map((r, i) => (
                <li key={i} className="mb-1">
                  <span className="font-mono">{r.email}</span>{" "}
                  <span className="text-gray-500">({r.confidence.toFixed(1)}%)</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}