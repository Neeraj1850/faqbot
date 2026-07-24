import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useFaqs, useSections, useFilteredFaqs } from "@/hooks/useFaqApi";
import { FaqAccordion } from "@/components/faq/FaqAccordion";
import { SectionSidebar } from "@/components/faq/SectionSidebar";
import { AppLayout } from "@/components/layout/AppLayout";
import {
  FaqListSkeleton,
  SectionSkeleton,
} from "@/components/ui/skeleton-loaders";
import { ErrorState } from "@/components/ui/error-state";
import { BookOpen } from "lucide-react";
import { useNavigate } from "react-router-dom";
const FaqViewPage = () => {
  const { data: faqs, isLoading, isError, refetch } = useFaqs();
  const sections = useSections(faqs);
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const filteredFaqs = useFilteredFaqs(faqs, "", selectedSection);
  const navigate = useNavigate();

  // Auto-select first section on load
  useEffect(() => {
    if (sections.length > 0 && !selectedSection) {
      setSelectedSection(sections[0].name);
    }
  }, [sections, selectedSection]);

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto pb-32">
        {/* Page Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-primary-foreground" />
            </div>
            <h1 className="text-3xl font-bold text-foreground">
              Frequently Answered Questions
            </h1>
          </div>
          <p className="text-muted-foreground">
            Find answers to commonly asked questions
          </p>
        </motion.div>

        {/* Error State */}
        {isError && (
          <ErrorState
            title="Failed to load FAQs"
            message="We couldn't fetch the knowledge base. Please check your connection and try again."
            onRetry={() => refetch()}
          />
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col md:flex-row gap-8">
            <aside className="w-full md:w-64 shrink-0">
              <div className="sticky top-24">
                <div className="h-4 bg-muted rounded w-20 mb-4" />
                <SectionSkeleton count={5} />
              </div>
            </aside>
            <div className="flex-1">
              <div className="h-6 bg-muted rounded w-32 mb-4" />
              <FaqListSkeleton count={4} />
            </div>
          </div>
        )}

        {/* Content */}
        {!isLoading && !isError && (
          <div className="flex flex-col md:flex-row gap-8">
            {/* Sections Sidebar */}
            <SectionSidebar
              sections={sections}
              selectedSection={selectedSection}
              onSelectSection={setSelectedSection}
            />

            {/* FAQs List */}
            <div className="flex-1 min-w-0">
              <AnimatePresence mode="wait">
                <motion.div
                  key={selectedSection}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-3"
                >
                  {selectedSection && (
                    <h2 className="text-lg font-semibold text-foreground mb-4">
                      {selectedSection}
                    </h2>
                  )}

                  {filteredFaqs.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                      <p>No FAQs found in this section.</p>
                    </div>
                  ) : (
                    filteredFaqs.map((faq, index) => (
                      <FaqAccordion key={faq.id} faq={faq} index={index} />
                    ))
                  )}
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        )}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="fixed bottom-2 inset-x-0 z-20 bg-card/90 backdrop-blur mx-4"
      >
        <div className="relative overflow-hidden rounded-2xl border border-border bg-card shadow-sm p-6 md:p-8">
          {/* subtle gradient top */}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary/60 via-primary to-primary/60" />

          <div className="flex flex-col md:flex-row items-start md:items-center gap-4 md:gap-6">
            <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 text-primary shrink-0">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.8}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16h6m3 2l.543-.906a9 9 0 10-13.086 0L6 18h12z"
                />
              </svg>
            </div>

            <div className="flex-1">
              <h3 className="text-lg font-semibold text-foreground">
                Didn’t find what you're looking for?
              </h3>
              <p className="text-muted-foreground text-sm mt-1">
                Our AI assistant can answer questions and guide you to the right
                information.
              </p>
            </div>

            <button
              onClick={() => navigate("/chat")}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm"
            >
              Start Chat
              <span className="text-xs">→</span>
            </button>
          </div>
        </div>
      </motion.div>
    </AppLayout>
  );
};

export default FaqViewPage;
