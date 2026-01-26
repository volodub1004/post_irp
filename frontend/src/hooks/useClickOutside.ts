/**
 * @file useClickOutside.ts
 * @description
 * Custom React hook for detecting clicks or key presses that occur
 * outside a referenced element. Commonly used for closing dropdowns,
 * modals, or popovers when a user clicks elsewhere or presses Escape.
 *
 * Example usage:
 * ```tsx
 * const ref = useRef<HTMLDivElement>(null);
 * useClickOutside(ref, () => setIsOpen(false));
 * ```
 *
 * @module useClickOutside
 */

import { useEffect } from "react";

/**
 * useClickOutside
 * 
 * Listens for global click (mousedown) and keyboard (Escape key) events.
 * When the user clicks outside the provided element or presses Escape,
 * it executes the provided `onClose` callback.
 *
 * @template T HTMLElement subtype for the ref
 * @param {React.RefObject<T>} ref - React ref for the target element
 * @param {() => void} onClose - Callback to run when an outside click or Escape press occurs
 */
export function useClickOutside<T extends HTMLElement>(
  ref: React.RefObject<T>,
  onClose: () => void
) {
  useEffect(() => {
    /**
     * Handles mouse click events.
     * If the click target is outside the referenced element, trigger `onClose`.
     */
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    };

    /**
     * Handles keyboard events.
     * If the Escape key is pressed, trigger `onClose`.
     */
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };

    // Attach global event listeners
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleEscape);

    // Cleanup when component unmounts or dependencies change
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [ref, onClose]);
}
