"use client";

import { CheckCircle, Search, Lightbulb, Target } from "lucide-react";

interface Step {
  id: number;
  title: string;
  icon: React.ReactNode;
}

interface ProcessStepperProps {
  currentStep?: number;
  className?: string;
}

export default function ProcessStepper({
  currentStep = 0,
  className = ""
}: ProcessStepperProps) {
  const steps: Step[] = [
    {
      id: 1,
      title: "Identificación",
      icon: <Target size={16} />,
    },
    {
      id: 2,
      title: "Análisis",
      icon: <Search size={16} />,
    },
    {
      id: 3,
      title: "Accionables",
      icon: <Lightbulb size={16} />,
    },
  ];

  const getStepStatus = (stepIndex: number) => {
    if (stepIndex < currentStep) return "completed";
    if (stepIndex === currentStep) return "current";
    return "upcoming";
  };

  const getStepStyles = (status: string) => {
    switch (status) {
      case "completed":
        return {
          circle: "bg-emerald-500 text-white border-emerald-500",
          connector: "bg-emerald-500",
          title: "text-(--color-text) font-medium",
        };
      case "current":
        return {
          circle: "bg-emerald-500 text-white border-emerald-500 ring-2 ring-emerald-200",
          connector: "bg-(--color-border)",
          title: "text-emerald-600 font-semibold",
        };
      default:
        return {
          circle: "bg-(--color-background) text-(--color-text-secondary) border-(--color-border)",
          connector: "bg-(--color-border)",
          title: "text-(--color-text-secondary)",
        };
    }
  };

  return (
    <div className={`w-full max-w-4xl mx-auto ${className}`}>
      <div className="relative">
        {/* Progress line */}
        <div className="absolute top-6 left-6 right-6 h-0.5 bg-(--color-border)">
          <div
            className="h-full bg-emerald-500 transition-all duration-700 ease-out"
            style={{
              width: `${currentStep > 0 ? ((currentStep) / (steps.length - 1)) * 100 : 0}%`
            }}
          />
        </div>

        {/* Steps */}
        <div className="relative flex justify-between">
          {steps.map((step, index) => {
            const status = getStepStatus(index);
            const styles = getStepStyles(status);

            return (
              <div key={step.id} className="flex flex-col items-center group">
                {/* Step circle */}
                <div
                  className={`
                    relative z-10 flex h-12 w-12 items-center justify-center rounded-full border-2
                    transition-all duration-300 ${styles.circle}
                  `}
                >
                  {status === "completed" ? (
                    <CheckCircle size={18} className="text-white" />
                  ) : (
                    <div className="flex items-center justify-center text-white">
                      {step.icon}
                    </div>
                  )}
                </div>

                {/* Step content */}
                <div className="mt-3 max-w-28 text-center">
                  <h3 className={`text-xs transition-colors duration-200 ${styles.title}`}>
                    {step.title}
                  </h3>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
