"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect, useMemo } from "react";
import { ArrowRight, Sparkles } from "lucide-react";
import ProcessStepper from "@/components/ProcessStepper";

export default function Home() {
  const [inputValue, setInputValue] = useState("");
  const [currentActionIndex, setCurrentActionIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [text, setText] = useState("");

  const router = useRouter();

  const actions = useMemo(
    () => [
      { text: "gastar de más", color: "text-white" },
      { text: "priorizar mal", color: "text-white" },
      { text: "perder tiempo", color: "text-white" },
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

    <section className="relative min-h-screen overflow-hidden border-b border-(--color-border) bg-(--color-background)">
      {/* Grid background pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-size-[64px_64px]" />
      <div className="relative mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:px-8 flex items-center justify-center min-h-screen">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mx-auto max-w-2xl mb-24 -mt-28">
            <ProcessStepper currentStep={0} />
          </div>
          {/* Badge */}
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-sm text-(--color-primary)">
            <Sparkles className="h-4 w-4" />
            <span className="font-mono">Tu equipo de consultoría IA</span>
          </div>

          {/* Main heading with animation */}
          <h1 className="mb-6 text-balance font-sans text-5xl font-bold tracking-tight text-(--color-text) sm:text-6xl lg:text-7xl min-h-[2.5em]">
            <span className="text-emerald-400">GreenLight</span> antes de{" "}
            <br />
            <span
              className={`${actions[currentActionIndex].color} transition-colors duration-300`}
            >
              {text}
              <span className="animate-pulse">|</span>
            </span>
          </h1>

          {/* Description */}
          <p className="mb-10 text-pretty text-lg leading-relaxed text-(--color-text-secondary) sm:text-xl">
            Utiliza agentes de IA para investigar a fondo, dialogar con stakeholders y validar tus ideas.
            Obtén un documento completo de investigación en formato listo para accionar.
          </p>

          {/* Input area */}
          <div className="w-full max-w-2xl mx-auto mb-6">
            <div className="relative flex items-end rounded-xl border border-(--color-input-border) bg-(--color-input-bg) shadow-lg">
              <input
                placeholder="¿Qué problema buscas resolver?"
                className={`w-full bg-transparent px-5 py-4 text-base text-(--color-text) outline-none placeholder:text-(--color-text-secondary) resize-none ${
                  inputValue.trim() ? "pr-14" : ""
                }`}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <button
                className="disabled:cursor-not-allowed disabled:bg-(--color-primary-disabled) absolute right-2 bottom-2 rounded-full bg-(--color-primary) p-2 text-white transition-all hover:bg-(--color-primary-hover) hover:scale-105 shadow-lg cursor-pointer"
                onClick={handleSubmit}
                aria-label="Comenzar investigación"
                disabled={!inputValue.trim()}
              >
                <ArrowRight size={20} strokeWidth={2.5} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
