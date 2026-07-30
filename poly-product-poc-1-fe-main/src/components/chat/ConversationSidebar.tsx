import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, PanelLeftClose, PanelLeftOpen, Plus, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { useConversations } from "@/hooks/useFaqApi";

// Gemini-style Recents sidebar, built on this app's existing theme tokens
// (no new colors) — collapse-to-icon-rail, a client-side title filter over
// the already-fetched conversation list, and real per-chat titles.
export const ConversationSidebar = () => {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { data: conversations } = useConversations();

  const [collapsed, setCollapsed] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = useMemo(() => {
    const list = conversations ?? [];
    if (!searchQuery.trim()) return list;
    const q = searchQuery.toLowerCase();
    return list.filter((c) => (c.title ?? "").toLowerCase().includes(q));
  }, [conversations, searchQuery]);

  if (collapsed) {
    return (
      <aside className="shrink-0 flex flex-col items-center gap-2 py-1">
        <button
          onClick={() => setCollapsed(false)}
          title="Expand sidebar"
          className="w-10 h-10 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-all duration-200"
        >
          <PanelLeftOpen className="w-5 h-5" />
        </button>
        <button
          onClick={() => navigate("/chat")}
          title="New chat"
          className="w-10 h-10 flex items-center justify-center rounded-lg border border-border bg-card text-foreground hover:border-primary/50 transition-all duration-200"
        >
          <Plus className="w-5 h-5" />
        </button>
        <button
          onClick={() => setCollapsed(false)}
          title="Search chats"
          className="w-10 h-10 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-all duration-200"
        >
          <Search className="w-5 h-5" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="w-full md:w-64 shrink-0">
      <div className="sticky top-24">
        <div className="flex items-center justify-between mb-3 px-1">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Recents
          </h2>
          <button
            onClick={() => setCollapsed(true)}
            title="Collapse sidebar"
            className="w-7 h-7 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-all duration-200"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        <button
          onClick={() => navigate("/chat")}
          className="w-full mb-2 flex items-center gap-2 px-3 py-2.5 rounded-lg border border-border bg-card text-sm font-medium text-foreground hover:border-primary/50 transition-all duration-200"
        >
          <Plus className="w-4 h-4" />
          New chat
        </button>

        {searchOpen ? (
          <div className="mb-3 flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-background">
            <Search className="w-4 h-4 text-muted-foreground shrink-0" />
            <input
              autoFocus
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onBlur={() => {
                if (!searchQuery) setSearchOpen(false);
              }}
              placeholder="Search chats"
              className="w-full bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
            />
          </div>
        ) : (
          <button
            onClick={() => setSearchOpen(true)}
            className="w-full mb-3 flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-all duration-200"
          >
            <Search className="w-4 h-4" />
            Search chats
          </button>
        )}

        <nav className="space-y-1 max-h-[55vh] overflow-y-auto">
          <AnimatePresence>
            {filtered.map((conv, index) => {
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
                    <span className="truncate text-sm">{conv.title ?? "New conversation"}</span>
                  </Link>
                </motion.div>
              );
            })}
          </AnimatePresence>

          {filtered.length === 0 && (
            <p className="px-3 py-2 text-sm text-muted-foreground">
              {searchQuery ? "No matching chats" : "No conversations yet"}
            </p>
          )}
        </nav>
      </div>
    </aside>
  );
};
