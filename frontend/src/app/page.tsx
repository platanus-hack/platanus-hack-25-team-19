'use client'

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function Home() {
  const [inputValue, setInputValue] = useState("");

  const router = useRouter();

  const handleSubmit = () => {
    if (inputValue.trim()) {
      localStorage.setItem('conversation-messages', JSON.stringify([{ role: 'user', content: inputValue }]));
      router.push('/conversation');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-(--color-background) px-4">
      <main className="flex w-full max-w-3xl flex-col items-center text-center">
        <h1 className="mb-4 text-5xl font-semibold tracking-tight text-(--color-text) md:text-6xl lg:text-7xl">
          Linear-Inspired Landing
        </h1>

        <p className="mb-12 text-lg text-(--color-text-secondary) md:text-xl">
          A beautiful, minimal interface for your next project
        </p>

        <div className="w-full max-w-xl">
          <div className="relative flex items-center rounded-lg border border-(--color-input-border) bg-(--color-input-bg)">
            <input
              type="text"
              placeholder="Enter your text here..."
              className="w-full bg-transparent px-5 py-4 text-base text-(--color-text) outline-none placeholder:text-(--color-text-secondary)"
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button
              className="absolute right-2 rounded-md bg-(--color-primary) px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-(--color-primary-hover) hover:cursor-pointer"
              onClick={handleSubmit}
            >
              Enter
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
