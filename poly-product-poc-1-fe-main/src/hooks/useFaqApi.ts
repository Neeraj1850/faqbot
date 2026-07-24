import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { faqApi, chatApi, ingestApi } from '@/services/faqApi';
import { FAQ, Section } from '@/types/faq';
import { toast } from 'sonner';
import { useState, useMemo, useCallback } from 'react';

// Query keys
export const faqKeys = {
  all: ['faqs'] as const,
  list: () => [...faqKeys.all, 'list'] as const,
};

// Hook for fetching FAQs
export const useFaqs = () => {
  return useQuery({
    queryKey: faqKeys.list(),
    queryFn: faqApi.getAll,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};

// Hook for creating FAQ
export const useCreateFaq = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: faqApi.create,
    onMutate: async (newFaq) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: faqKeys.list() });

      // Snapshot previous value
      const previousFaqs = queryClient.getQueryData<FAQ[]>(faqKeys.list());

      // Optimistically update
      if (previousFaqs) {
        const optimisticFaq: FAQ = {
          id: `temp-${Date.now()}`,
          ...newFaq,
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        queryClient.setQueryData<FAQ[]>(faqKeys.list(), [optimisticFaq, ...previousFaqs]);
      }

      return { previousFaqs };
    },
    onError: (err, newFaq, context) => {
      // Rollback on error
      if (context?.previousFaqs) {
        queryClient.setQueryData(faqKeys.list(), context.previousFaqs);
      }
    },
    onSuccess: () => {
      toast.success('FAQ created successfully');
    },
    onSettled: () => {
      // Refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: faqKeys.list() });
    },
  });
};

// Hook for updating FAQ
export const useUpdateFaq = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Omit<FAQ, 'id' | 'createdAt'>> }) =>
      faqApi.update(id, data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: faqKeys.list() });

      const previousFaqs = queryClient.getQueryData<FAQ[]>(faqKeys.list());

      if (previousFaqs) {
        queryClient.setQueryData<FAQ[]>(
          faqKeys.list(),
          previousFaqs.map((faq) =>
            faq.id === id ? { ...faq, ...data, updatedAt: new Date() } : faq
          )
        );
      }

      return { previousFaqs };
    },
    onError: (err, variables, context) => {
      if (context?.previousFaqs) {
        queryClient.setQueryData(faqKeys.list(), context.previousFaqs);
      }
    },
    onSuccess: () => {
      toast.success('FAQ updated successfully');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: faqKeys.list() });
    },
  });
};

// Hook for deleting FAQ
export const useDeleteFaq = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: faqApi.delete,
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: faqKeys.list() });

      const previousFaqs = queryClient.getQueryData<FAQ[]>(faqKeys.list());

      if (previousFaqs) {
        queryClient.setQueryData<FAQ[]>(
          faqKeys.list(),
          previousFaqs.filter((faq) => faq.id !== id)
        );
      }

      return { previousFaqs };
    },
    onError: (err, id, context) => {
      if (context?.previousFaqs) {
        queryClient.setQueryData(faqKeys.list(), context.previousFaqs);
      }
    },
    onSuccess: () => {
      toast.success('FAQ deleted');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: faqKeys.list() });
    },
  });
};

// Hook for chat query
export const useChatQuery = () => {
  return useMutation({
    mutationFn: chatApi.query,
  });
};

// Hook for PDF ingestion
export const useIngestPdf = () => {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState(0);

  const mutation = useMutation({
    mutationFn: (file: File) => ingestApi.uploadPdf(file, setProgress),
    onSuccess: (data) => {
      toast.success('PDF ingested successfully', {
        description: `${data.faqs_created || 0} FAQs created`,
      });
      queryClient.invalidateQueries({ queryKey: faqKeys.list() });
      setProgress(0);
    },
    onError: () => {
      setProgress(0);
    },
  });

  return { ...mutation, progress };
};

// Helper hook for sections derived from FAQs
export const useSections = (faqs: FAQ[] | undefined): Section[] => {
  return useMemo(() => {
    if (!faqs) return [];
    
    const sectionMap = new Map<string, number>();
    faqs.forEach((faq) => {
      const count = sectionMap.get(faq.section) || 0;
      sectionMap.set(faq.section, count + 1);
    });

    return Array.from(sectionMap.entries()).map(([name, faqCount], index) => ({
      id: `section-${index}`,
      name,
      faqCount,
    }));
  }, [faqs]);
};

// Hook for filtered FAQs (used in management)
export const useFilteredFaqs = (
  faqs: FAQ[] | undefined,
  searchQuery: string,
  selectedSection: string | null
): FAQ[] => {
  return useMemo(() => {
    if (!faqs) return [];

    let result = faqs;

    if (selectedSection) {
      result = result.filter((faq) => faq.section === selectedSection);
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (faq) =>
          faq.question.toLowerCase().includes(query) ||
          faq.answer.toLowerCase().includes(query) ||
          faq.section.toLowerCase().includes(query)
      );
    }

    return result;
  }, [faqs, searchQuery, selectedSection]);
};

// Hook for local search (used in chat when API fails)
export const useLocalSearch = (faqs: FAQ[] | undefined) => {
  return useCallback(
    (query: string): FAQ[] => {
      if (!faqs || !query.trim()) return [];

      const lowerQuery = query.toLowerCase();
      const words = lowerQuery.split(/\s+/).filter(Boolean);

      return faqs
        .map((faq) => {
          let score = 0;
          const questionLower = faq.question.toLowerCase();
          const answerLower = faq.answer.toLowerCase();

          words.forEach((word) => {
            if (questionLower.includes(word)) score += 3;
            if (answerLower.includes(word)) score += 1;
          });

          return { faq, score };
        })
        .filter((item) => item.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, 5)
        .map((item) => item.faq);
    },
    [faqs]
  );
};
