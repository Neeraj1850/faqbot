import { forwardRef } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isLoading?: boolean;
}

export const ChatInput = forwardRef<HTMLInputElement, ChatInputProps>(
  ({ value, onChange, onSend, isLoading }, ref) => {
    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        onSend();
      }
    };

    // No outer wrapper here on purpose: the caller supplies the surrounding
    // container, since this same pill is used both pinned to the bottom of
    // an active conversation and centered mid-page on a fresh chat.
    return (
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <input
            ref={ref}
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            disabled={isLoading}
            className="w-full h-12 px-5 rounded-full border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-all duration-200 shadow-soft-sm focus:shadow-soft-md"
          />
        </div>
        <Button
          onClick={onSend}
          disabled={!value.trim() || isLoading}
          variant="brand"
          size="icon"
          className="h-12 w-12 rounded-full shrink-0"
        >
          <Send className="w-5 h-5" />
        </Button>
      </div>
    );
  }
);

ChatInput.displayName = 'ChatInput';
