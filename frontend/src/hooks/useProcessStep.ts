"use client";

import { usePathname } from "next/navigation";

export function useProcessStep(): number {
  const pathname = usePathname();

  // Map routes to step numbers
  switch (pathname) {
    case "/":
      return 0; // Identificación - Homepage where user defines the problem
    case "/conversation":
      return 0; // Identificación - Conversation step for gathering information
    case "/jobs":
      return 1; // Análisis - Conversation/investigation phase
    case "/summary":
      return 2; // Resumen - Final summary step
    default:
      return 0; // Default to first step
  }
}
