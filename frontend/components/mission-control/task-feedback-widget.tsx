"use client";

import { useState } from "react";
import { Star, X } from "lucide-react";

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
  const [rating, setRating] = useState<number>(0);
  const [hoveredRating, setHoveredRating] = useState<number>(0);
  const [feedback, setFeedback] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) return;

    setIsSubmitting(true);
    try {
      await onSubmit(rating, feedback);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStarClick = (star: number) => {
    setRating(star);
  };

  const displayRating = hoveredRating || rating;

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
      <div className="flex items-center gap-2 mb-3">
        <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
        <span className="text-sm font-semibold text-[var(--mc-text-primary)]">
          Rate this response
        </span>
      </div>

      {/* Star Rating */}
      <div className="flex gap-1 mb-3">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => handleStarClick(star)}
            onMouseEnter={() => setHoveredRating(star)}
            onMouseLeave={() => setHoveredRating(0)}
            className="transition-transform hover:scale-110"
            aria-label={`Rate ${star} stars`}
          >
            <Star
              className={`h-6 w-6 transition-colors ${
                star <= displayRating
                  ? "text-yellow-500 fill-yellow-500"
                  : "text-gray-600"
              }`}
            />
          </button>
        ))}
        {rating > 0 && (
          <span className="ml-2 text-sm text-gray-400">
            {rating} star{rating !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Optional Feedback */}
      <textarea
        placeholder="Optional: What could be improved? (Press Enter to submit)"
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (rating > 0) {
              handleSubmit();
            }
          }
        }}
        className="w-full p-2 text-sm bg-black/30 border border-gray-700 rounded text-[var(--mc-text-primary)] placeholder:text-gray-500 focus:outline-none focus:border-blue-500"
        rows={2}
      />

      {/* Buttons */}
      <div className="flex gap-2 mt-3">
        <button
          onClick={handleSubmit}
          disabled={rating === 0 || isSubmitting}
          className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
            rating === 0
              ? "bg-gray-700 text-gray-500 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 text-white"
          }`}
        >
          {isSubmitting ? "Submitting..." : "Submit"}
        </button>
        <button
          onClick={onDismiss}
          className="px-4 py-2 text-gray-400 hover:text-gray-300 text-sm transition-colors"
        >
          Skip
        </button>
      </div>

      {/* Helper text */}
      <p className="text-xs text-gray-500 mt-2">
        💡 Your feedback helps improve agent performance
      </p>
    </div>
  );
}
