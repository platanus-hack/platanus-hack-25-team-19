'use client'

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import type { ReactElement } from "react";

type JobType = 'slack' | 'data' | 'research' | 'mail' | 'market_research' | 'external_research';
type JobStatus = 'CREATED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'pending' | 'in_progress' | 'completed' | 'failed';

interface Job {
    id: string;
    job_id?: string;
    session_id: string;
    job_type: JobType;
    type?: JobType;
    status: JobStatus;
    instructions?: string;
    context_summary?: string;
    created_at?: string;
    updated_at?: string;
    result?: string | {
        content: string;
        sources?: Array<{
            title: string;
            url: string;
            description: string;
        }>;
    };
}

export default function Jobs() {
    const router = useRouter();

    const [jobs, setJobs] = useState<Job[]>([]);

    const [sessionId] = useState<string | null>(() => {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('conversation-session-id');
    });

    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        if (!sessionId) return;

        const pollJobs = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/jobs?session_id=${sessionId}`);
                if (response.ok) {
                    const updatedJobs = await response.json();
                    setJobs(updatedJobs);
                    setIsLoading(false);
                    localStorage.setItem('current-jobs', JSON.stringify(updatedJobs));
                }
            } catch (error) {
                console.error('Error polling job status:', error);
                setIsLoading(false);
            }
        };

        pollJobs();

        const interval = setInterval(pollJobs, 5000);

        return () => clearInterval(interval);
    }, [sessionId]);

    const getServiceConfig = (type: JobType) => {
        const configs: Record<JobType, { name: string; description: string; icon: ReactElement; color: string }> = {
            slack: {
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
            data: {
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
            research: {
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
            mail: {
                name: 'Correo Externo',
                description: 'Contactar expertos',
                icon: (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect width="20" height="16" x="2" y="4" rx="2"/>
                        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                    </svg>
                ),
                color: 'from-orange-500/20 to-orange-600/20 border-orange-500/50 text-orange-400'
            },
            market_research: {
                name: 'Market Research',
                description: 'Análisis de mercado',
                icon: (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="m21 21-4.3-4.3"/>
                    </svg>
                ),
                color: 'from-emerald-500/20 to-emerald-600/20 border-emerald-500/50 text-emerald-400'
            },
            external_research: {
                name: 'External Research',
                description: 'Investigación externa',
                icon: (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="m21 21-4.3-4.3"/>
                    </svg>
                ),
                color: 'from-emerald-500/20 to-emerald-600/20 border-emerald-500/50 text-emerald-400'
            }
        };
        return configs[type];
    };

    const getStatusBadge = (status: JobStatus) => {
        const normalizedStatus = status.toLowerCase();
        const badges = {
            created: { text: 'Pendiente', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50' },
            pending: { text: 'Pendiente', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50' },
            in_progress: { text: 'En Progreso', color: 'bg-blue-500/20 text-blue-400 border-blue-500/50' },
            completed: { text: 'Completado', color: 'bg-green-500/20 text-green-400 border-green-500/50' },
            failed: { text: 'Fallido', color: 'bg-red-500/20 text-red-400 border-red-500/50' }
        };
        return badges[normalizedStatus as keyof typeof badges];
    };

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
                    {/* Jobs Grid */}
                    <div className="mb-8">
                        <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-(--color-text-secondary)">
                            Trabajos en Curso
                        </h2>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                            {isLoading ? (
                                // Skeleton loaders
                                <>
                                    {[1, 2, 3, 4].map((i) => (
                                        <div
                                            key={i}
                                            className="group flex flex-col gap-3 rounded-xl border border-(--color-border) bg-(--color-input-bg) p-5 text-left animate-pulse"
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="h-8 w-8 rounded-lg bg-(--color-border)"></div>
                                                <div className="h-5 w-20 rounded bg-(--color-border)"></div>
                                            </div>
                                            <div>
                                                <div className="h-4 w-24 rounded bg-(--color-border)"></div>
                                                <div className="mt-2 h-3 w-32 rounded bg-(--color-border)"></div>
                                            </div>
                                        </div>
                                    ))}
                                </>
                            ) : (
                                jobs.map((job) => {
                                    const jobType = job.job_type || job.type;
                                    const jobId = job.id || job.job_id;
                                    if (!jobType) return null;

                                    const config = getServiceConfig(jobType);
                                    const statusBadge = getStatusBadge(job.status);

                                    if (!config || !statusBadge) return null;

                                    return (
                                        <div
                                            key={jobId}
                                            className="group flex flex-col gap-3 rounded-xl border border-(--color-border) bg-(--color-input-bg) p-5 text-left"
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className={`flex h-8 w-8 items-center justify-center rounded-lg border bg-linear-to-br ${config.color}`}>
                                                    {config.icon}
                                                </div>
                                                <span className={`rounded border px-2 py-0.5 text-xs font-medium ${statusBadge.color}`}>
                                                    {statusBadge.text}
                                                </span>
                                            </div>
                                            <div>
                                                <h3 className="text-sm font-medium text-(--color-text)">{config.name}</h3>
                                                <p className="mt-1 text-xs text-(--color-text-secondary)">{config.description}</p>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>

                    <div>
                        <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-(--color-text-secondary)">
                            Resultados
                        </h2>
                        <div className="space-y-4">
                            {isLoading ? (
                                // Skeleton loader for results
                                <div className="animate-pulse rounded-lg border border-(--color-border) bg-(--color-input-bg) p-4">
                                    <div className="mb-2 h-5 w-32 rounded bg-(--color-border)"></div>
                                    <div className="h-4 w-full rounded bg-(--color-border)"></div>
                                    <div className="mt-2 h-4 w-3/4 rounded bg-(--color-border)"></div>
                                </div>
                            ) : jobs.filter(j => {
                                const isCompleted = j.status.toLowerCase() === 'completed';
                                const hasResult = j.result && (typeof j.result === 'string' ? j.result.trim() !== '' : true);
                                return isCompleted && hasResult;
                            }).length === 0 ? (
                                <div className="rounded-lg border border-(--color-border) bg-(--color-input-bg) p-4 text-sm italic text-(--color-text-secondary)">
                                    Esperando resultados...
                                </div>
                            ) : (
                                jobs.filter(j => {
                                    const isCompleted = j.status.toLowerCase() === 'completed';
                                    const hasResult = j.result && (typeof j.result === 'string' ? j.result.trim() !== '' : true);
                                    return isCompleted && hasResult;
                                }).map((job) => {
                                    const jobType = job.job_type || job.type;
                                    const jobId = job.id || job.job_id;
                                    if (!jobType) return null;

                                    const config = getServiceConfig(jobType);
                                    const resultContent = typeof job.result === 'string' ? job.result : job.result?.content;
                                    const resultSources = typeof job.result === 'object' ? job.result?.sources : undefined;

                                    return (
                                        <div
                                            key={jobId}
                                            className="animate-fade-in rounded-lg border border-(--color-border) bg-(--color-input-bg) p-4"
                                        >
                                            <div className="mb-2 flex items-center gap-2">
                                                <span className="rounded bg-(--color-primary) px-2 py-0.5 text-xs font-medium text-white">
                                                    {config.name}
                                                </span>
                                            </div>
                                            <p className="text-sm text-(--color-text)">{resultContent}</p>

                                            {resultSources && resultSources.length > 0 && (
                                                <div className="mt-4 space-y-3">
                                                    {resultSources.map((source, sourceIndex) => (
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
                                    );
                                })
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
