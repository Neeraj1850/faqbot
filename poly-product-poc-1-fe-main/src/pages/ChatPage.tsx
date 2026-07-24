import { useState, useRef, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, Sparkles, Loader2 } from "lucide-react";
import { useFaqs, useChatQuery, useLocalSearch, useConversationMessages, conversationKeys } from "@/hooks/useFaqApi";
import { AppLayout } from "@/components/layout/AppLayout";
import { ChatMessageBubble } from "@/components/chat/ChatMessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { ChatMessage, FAQ } from "@/types/faq";
import { FaqDrawer } from "@/components/faq/Faqdrawer";
const ChatPage = () => {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: faqs } = useFaqs();
  const chatMutation = useChatQuery();
  const localSearch = useLocalSearch(faqs);
  const historyQuery = useConversationMessages(conversationId);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // New chat (no conversationId in the URL) starts empty; opening an older
  // one hydrates local state from its stored history once it arrives.
  useEffect(() => {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    if (historyQuery.data) {
      setMessages(
        historyQuery.data.map((m) => ({
          id: m.id,
          role: m.role === "agent" ? "assistant" : "user",
          content: m.content,
          timestamp: new Date(m.timestamp),
        }))
      );
    }
  }, [conversationId, historyQuery.data]);

  const handleSend = async () => {
    if (!inputValue.trim() || chatMutation.isPending) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const query = inputValue.trim();
    setInputValue("");

    try {
      // Try API first
      const response = await chatMutation.mutateAsync({ query, conversationId });

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.message,
        faqs: response.results as FAQ[],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // First turn of a new chat: the backend just created a conversation.
      // Adopt its id into the URL and refresh the sidebar so it shows up.
      if (!conversationId && response.conversation_id) {
        queryClient.invalidateQueries({ queryKey: conversationKeys.list() });
        navigate(`/chat/${response.conversation_id}`, { replace: true });
      }
    } catch (error) {
      // Fallback to local search if API fails
      const localResults = localSearch(query);

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content:
          localResults.length > 0
            ? `I found ${localResults.length} relevant FAQ${
                localResults.length > 1 ? "s" : ""
              } that might help you:`
            : "I couldn't find any FAQs matching your question. Try rephrasing or browse our knowledge base for more topics.",
        faqs: localResults,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    }
  };

  const [selectedFaq, setSelectedFaq] = useState<FAQ | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleSelectFaq = (faq: FAQ) => {
    setSelectedFaq(faq);
    setDrawerOpen(true);
  };

  return (
    <AppLayout>
      <div className="flex flex-col md:flex-row gap-6 max-w-6xl mx-auto">
        <ConversationSidebar />

        <div className="flex-1 min-w-0 h-[calc(100vh-10rem)] flex flex-col">
        {/* Chat Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-6"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent text-accent-foreground text-sm font-medium mb-4">
            <Sparkles className="w-4 h-4" />
            Semantic FAQ Search
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            How can we help?
          </h1>
          <p className="text-muted-foreground">
            Ask a question and we'll find the most relevant answers
          </p>
        </motion.div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-2 mb-4">
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="h-full flex flex-col items-center justify-center text-center"
            >
              <div className="w-16 h-16 rounded-2xl gradient-secondary flex items-center justify-center mb-4">
                <MessageCircle className="w-8 h-8 text-secondary-foreground" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Start a conversation
              </h3>
              <p className="text-muted-foreground max-w-sm">
                Type your question below and we'll search our knowledge base for
                relevant answers.
              </p>

              {/* Suggested Questions */}
              <div className="mt-8 flex flex-wrap justify-center gap-2">
                {[
                  "Polynomial vs Traditional Bots",
                  "Multimodal Interfaces",
                  "Deployments",
                  "LLMs",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      setInputValue(suggestion);
                      inputRef.current?.focus();
                    }}
                    className="px-4 py-2 rounded-full border border-border bg-card text-sm text-muted-foreground hover:text-foreground hover:border-primary/50 transition-all duration-200"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </motion.div>
          ) : (
            <div className="space-y-4 py-4">
              <AnimatePresence>
                {messages.map((message, index) => (
                  <ChatMessageBubble
                    key={message.id}
                    role={message.role}
                    content={message.content}
                    faqs={message.faqs}
                    index={index}
                    onSelectFaq={handleSelectFaq}
                  />
                ))}
              </AnimatePresence>

              {chatMutation.isPending && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="bg-card border border-border rounded-2xl rounded-bl-md px-4 py-3 shadow-soft-sm">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">
                        Searching knowledge base...
                      </span>
                    </div>
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <FaqDrawer
          faq={selectedFaq}
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
        />

        {/* Chat Input */}
        <ChatInput
          ref={inputRef}
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSend}
          isLoading={chatMutation.isPending}
        />
        </div>
      </div>
    </AppLayout>
  );
};

export default ChatPage;
