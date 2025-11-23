'use client'

import { useRouter } from "next/navigation";
import { useState } from "react";
import ReactMarkdown from 'react-markdown';
import ProcessStepper from "@/components/ProcessStepper";
import { useProcessStep } from "@/hooks/useProcessStep";

export default function Summary() {
    const router = useRouter();
    const currentStep = useProcessStep();
    const [summaryText] = useState(() => {
        // Only access localStorage on client side
        if (typeof window === 'undefined') return '';

        const storedSummary = localStorage.getItem('summary-text');

        if (storedSummary) {
            return storedSummary;
        }

        return '';
    });

    const handleExportMarkdown = () => {
        const blob = new Blob([summaryText], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `resumen-investigacion-${new Date().toISOString().split('T')[0]}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="flex min-h-screen flex-col bg-(--color-background)">
            {/* Process Stepper */}
            <div className="w-full max-w-5xl mx-auto pt-6 px-6">
                <ProcessStepper currentStep={currentStep} />
            </div>

            {/* Header */}
            <header className="border-b border-(--color-border) bg-(--color-background) px-6 py-4 mt-6">
                <div className="mx-auto max-w-4xl grid grid-cols-3 items-center">
                    <button
                        onClick={() => router.push('/jobs')}
                        className="cursor-pointer text-sm text-(--color-text-secondary) transition-colors hover:text-(--color-text) justify-self-start"
                    >
                        ← Volver
                    </button>
                    <h1 className="text-lg font-semibold text-(--color-text) justify-self-center">Resumen Ejecutivo</h1>
                    <div />
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto px-6 py-8">
                <div className="mx-auto max-w-4xl">
                    <div className="rounded-lg border border-(--color-border) bg-(--color-input-bg) p-8">
                        {/* Title */}
                        <div className="mb-6 border-b border-(--color-border) pb-6">
                            <h2 className="text-2xl font-bold text-(--color-text) mb-2">
                                Resumen del Plan de Investigación
                            </h2>
                            <p className="text-sm text-(--color-text-secondary)">
                                Análisis completo basado en múltiples fuentes de investigación
                            </p>
                        </div>

                        {/* Body - Markdown Content */}
                        <div className="prose prose-invert prose-sm max-w-none prose-headings:text-(--color-text) prose-h1:text-3xl prose-h1:font-bold prose-h1:mb-4 prose-h2:text-2xl prose-h2:font-semibold prose-h2:mt-8 prose-h2:mb-4 prose-h3:text-xl prose-h3:font-semibold prose-h3:mt-6 prose-h3:mb-3 prose-p:text-(--color-text) prose-p:leading-relaxed prose-p:mb-4 prose-strong:text-(--color-text) prose-strong:font-semibold prose-ul:text-(--color-text) prose-ul:my-4 prose-li:text-(--color-text) prose-li:my-2">
                            <ReactMarkdown>
                                {summaryText}
                            </ReactMarkdown>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer with Export Button */}
            <div className="mx-auto max-w-6xl mb-12 flex justify-end">
                <button
                    onClick={handleExportMarkdown}
                    className="cursor-pointer rounded-md bg-(--color-primary) px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-(--color-primary-hover)"
                >
                    Exportar Markdown
                </button>
            </div>
        </div>
    );
}
