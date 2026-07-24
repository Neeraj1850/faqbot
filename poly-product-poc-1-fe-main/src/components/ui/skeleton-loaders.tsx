import { cn } from '@/lib/utils';

interface SkeletonLoaderProps {
  className?: string;
  count?: number;
}

export const FaqSkeleton = ({ className }: { className?: string }) => (
  <div className={cn('rounded-xl border border-border bg-card p-4 animate-pulse', className)}>
    <div className="h-5 bg-muted rounded w-3/4 mb-2" />
    <div className="h-4 bg-muted rounded w-1/4" />
  </div>
);

export const FaqListSkeleton = ({ count = 5 }: SkeletonLoaderProps) => (
  <div className="space-y-3">
    {Array.from({ length: count }).map((_, i) => (
      <FaqSkeleton key={i} />
    ))}
  </div>
);

export const TableRowSkeleton = () => (
  <tr className="animate-pulse">
    <td className="px-6 py-4">
      <div className="h-5 bg-muted rounded w-3/4 mb-2" />
      <div className="h-4 bg-muted rounded w-1/2" />
    </td>
    <td className="px-6 py-4 hidden md:table-cell">
      <div className="h-6 bg-muted rounded-full w-24" />
    </td>
    <td className="px-6 py-4 hidden lg:table-cell">
      <div className="h-4 bg-muted rounded w-20" />
    </td>
    <td className="px-6 py-4">
      <div className="flex justify-end gap-2">
        <div className="h-10 w-10 bg-muted rounded" />
        <div className="h-10 w-10 bg-muted rounded" />
      </div>
    </td>
  </tr>
);

export const TableSkeleton = ({ count = 5 }: SkeletonLoaderProps) => (
  <>
    {Array.from({ length: count }).map((_, i) => (
      <TableRowSkeleton key={i} />
    ))}
  </>
);

export const SectionSkeleton = ({ count = 5 }: SkeletonLoaderProps) => (
  <div className="space-y-2">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="h-10 bg-muted rounded-lg animate-pulse" />
    ))}
  </div>
);

export const ChatBubbleSkeleton = () => (
  <div className="flex justify-start">
    <div className="max-w-[70%] bg-card border border-border rounded-2xl rounded-bl-md px-4 py-3 animate-pulse">
      <div className="h-4 bg-muted rounded w-48 mb-2" />
      <div className="h-4 bg-muted rounded w-32" />
    </div>
  </div>
);
