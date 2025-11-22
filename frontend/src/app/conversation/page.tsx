'use client'

import { useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export default function Conversation() {
    const router = useRouter();
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const hasInitialized = useRef(false);

    // Load messages from localStorage on mount and check for initial message
    useEffect(() => {
        if (hasInitialized.current) return;
        hasInitialized.current = true;

        const savedMessages = localStorage.getItem('conversation-messages');

        if (savedMessages) {
            try {
                const parsed = JSON.parse(savedMessages);
                handleSendMessage(parsed[0].content);
                setMessages(parsed);
            } catch (error) {
                console.error('Error loading messages:', error);
            }
        }
    }, []);

    // Save messages to localStorage whenever they change
    useEffect(() => {
        if (messages.length > 0) {
            localStorage.setItem('conversation-messages', JSON.stringify(messages));
        }
    }, [messages]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = async (message: string) => {
        if (!message.trim()) return;

        const userMessage: Message = { role: 'user', content: message };
        setMessages(prev => [...prev, userMessage]);
        setInputValue("");
        setIsLoading(true);

        try {
            // TODO: Replace with actual API call to /test endpoint
            const response = await fetch('/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            const data = await response.json();
            const assistantMessage: Message = {
                role: 'assistant',
                content: data.response || 'This is a placeholder response. Connect the /test endpoint to see real responses.'
            };
            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Error sending message:', error);
            // Placeholder response for now
            const assistantMessage: Message = {
                role: 'assistant',
                content: 'This is a placeholder response. Connect the /test endpoint to see real responses.'
            };
            setMessages(prev => [...prev, assistantMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        handleSendMessage(inputValue);
    };

    const clearConversation = () => {
        setMessages([]);
        localStorage.removeItem('conversation-messages');
    };

    return (
        <div className="flex min-h-screen flex-col bg-(--color-background)">
            {/* Header */}
            <header className="border-b border-(--color-border) bg-(--color-background) px-6 py-4">
                <div className="mx-auto flex max-w-4xl items-center justify-between">
                    <button
                        onClick={() => router.push('/')}
                        className="cursor-pointer text-sm text-(--color-text-secondary) transition-colors hover:text-(--color-text)"
                    >
                        ← Back
                    </button>
                    <h1 className="text-lg font-semibold text-(--color-text)">AI Conversation</h1>
                    <button
                        onClick={clearConversation}
                        className="cursor-pointer text-sm text-(--color-text-secondary) transition-colors hover:text-red-500"
                        title="Clear conversation"
                    >
                        Limpiar
                    </button>
                </div>
            </header>

            {/* Messages Container */}
            <div className="flex-1 overflow-y-auto px-4 py-8">
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
                            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                                    message.role === 'user'
                                        ? 'bg-(--color-primary) text-white'
                                        : 'border border-(--color-border) bg-(--color-input-bg) text-(--color-text)'
                                }`}
                            >
                                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                                    {message.content}
                                </p>
                            </div>
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="max-w-[80%] rounded-lg border border-(--color-border) bg-(--color-input-bg) px-4 py-3">
                                <div className="flex items-center space-x-2">
                                    <div className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)" style={{ animationDelay: '0ms' }}></div>
                                    <div className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)" style={{ animationDelay: '150ms' }}></div>
                                    <div className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)" style={{ animationDelay: '300ms' }}></div>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            <button
                type="button"
                className="w-64 mb-8 mx-auto rounded-md bg-(--color-primary) px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-(--color-primary-hover) disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                onClick={() => router.push('/jobs')}
            >
                Encontré el problema
            </button>

            {/* Input Container */}
            <div className="border-t border-(--color-border) bg-(--color-background) px-4 py-6">
                <div className="mx-auto max-w-3xl">
                    <form onSubmit={handleSubmit}>
                        <div className="relative flex items-center rounded-lg border border-(--color-input-border) bg-(--color-input-bg)">
                            <input
                                type="text"
                                placeholder="Type your message..."
                                className="w-full bg-transparent px-5 py-4 text-base text-(--color-text) outline-none placeholder:text-(--color-text-secondary)"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                disabled={isLoading}
                            />
                            <button
                                type="submit"
                                className="absolute right-2 rounded-md bg-(--color-primary) px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-(--color-primary-hover) disabled:opacity-50 disabled:cursor-not-allowed"
                                disabled={isLoading || !inputValue.trim()}
                            >
                                Send
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
