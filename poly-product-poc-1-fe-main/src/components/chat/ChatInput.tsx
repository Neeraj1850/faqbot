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

    return (
      <div className="glass border-t p-4">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
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
      </div>
    );
  }
);

ChatInput.displayName = 'ChatInput';
