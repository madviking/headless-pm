import { Navigation } from './navigation';
import { cn } from '@/lib/utils';

interface PageLayoutProps {
  children: React.ReactNode;
  fullWidth?: boolean;
  mainClassName?: string;
}

export function PageLayout({ children, fullWidth = false, mainClassName }: PageLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Navigation fullWidth={fullWidth} />
      <main
        className={cn(
          fullWidth ? 'w-full px-4 py-6' : 'container mx-auto px-4 py-6',
          mainClassName
        )}
      >
        {children}
      </main>
    </div>
  );
}
