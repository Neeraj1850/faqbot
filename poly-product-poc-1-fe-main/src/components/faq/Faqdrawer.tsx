import { FAQ } from "@/types/faq";
import { motion, AnimatePresence } from "framer-motion";

interface FaqDrawerProps {
  faq?: FAQ | null;
  open: boolean;
  onClose: () => void;
}

export const FaqDrawer = ({ faq, open, onClose }: FaqDrawerProps) => {
  return (
    <AnimatePresence>
      {open && faq && (
        <>
          {/* Overlay */}
          <motion.div
            onClick={onClose}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          {/* Drawer */}
          <motion.div
            className="fixed top-0 right-0 w-full sm:w-[440px] h-full bg-background border-l border-border z-50 shadow-xl p-6 flex flex-col"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 240, damping: 28 }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold">{faq.section}</h2>
              <button
                onClick={onClose}
                className="text-muted-foreground hover:text-foreground transition"
              >
                ✕
              </button>
            </div>

            <h3 className="text-md font-medium mb-2">{faq.question}</h3>
            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
              {faq.answer}
            </p>

            <div className="mt-auto pt-6 text-xs text-muted-foreground opacity-70">
              Powered by Semantic FAQ Search
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
