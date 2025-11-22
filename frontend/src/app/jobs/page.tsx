'use client'

import { useRouter } from "next/navigation";
import { useState } from "react";

type JobType = 'slack' | 'data' | 'research' | 'mail';

interface JobResult {
    type: JobType;
    content: string;
    sources?: Array<{
        title: string;
        url: string;
        description: string;
    }>;
}

export default function Jobs() {
    const router = useRouter();
    const [results, setResults] = useState<JobResult[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const mockJobResponses: Record<JobType, JobResult> = {
        slack: {
            type: 'slack',
            content: 'Le mandé un mensaje a Juan, él dice que no sabe nada del proyecto pero se ve interesante'
        },
        data: {
            type: 'data',
            content: 'Según los registros de la compañía hace 3 años se intentó X y resultó en Y'
        },
        research: {
            type: 'research',
            content: 'He encontrado información relevante en las siguientes fuentes:',
            sources: [
                {
                    title: 'MIT Technology Review - AI Research 2024',
                    url: 'https://example.com/source1',
                    description: 'Estudio sobre implementación de IA en empresas medianas muestra un incremento del 45% en productividad.'
                },
                {
                    title: 'Nature Journal - Machine Learning Applications',
                    url: 'https://example.com/source2',
                    description: 'Análisis de casos de uso en diferentes industrias revela patrones de adopción similares.'
                },
                {
                    title: 'Harvard Business Review - Digital Transformation',
                    url: 'https://example.com/source3',
                    description: 'Las empresas que implementan gradualmente nuevas tecnologías tienen 3x más éxito.'
                },
                {
                    title: 'Stanford Research Paper - AI Integration',
                    url: 'https://example.com/source4',
                    description: 'Metodología recomendada para proyectos piloto en organizaciones tradicionales.'
                }
            ]
        },
        mail: {
            type: 'mail',
            content: 'Le mandé un mensaje a Pedro con: "Estoy investigando sobre Y", espero su respuesta'
        }
    };

    const triggerService = async (serviceType: JobType) => {
        setIsLoading(true);

        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 1000));

        // TODO: Replace with actual API call
        // const response = await fetch('/api/jobs', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({ type: serviceType })
        // });
        // const data = await response.json();

        const result = mockJobResponses[serviceType];
        setResults(prev => [...prev, result]);
        setIsLoading(false);
    };

    const services = [
        {
            id: 'slack' as JobType,
            name: 'Slack',
            description: 'Consultar equipo',
            icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14.5 10c-.83 0-1.5-.67-1.5-1.5v-5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5v5c0 .83-.67 1.5-1.5 1.5z"/>
                    <path d="M20.5 10H19V8.5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
                    <path d="M9.5 14c.83 0 1.5.67 1.5 1.5v5c0 .83-.67 1.5-1.5 1.5S8 21.33 8 20.5v-5c0-.83.67-1.5 1.5-1.5z"/>
                    <path d="M3.5 14H5v1.5c0 .83-.67 1.5-1.5 1.5S2 16.33 2 15.5 2.67 14 3.5 14z"/>
                    <path d="M14 14.5c0-.83.67-1.5 1.5-1.5h5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5h-5c-.83 0-1.5-.67-1.5-1.5z"/>
                    <path d="M15.5 19H14v1.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5-.67-1.5-1.5-1.5z"/>
                    <path d="M10 9.5C10 8.67 9.33 8 8.5 8h-5C2.67 8 2 8.67 2 9.5S2.67 11 3.5 11h5c.83 0 1.5-.67 1.5-1.5z"/>
                    <path d="M8.5 5H10V3.5C10 2.67 9.33 2 8.5 2S7 2.67 7 3.5 7.67 5 8.5 5z"/>
                </svg>
            ),
            color: 'from-pink-500/20 to-purple-500/20 border-pink-500/50 text-pink-400'
        },
        {
            id: 'data' as JobType,
            name: 'Datos Internos',
            description: 'Historial & Logs',
            icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2c-4 0-8 .5-8 4v12c0 3.5 4 4 8 4s8-.5 8-4V6c0-3.5-4-4-8-4z"/>
                    <path d="M20 12c0 3.5-4 4-8 4s-8-.5-8-4"/>
                    <path d="M20 6c0 3.5-4 4-8 4s-8-.5-8-4"/>
                </svg>
            ),
            color: 'from-blue-500/20 to-blue-600/20 border-blue-500/50 text-blue-400'
        },
        {
            id: 'research' as JobType,
            name: 'Deep Research',
            description: 'Web & Papers',
            icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="m21 21-4.3-4.3"/>
                </svg>
            ),
            color: 'from-emerald-500/20 to-emerald-600/20 border-emerald-500/50 text-emerald-400'
        },
        {
            id: 'mail' as JobType,
            name: 'Correo Externo',
            description: 'Contactar expertos',
            icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect width="20" height="16" x="2" y="4" rx="2"/>
                    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                </svg>
            ),
            color: 'from-orange-500/20 to-orange-600/20 border-orange-500/50 text-orange-400'
        }
    ];

    return (
        <div className="flex min-h-screen flex-col bg-(--color-background)">
            {/* Header */}
            <header className="border-b border-(--color-border) bg-(--color-background) px-6 py-4">
                <div className="mx-auto flex max-w-6xl items-center justify-between">
                    <button
                        onClick={() => router.push('/conversation')}
                        className="cursor-pointer text-sm text-(--color-text-secondary) transition-colors hover:text-(--color-text)"
                    >
                        ← Volver a conversación
                    </button>
                    <h1 className="text-lg font-semibold text-(--color-text)">Servicios de Investigación</h1>
                    <div className="w-40"></div>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto px-6 py-8">
                <div className="mx-auto max-w-6xl">
                    {/* Services Grid */}
                    <div className="mb-8">
                        <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-(--color-text-secondary)">
                            Servicios Disponibles
                        </h2>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                            {services.map((service) => (
                                <button
                                    key={service.id}
                                    onClick={() => triggerService(service.id)}
                                    disabled={isLoading}
                                    className="group cursor-pointer flex flex-col gap-3 rounded-xl border border-(--color-border) bg-(--color-input-bg) p-5 text-left transition-all hover:border-(--color-text-secondary) hover:bg-(--color-background) disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg border bg-linear-to-br ${service.color}`}>
                                        {service.icon}
                                    </div>
                                    <div>
                                        <h3 className="text-sm font-medium text-(--color-text)">{service.name}</h3>
                                        <p className="mt-1 text-xs text-(--color-text-secondary)">{service.description}</p>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Results Area */}
                    <div>
                        <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-(--color-text-secondary)">
                            Resultados
                        </h2>
                        <div className="space-y-4">
                            {results.length === 0 && !isLoading && (
                                <div className="rounded-lg border border-(--color-border) bg-(--color-input-bg) p-4 text-sm italic text-(--color-text-secondary)">
                                    Esperando acción...
                                </div>
                            )}

                            {isLoading && (
                                <div className="rounded-lg border border-(--color-border) bg-(--color-input-bg) p-4">
                                    <div className="flex items-center space-x-2">
                                        <div className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)" style={{ animationDelay: '0ms' }}></div>
                                        <div className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)" style={{ animationDelay: '150ms' }}></div>
                                        <div className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)" style={{ animationDelay: '300ms' }}></div>
                                        <span className="ml-2 text-sm text-(--color-text-secondary)">Procesando...</span>
                                    </div>
                                </div>
                            )}

                            {results.map((result, index) => (
                                <div
                                    key={index}
                                    className="animate-fade-in rounded-lg border border-(--color-border) bg-(--color-input-bg) p-4"
                                >
                                    <div className="mb-2 flex items-center gap-2">
                                        <span className="rounded bg-(--color-primary) px-2 py-0.5 text-xs font-medium text-white">
                                            {services.find(s => s.id === result.type)?.name}
                                        </span>
                                    </div>
                                    <p className="text-sm text-(--color-text)">{result.content}</p>

                                    {result.sources && result.sources.length > 0 && (
                                        <div className="mt-4 space-y-3">
                                            {result.sources.map((source, sourceIndex) => (
                                                <div
                                                    key={sourceIndex}
                                                    className="rounded-lg border border-(--color-border) bg-(--color-background) p-3"
                                                >
                                                    <h4 className="mb-1 text-sm font-medium text-(--color-text)">
                                                        {sourceIndex + 1}. {source.title}
                                                    </h4>
                                                    <p className="mb-2 text-xs text-(--color-text-secondary)">
                                                        {source.description}
                                                    </p>
                                                    <a
                                                        href={source.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-xs text-(--color-primary) hover:underline"
                                                    >
                                                        {source.url}
                                                    </a>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
