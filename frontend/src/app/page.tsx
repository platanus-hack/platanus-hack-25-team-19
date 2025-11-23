"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect, useMemo } from "react";
import { ArrowUp } from "lucide-react";
import ProcessStepper from "@/components/ProcessStepper";

export default function Home() {
  const [inputValue, setInputValue] = useState("");
  const [currentActionIndex, setCurrentActionIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [text, setText] = useState("");

  const router = useRouter();

  const actions = useMemo(
    () => [
      { text: "antes de gastar de más", color: "text-(--color-text)" },
      { text: "prioriza lo que importa", color: "text-(--color-text)" },
      { text: "no pierdas tiempo", color: "text-(--color-text)" },
    ],
    []
  );

  useEffect(() => {
    const currentAction = actions[currentActionIndex];
    const fullText = currentAction.text;

    if (!isDeleting && text === fullText) {
      const timeout = setTimeout(() => setIsDeleting(true), 2000);
      return () => clearTimeout(timeout);
    }

    if (isDeleting && text === "") {
      const timeout = setTimeout(() => {
        setIsDeleting(false);
        setCurrentActionIndex((prev) => (prev + 1) % actions.length);
      }, 50);
      return () => clearTimeout(timeout);
    }

    const timeout = setTimeout(
      () => {
        if (isDeleting) {
          setText(fullText.substring(0, text.length - 1));
        } else {
          setText(fullText.substring(0, text.length + 1));
        }
      },
      isDeleting ? 50 : 100
    );

    return () => clearTimeout(timeout);
  }, [text, isDeleting, currentActionIndex, actions]);

  const handleSubmit = () => {
    if (inputValue.trim()) {
      localStorage.setItem(
        "conversation-messages",
        JSON.stringify([{ role: "user", content: inputValue }])
      );
      router.push("/conversation");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-(--color-background) px-4">
      {/* Process Stepper */}
      <div className="w-full max-w-5xl mb-16">
        <ProcessStepper currentStep={0} />
      </div>

      {/* Main Content */}
      <main className="flex w-full max-w-3xl flex-col items-center text-center">
        <h1 className="text-emerald-400 min-h-[2.5em] text-4xl font-semibold tracking-tight md:text-6xl lg:text-7xl">
          GreenLight{" "}
          <span
            className={`${actions[currentActionIndex].color} transition-colors duration-300`}
          >
            {text}
            <span className="animate-pulse">|</span>
          </span>
        </h1>
        <p className="mb-12 max-w-xl text-lg text-(--color-text-secondary) md:text-xl">
          Resolver el problema equivocado sale carísimo: compara, investiga y
          confirma.
        </p>

        <div className="w-full max-w-xl">
          <div className="relative flex items-end rounded-xl border border-(--color-input-border) bg-(--color-input-bg)">
            <textarea
              placeholder="¿Qué problema grande buscas resolver?"
              className={`w-full bg-transparent px-5 py-4 text-base text-(--color-text) outline-none placeholder:text-(--color-text-secondary) resize-none ${
                inputValue.trim() ? "pr-14" : ""
              }`}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={3}
            />
            {inputValue.trim() && (
              <button
                className="absolute right-2 bottom-2 rounded-full bg-(--color-primary) p-2 text-white transition-all hover:bg-(--color-primary-hover) hover:scale-105 shadow-lg cursor-pointer"
                onClick={handleSubmit}
                aria-label="Submit"
              >
                <ArrowUp size={20} strokeWidth={2.5} />
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
