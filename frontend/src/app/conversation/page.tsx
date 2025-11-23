"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect, useRef, Suspense } from "react";
import ReactMarkdown from "react-markdown";
import { ArrowUp, Edit3 } from "lucide-react";
import ProcessStepper from "@/components/ProcessStepper";
import { useProcessStep } from "@/hooks/useProcessStep";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL;

function ConversationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentStep = useProcessStep();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(() => searchParams.get('session_id'));
  const [showModal, setShowModal] = useState(false);
  const [synthesisMessage, setSynthesisMessage] = useState("");
  const [editableSynthesis, setEditableSynthesis] = useState("");
  const [temperature, setTemperature] = useState(0);
  const [isSynthesisLoading, setIsSynthesisLoading] = useState(false);
  const [continueRefining, setContinueRefining] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasInitialized = useRef(false);

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;

    const userMessage: Message = { role: "user", content: message };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const requestBody: { message: string; session_id?: string } = { message };
      if (sessionId) {
        requestBody.session_id = sessionId;
      }

      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();

      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
        // Update URL with session_id
        const newUrl = new URL(window.location.href);
        newUrl.searchParams.set('session_id', data.session_id);
        window.history.replaceState({}, '', newUrl.toString());
      }

      // Update temperature from response
      if (data.temperature !== undefined) {
        setTemperature(data.temperature);
      }

      // Parse the message field which contains JSON
      let messageContent =
        data.message || "No se recibió respuesta del servidor.";
      try {
        // Check if message contains JSON (starts with ```json)
        if (messageContent.includes("```json")) {
          const jsonMatch = messageContent.match(/```json\n([\s\S]*?)\n```/);
          if (jsonMatch && jsonMatch[1]) {
            const parsedJson = JSON.parse(jsonMatch[1]);
            messageContent = parsedJson.message || messageContent;
          }
        }
      } catch (error) {
        console.error("Error parsing message JSON:", error);
      }

      const assistantMessage: Message = {
        role: "assistant",
        content: messageContent,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      const assistantMessage: Message = {
        role: "assistant",
        content:
          "Error al conectar con el servidor. Por favor intenta de nuevo.",
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const savedMessages = localStorage.getItem("conversation-messages");

    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        if (parsed.length === 1) {
          handleSendMessage(parsed[0].content);
        } else {
          setMessages(parsed);
        }
      } catch (error) {
        console.error("Error loading messages:", error);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem("conversation-messages", JSON.stringify(messages));
    }
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(inputValue);
  };

  const handleClearConversation = () => {
    setMessages([]);
    setSessionId(null);
    localStorage.removeItem("conversation-messages");
    // Clear session_id from URL
    const newUrl = new URL(window.location.href);
    newUrl.searchParams.delete('session_id');
    window.history.replaceState({}, '', newUrl.toString());
  };

  const handleSynthesizeConversation = async () => {
    const synthesisPrompt =
      "Sintetiza esta conversación y dame el problema de fondo";

    // Show modal immediately with loading state
    setShowModal(true);
    setIsSynthesisLoading(true);
    setSynthesisMessage("");
    setEditableSynthesis("");

    try {
      const requestBody: { message: string; session_id?: string } = {
        message: synthesisPrompt,
      };
      if (sessionId) {
        requestBody.session_id = sessionId;
      }

      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();

      // Parse the message field which contains JSON
      let messageContent =
        data.message || "No se recibió respuesta del servidor.";
      try {
        // Check if message contains JSON (starts with ```json)
        if (messageContent.includes("```json")) {
          const jsonMatch = messageContent.match(/```json\n([\s\S]*?)\n```/);
          if (jsonMatch && jsonMatch[1]) {
            const parsedJson = JSON.parse(jsonMatch[1]);
            messageContent = parsedJson.message || messageContent;
          }
        }
      } catch (error) {
        console.error("Error parsing synthesis message JSON:", error);
        // Keep original message if parsing fails
      }

      setSynthesisMessage(messageContent);
      setEditableSynthesis(messageContent);
    } catch (error) {
      console.error("Error synthesizing conversation:", error);
      setSynthesisMessage(
        "Error al conectar con el servidor. Por favor intenta de nuevo."
      );
      setEditableSynthesis(
        "Error al conectar con el servidor. Por favor intenta de nuevo."
      );
    } finally {
      setIsSynthesisLoading(false);
    }
  };

  const handleCreateJobs = async () => {
    try {
      setIsLoading(true);
      const problemDeclaration = editableSynthesis || synthesisMessage || "";

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 900000);

      const response = await fetch(`${API_URL}/jobs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          full_problem_declaration: problemDeclaration,
          session_id: sessionId,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("current-jobs", JSON.stringify(data.jobs));
        setIsLoading(false);
        router.push(`/jobs${sessionId ? `?session_id=${sessionId}` : ''}`);
      } else {
        console.error("Failed to create jobs");
        setIsLoading(false);
        router.push(`/jobs${sessionId ? `?session_id=${sessionId}` : ''}`);
      }
    } catch (error) {
      console.error("Error creating jobs:", error);
      router.push(`/jobs${sessionId ? `?session_id=${sessionId}` : ''}`);
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-(--color-background)">
      {/* Process Stepper - Fixed positioning */}
      <div className="w-full bg-(--color-background) border-b border-(--color-border)/20">
        <div className="w-full max-w-5xl mx-auto py-4 px-6">
          <ProcessStepper currentStep={currentStep} />
        </div>
      </div>

      {/* Header */}
      <header className="border-b border-(--color-border) bg-(--color-background) px-6 py-4">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <button
            onClick={() => router.push("/")}
            className="cursor-pointer text-sm text-(--color-text-secondary) transition-colors hover:text-(--color-text)"
          >
            ← Volver al inicio
          </button>
          <h1 className="text-lg font-semibold text-(--color-text)">
            AI Conversation
          </h1>
          <button
            onClick={handleClearConversation}
            className="cursor-pointer text-sm text-(--color-text-secondary) transition-colors hover:text-red-400"
            title="Clear conversation"
          >
            Limpiar
          </button>
        </div>
      </header>

      {/* Messages Container */}
      <div
        className={`flex-1 overflow-y-auto px-4 py-8 ${
          temperature >= 6 && !continueRefining ? "pb-8" : "pb-80"
        }`}
      >
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.length === 0 && !isLoading && (
            <div className="flex h-full items-center justify-center py-20">
              <p className="text-lg text-(--color-text-secondary)">
                ¿Qué es lo que realmente quieres resolver?
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  message.role === "user"
                    ? "bg-(--color-primary) text-white"
                    : "border border-(--color-border) bg-(--color-input-bg) text-(--color-text)"
                }`}
              >
                {message.role === "assistant" ? (
                  <div className="prose prose-sm max-w-none text-(--color-text) prose-strong:font-semibold">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">
                    {message.content}
                  </p>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg border border-(--color-border) bg-(--color-input-bg) px-4 py-3">
                <div className="flex items-center space-x-2">
                  <div
                    className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)"
                    style={{ animationDelay: "0ms" }}
                  ></div>
                  <div
                    className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)"
                    style={{ animationDelay: "100ms" }}
                  ></div>
                  <div
                    className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)"
                    style={{ animationDelay: "300ms" }}
                  ></div>
                </div>
              </div>
            </div>
          )}

          {temperature >= 6 && !continueRefining && (
            <div className="pt-2">
              <div className="rounded-2xl border border-(--color-border) bg-(--color-background) shadow-xl p-6">
                <div className="text-center mb-6">
                  <h3 className="text-lg font-semibold text-(--color-text) mb-2">
                    Tu problema es válido, y amerita una investigación más
                    profunda
                  </h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={handleSynthesizeConversation}
                    className="cursor-pointer group relative overflow-hidden rounded-xl border-2 border-(--color-primary) bg-(--color-primary) hover:bg-(--color-primary-hover) p-6 text-left transition-all hover:shadow-xl hover:scale-105"
                  >
                    <div className="relative z-10">
                      <h4 className="text-base font-semibold text-white mb-1">
                        Comenzar análisis de solución
                      </h4>
                      <p className="text-sm text-white opacity-90">
                        Sintetizaremos esta conversación para encontrar el
                        problema de fondo y usarlo como punto de entrada para la
                        investigación.
                      </p>
                    </div>
                  </button>

                  {/* Continue Refining Option */}
                  <button
                    onClick={() => setContinueRefining(true)}
                    className="cursor-pointer group relative overflow-hidden rounded-xl border-2 border-(--color-border) bg-(--color-input-bg) hover:bg-(--color-background) p-6 text-left transition-all hover:shadow-xl hover:scale-105"
                  >
                    <div className="relative z-10">
                      <h4 className="text-base font-semibold text-(--color-text) mb-1">
                        Seguir refinando
                      </h4>
                      <p className="text-sm text-(--color-text-secondary)">
                        Si te faltan detalles, puedes continuar la conversación
                        para refinar aún más el problema de fondo
                      </p>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Floating Chat Box with Progress Bar */}
      {/* Only show floating component when not showing the choice component in flow */}
      {!(temperature >= 6 && !continueRefining) && (
        <div className="fixed bottom-6 left-0 right-0 z-50 px-4">
          <div className="mx-auto max-w-3xl">
            {/* Unified Floating Component */}
            <div className="rounded-2xl border border-(--color-border) bg-(--color-background) shadow-2xl backdrop-blur-xl bg-opacity-95 animate-slide-up">
              <>
                {/* Progress Bar Section (shown when messages exist) */}
                {messages.length > 0 && (
                  <div className="px-6 pt-5 pb-4 border-b border-(--color-border)">
                    {/* White to Purple Gradient Bar */}
                    <div className="relative h-2.5 w-full rounded-full bg-gray-800 overflow-hidden shadow-inner">
                      <div className="absolute inset-0 bg-linear-to-r from-white via-[#9BA1E8] to-primary opacity-30" />
                      <div
                        className="absolute inset-y-0 left-0 transition-all duration-500 ease-out rounded-full shadow-lg"
                        style={{
                          width: `${(Math.min(temperature, 7) / 7) * 100}%`,
                          background: `linear-gradient(90deg,
                            rgba(255, 255, 255, ${
                              temperature <= 2 ? "0.9" : "0.7"
                            }) 0%,
                            ${
                              temperature <= 2
                                ? "#E8E9FA"
                                : temperature <= 4
                                ? "#9BA1E8"
                                : "#5E6AD2"
                            } 100%)`,
                          boxShadow:
                            temperature >= 7
                              ? "0 0 20px rgba(94, 106, 210, 0.7)"
                              : temperature >= 4
                              ? "0 0 15px rgba(155, 161, 232, 0.5)"
                              : "0 0 10px rgba(255, 255, 255, 0.4)",
                        }}
                      >
                        {/* Animated shimmer effect */}
                        {temperature < 7 && (
                          <div className="absolute inset-0 bg-linear-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer" />
                        )}
                      </div>
                    </div>

                    {/* Status text and button */}
                    <div className="mt-3 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className="text-xs font-semibold transition-colors duration-300"
                          style={{
                            color:
                              temperature <= 2
                                ? "#A0A0A0"
                                : temperature <= 4
                                ? "#9BA1E8"
                                : temperature >= 7
                                ? "#5E6AD2"
                                : "#7580D8",
                          }}
                        >
                          {temperature >= 7
                            ? "✓ Problema definido"
                            : `${
                                temperature <= 2
                                  ? "Necesitamos más contexto"
                                  : temperature <= 4
                                  ? "Avanzando hacia el problema"
                                  : "Casi llegamos al problema real"
                              }`}
                        </span>
                      </div>

                      {(
                        <button
                          onClick={handleSynthesizeConversation}
                          className="cursor-pointer px-4 py-1.5 rounded-md bg-(--color-primary) hover:bg-(--color-primary-hover) text-white text-xs font-medium transition-all shadow-lg hover:shadow-xl animate-pulse"
                        >
                          Sintetizar problema →
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Chat Input Section */}
                <div className="p-4">
                  <form onSubmit={handleSubmit}>
                    <div className="relative flex items-end rounded-xl border border-(--color-input-border) bg-(--color-input-bg)">
                      <textarea
                        placeholder="Sigue profundizando..."
                        className={`w-full bg-transparent px-5 py-4 text-base text-(--color-text) outline-none placeholder:text-(--color-text-secondary) resize-none min-h-14 max-h-[200px] overflow-y-auto ${
                          inputValue.trim() || isLoading ? "pr-14" : ""
                        }`}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        disabled={isLoading}
                        rows={1}
                        onInput={(e) => {
                          const target = e.target as HTMLTextAreaElement;
                          target.style.height = "56px";
                          target.style.height =
                            Math.min(target.scrollHeight, 200) + "px";
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmit(e);
                          }
                        }}
                      />
                      {(inputValue.trim() || isLoading) && (
                        <button
                          type="submit"
                          className="absolute right-2 bottom-2 rounded-full bg-(--color-primary) p-2 text-white transition-all hover:bg-(--color-primary-hover) hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-lg cursor-pointer"
                          disabled={isLoading || !inputValue.trim()}
                          aria-label="Submit"
                        >
                          {isLoading ? (
                            <svg
                              className="animate-spin h-5 w-5"
                              xmlns="http://www.w3.org/2000/svg"
                              fill="none"
                              viewBox="0 0 24 24"
                            >
                              <circle
                                className="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                strokeWidth="4"
                              ></circle>
                              <path
                                className="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                              ></path>
                            </svg>
                          ) : (
                            <ArrowUp size={20} strokeWidth={2.5} />
                          )}
                        </button>
                      )}
                    </div>
                  </form>
                </div>
              </>
            </div>
          </div>
        </div>
      )}

      {/* Synthesis Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="mx-4 max-w-2xl rounded-lg border border-(--color-border) bg-(--color-background) p-8 shadow-xl">
            <h2 className="mb-2 text-xl font-semibold text-(--color-text) w-full md:min-w-md">
              Problema a resolver
            </h2>
            {!isSynthesisLoading && (
              <div className="mb-4 flex items-center gap-2 text-sm text-(--color-text-secondary)">
                <Edit3 size={16} className="text-(--color-primary)" />
                <p>Puedes modificar el problema seleccionado antes de continuar</p>
              </div>
            )}
            <div className="mb-6 max-h-96 overflow-y-auto rounded-lg border-2 border-(--color-input-border) bg-(--color-input-bg) p-4 focus-within:border-(--color-primary) transition-colors">
              {isSynthesisLoading ? (
                <div className="flex flex-col items-center justify-center min-h-[200px] space-y-4">
                  <div className="flex items-center space-x-2">
                    <div
                      className="h-3 w-3 animate-bounce rounded-full bg-(--color-primary)"
                      style={{ animationDelay: "0ms" }}
                    ></div>
                    <div
                      className="h-3 w-3 animate-bounce rounded-full bg-(--color-primary)"
                      style={{ animationDelay: "150ms" }}
                    ></div>
                    <div
                      className="h-3 w-3 animate-bounce rounded-full bg-(--color-primary)"
                      style={{ animationDelay: "300ms" }}
                    ></div>
                  </div>
                  <p className="text-sm text-(--color-text-secondary)">
                    Analizando la conversación y sintetizando el problema...
                  </p>
                </div>
              ) : (
                <textarea
                  className="w-full min-h-[200px] bg-transparent text-sm leading-relaxed text-(--color-text) outline-none resize-none"
                  value={editableSynthesis}
                  onChange={(e) => setEditableSynthesis(e.target.value)}
                  placeholder="Edita la síntesis del problema aquí..."
                  autoFocus
                />
              )}
            </div>
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => {
                  setShowModal(false);
                  setIsSynthesisLoading(false);
                }}
                disabled={isSynthesisLoading}
                className="cursor-pointer rounded-md border border-(--color-border) px-6 py-2 text-sm font-medium text-(--color-text) transition-colors hover:bg-(--color-input-bg) disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← Volver al chat
              </button>
              <button
                onClick={handleCreateJobs}
                disabled={isSynthesisLoading || isLoading}
                className="cursor-pointer rounded-md bg-(--color-primary) px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-(--color-primary-hover) flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading && (
                  <svg
                    className="animate-spin h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                )}
                Continuar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Conversation() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-(--color-background)">
        <div className="flex flex-col items-center space-y-4">
          <div className="flex items-center space-x-2">
            <div
              className="h-3 w-3 animate-bounce rounded-full bg-(--color-primary)"
              style={{ animationDelay: "0ms" }}
            ></div>
            <div
              className="h-3 w-3 animate-bounce rounded-full bg-(--color-primary)"
              style={{ animationDelay: "150ms" }}
            ></div>
            <div
              className="h-3 w-3 animate-bounce rounded-full bg-(--color-primary)"
              style={{ animationDelay: "300ms" }}
            ></div>
          </div>
          <p className="text-sm text-(--color-text-secondary)">Cargando conversación...</p>
        </div>
      </div>
    }>
      <ConversationContent />
    </Suspense>
  );
}
