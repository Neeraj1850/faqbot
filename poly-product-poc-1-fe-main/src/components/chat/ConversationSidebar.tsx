import { Link, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Plus, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";
import { useConversations } from "@/hooks/useFaqApi";

// Mirrors the styling conventions of SectionSidebar (FAQ section list):
// same aside/sticky wrapper, same active-item highlight pattern.
export const ConversationSidebar = () => {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { data: conversations } = useConversations();

  return (
    <aside className="w-full md:w-64 shrink-0">
      <div className="sticky top-24">
        <button
          onClick={() => navigate("/chat")}
          className="w-full mb-4 flex items-center gap-2 px-3 py-2.5 rounded-lg border border-border bg-card text-sm font-medium text-foreground hover:border-primary/50 transition-all duration-200"
        >
          <Plus className="w-4 h-4" />
          New chat
        </button>

        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-3">
          Conversations
        </h2>

        <nav className="space-y-1 max-h-[60vh] overflow-y-auto">
          {(conversations ?? []).map((conv, index) => {
            const isActive = conversationId === conv.id;

            return (
              <motion.div
                key={conv.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.03 }}
              >
                <Link
                  to={`/chat/${conv.id}`}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2.5 rounded-lg text-left transition-all duration-200",
                    isActive
                      ? "text-primary font-medium bg-accent"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                  )}
                >
                  <MessageSquare className="w-4 h-4 shrink-0" />
                  <span className="truncate text-sm">
                    {new Date(conv.updated_at).toLocaleString()}
                  </span>
                </Link>
              </motion.div>
            );
          })}

          {conversations?.length === 0 && (
            <p className="px-3 py-2 text-sm text-muted-foreground">No conversations yet</p>
          )}
        </nav>
      </div>
    </aside>
  );
};
