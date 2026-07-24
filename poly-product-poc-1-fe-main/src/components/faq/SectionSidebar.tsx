import { motion } from 'framer-motion';
import { Section } from '@/types/faq';
import { cn } from '@/lib/utils';

interface SectionSidebarProps {
  sections: Section[];
  selectedSection: string | null;
  onSelectSection: (section: string) => void;
}

export const SectionSidebar = ({ sections, selectedSection, onSelectSection }: SectionSidebarProps) => {
  return (
    <aside className="w-full md:w-64 shrink-0">
      <div className="sticky top-24">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 px-3">
          Sections
        </h2>
        <nav className="space-y-1">
          {sections.map((section, index) => {
            const isActive = selectedSection === section.name;
            
            return (
              <motion.button
                key={section.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                onClick={() => onSelectSection(section.name)}
                className={cn(
                  "w-full px-3 py-2.5 rounded-lg text-left transition-all duration-200 relative group",
                  isActive 
                    ? "text-primary font-medium" 
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeSection"
                    className="absolute inset-0 bg-accent rounded-lg"
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}
                <span className="relative z-10 flex items-center justify-between">
                  <span>{section.name}</span>
                  <span className={cn(
                    "text-xs px-2 py-0.5 rounded-full transition-colors",
                    isActive 
                      ? "bg-primary/10 text-primary" 
                      : "bg-muted text-muted-foreground group-hover:bg-accent"
                  )}>
                    {section.faqCount}
                  </span>
                </span>
              </motion.button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
};
