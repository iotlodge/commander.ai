"use client";

import { useState } from "react";
import { Star, X, MessageSquarePlus } from "lucide-react";

interface TaskFeedbackWidgetProps {
  taskId: string;
  onSubmit: (rating: number, feedback: string) => Promise<void>;
  onDismiss: () => void;
}

export function TaskFeedbackWidget({
  taskId,
  onSubmit,
  onDismiss,
}: TaskFeedbackWidgetProps) {
  const [hoveredRating, setHoveredRating] = useState<number>(0);
  const [feedback, setFeedback] = useState("");
  const [showFeedbackInput, setShowFeedbackInput] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleStarClick = async (star: number) => {
    // If no feedback text, submit immediately on star click
    if (!feedback.trim()) {
      setIsSubmitting(true);
      try {
        await onSubmit(star, "");
      } finally {
        setIsSubmitting(false);
      }
    } else {
      // If there's feedback text, submit both
      setIsSubmitting(true);
      try {
        await onSubmit(star, feedback);
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  return (
    <div className="relative p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg mb-4">
      {/* Close button */}
      <button
        onClick={onDismiss}
        className="absolute top-2 right-2 text-gray-400 hover:text-gray-300"
        aria-label="Dismiss feedback"
      >
        <X className="h-4 w-4" />
      </button>

      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
          <span className="text-sm font-semibold text-[var(--mc-text-primary)]">
            Rate this response
          </span>
        </div>
        {!showFeedbackInput && (
          <button
            onClick={() => setShowFeedbackInput(true)}
            className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            <MessageSquarePlus className="h-3 w-3" />
            Add feedback
          </button>
        )}
      </div>

      {/* Star Rating - Click to submit! */}
      <div className="flex items-center gap-1 mb-2">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => handleStarClick(star)}
            onMouseEnter={() => setHoveredRating(star)}
            onMouseLeave={() => setHoveredRating(0)}
            disabled={isSubmitting}
            className="transition-transform hover:scale-110 disabled:opacity-50"
            aria-label={`Rate ${star} stars`}
          >
            <Star
              className={`h-6 w-6 transition-colors ${
                star <= hoveredRating
                  ? "text-yellow-500 fill-yellow-500"
                  : "text-gray-600"
              }`}
            />
          </button>
        ))}
        {isSubmitting && (
          <span className="ml-2 text-xs text-gray-400">Submitting...</span>
        )}
      </div>

      {/* Optional Feedback Text Area (collapsed by default) */}
      {showFeedbackInput && (
        <div className="mt-3 animate-in slide-in-from-top-2 duration-200">
          <textarea
            placeholder="What could be improved? (Click a star to submit)"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            className="w-full p-2 text-sm bg-black/30 border border-gray-700 rounded text-[var(--mc-text-primary)] placeholder:text-gray-500 focus:outline-none focus:border-blue-500"
            rows={2}
            autoFocus
          />
        </div>
      )}

      {/* Helper text */}
      <p className="text-xs text-gray-500 mt-2">
        💡 Click any star to submit • Feedback helps improve agent performance
      </p>
    </div>
  );
}
