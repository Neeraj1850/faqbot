import { motion } from "framer-motion";
import { FAQ } from "@/types/faq";

interface ChatMessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  faqs?: FAQ[];
  index: number;
  onSelectFaq?: (faq: FAQ) => void;
}

export const ChatMessageBubble = ({
  role,
  content,
  faqs,
  index,
  onSelectFaq,
}: ChatMessageBubbleProps) => {
  const isUser = role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      className={`flex mb-4 ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`
          max-w-[85%] md:max-w-[70%] px-4 py-3 rounded-2xl shadow-soft-sm
          ${isUser
            ? "gradient-primary text-primary-foreground rounded-br-md"
            : "bg-secondary/20 text-foreground rounded-bl-md border border-border/40 backdrop-blur-sm"
          }
        `}
      >
        {/* Message text */}
        <p className="text-sm leading-relaxed whitespace-pre-line">
          {content}
        </p>

        {/* FAQ Carousel for assistant */}
        {role === "assistant" && faqs && faqs.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-medium opacity-70 mb-2">
              Related FAQs
            </p>

            <div className="relative">
              {/* Gradient fade hint (right) */}
              <div className="pointer-events-none absolute top-0 right-0 h-full w-8 bg-gradient-to-l from-background to-transparent" />

              {/* Horizontal scroll container */}
              <div className="flex gap-3 overflow-x-auto snap-x snap-mandatory no-scrollbar pb-2 pt-1">
                {faqs.map((faq) => (
                  <motion.div
                    key={faq.id}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => onSelectFaq?.(faq)}
                    className="
                      snap-start min-w-[220px] border border-border/40 
                      rounded-xl bg-background/70 backdrop-blur-sm p-3 cursor-pointer
                      hover:shadow-md transition-all
                    "
                  >
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-secondary/30 text-secondary">
                      {faq.section}
                    </span>

                    <p className="mt-2 text-sm font-medium text-foreground line-clamp-2">
                      {faq.question}
                    </p>

                    <p className="mt-1 text-xs text-muted-foreground line-clamp-3">
                      {faq.answer}
                    </p>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* subtle swipe hint */}
            <p className="text-[10px] text-muted-foreground text-center opacity-60 mt-1">
              Swipe to explore →
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
};
