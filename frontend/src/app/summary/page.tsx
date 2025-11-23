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
        // Initialize state from localStorage or use mock data
        if (typeof window === 'undefined') return '';

        const storedSummary = localStorage.getItem('summary-text');

        if (storedSummary) {
            return storedSummary;
        }

        // Mock data if no summary exists
        const mockSummary = `# Resumen Ejecutivo del Plan de Investigación

## Problema Identificado

El problema de fondo pareciera ser: Investigación de $10MM USD en viáticos no justificados de alta gerencia en los últimos 3 meses, con acceso a información deliberadamente restringido por posibles involucrados.

## Estrategia de Investigación

Para abordar este problema crítico, se ha diseñado un plan de investigación multi-canal que combina diferentes fuentes de información y metodologías:

### 1. Deep Research - Benchmarking y Contexto Externo

**Objetivo:** Establecer un marco de referencia comparativo para determinar si los montos observados son anómalos y conocer mejores prácticas de investigación.

**Consultas Realizadas:**
- Corporate executive travel expense fraud cases Latin America 2023-2024 investigation methodologies
- Benchmark executive travel expenses senior management Fortune 500 companies monthly average
- Internal audit best practices restricted information financial investigation whistleblower protocols

**Puntos de Datos Esperados:**
- Promedio de viáticos mensuales para alta gerencia en empresas similares (industria, tamaño, región) para establecer baseline comparativo
- Porcentaje de casos de fraude de viáticos ejecutivos detectados anualmente en corporaciones latinoamericanas y montos promedio involucrados
- Tiempo promedio de resolución de investigaciones de fraude financiero interno cuando hay obstrucción deliberada de información (30-90-180 días)

### 2. Datos Internos - Análisis Histórico

**Objetivo:** Extraer y analizar registros históricos de viáticos, patrones de gasto y comportamiento de aprobaciones.

**Acciones Ejecutadas:**
- Consulta de logs de sistemas financieros de los últimos 12 meses
- Análisis de patrones de aprobación y autorización de gastos
- Identificación de anomalías en frecuencia y montos de viáticos
- Mapeo de rutas de aprobación y responsables

### 3. Slack - Consulta Interna al Equipo

**Objetivo:** Recopilar información contextual de equipos relacionados y validar sospechas.

**Consultas Realizadas:**
- Comunicación con equipo de auditoría interna
- Consulta a finanzas sobre procesos de aprobación
- Verificación con equipos de IT sobre accesos y modificaciones de registros

### 4. Correo Externo - Expertos y Consultores

**Objetivo:** Obtener asesoría especializada en investigación de fraude corporativo.

**Acciones:**
- Consulta con firma de auditoría forense
- Contacto con expertos en compliance financiero
- Solicitud de mejores prácticas a consultores especializados

## Hallazgos Preliminares

1. **Magnitud del Problema:** $10MM USD representa un monto significativamente superior al promedio de la industria para viáticos ejecutivos trimestrales.

2. **Patrón de Obstrucción:** La restricción deliberada de acceso a información sugiere posible conocimiento y participación de múltiples niveles jerárquicos.

3. **Urgencia:** La ventana de investigación es crítica antes de que se comprometa más evidencia.

## Próximos Pasos Recomendados

1. **Inmediato (24-48 horas):**
   - Preservar evidencia digital disponible
   - Solicitar intervención legal preventiva
   - Implementar monitoreo de actividades relacionadas

2. **Corto Plazo (1-2 semanas):**
   - Ejecutar auditoría forense completa
   - Entrevistar personal clave
   - Documentar cadena de custodia de evidencia

3. **Mediano Plazo (1 mes):**
   - Completar investigación interna
   - Preparar reporte para directorio
   - Implementar controles preventivos

## Recursos Necesarios

- Equipo de auditoría forense externa
- Asesoría legal especializada
- Herramientas de análisis de datos financieros
- Soporte de IT para recuperación y análisis de logs

## Riesgos Identificados

- **Pérdida de Evidencia:** Riesgo alto de destrucción deliberada de documentación
- **Implicaciones Legales:** Posible responsabilidad corporativa y personal
- **Reputacional:** Impacto en imagen corporativa si se hace público
- **Financiero:** Además de los $10MM, posibles costos de investigación y remediación

---

*Este resumen ha sido generado automáticamente basado en el análisis de múltiples fuentes de investigación y debe ser tratado como información confidencial.*`;

        localStorage.setItem('summary-text', mockSummary);
        return mockSummary;
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
                <div className="mx-auto flex max-w-4xl items-center justify-between">
                    <button
                        onClick={() => router.push('/jobs')}
                        className="cursor-pointer text-sm text-(--color-text-secondary) transition-colors hover:text-(--color-text)"
                    >
                        ← Volver a trabajos
                    </button>
                    <h1 className="text-lg font-semibold text-(--color-text)">Resumen Ejecutivo</h1>
                    <div className="w-40"></div>
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
                        <div className="prose prose-sm max-w-none text-(--color-text) prose-strong:font-semibold">
                            <ReactMarkdown>
                                {summaryText}
                            </ReactMarkdown>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer with Export Button */}
            <div className="border-t border-(--color-border) bg-(--color-background) px-6 py-6">
                <div className="mx-auto max-w-4xl flex justify-end">
                    <button
                        onClick={handleExportMarkdown}
                        className="cursor-pointer rounded-md bg-(--color-primary) px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-(--color-primary-hover)"
                    >
                        Exportar como .md
                    </button>
                </div>
            </div>
        </div>
    );
}
