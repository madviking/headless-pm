'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { 
  Home, 
  Kanban, 
  Users, 
  MessageSquare, 
  BarChart3, 
  Activity 
} from 'lucide-react';

const navigationItems = [
  {
    name: 'Overview',
    href: '/',
    icon: Home,
  },
  {
    name: 'Tasks',
    href: '/tasks',
    icon: Kanban,
  },
  {
    name: 'Agents',
    href: '/agents',
    icon: Users,
  },
  {
    name: 'Communications',
    href: '/communications',
    icon: MessageSquare,
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
  },
  {
    name: 'System Health',
    href: '/health',
    icon: Activity,
  },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="border-b">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <div className="h-8 w-8 rounded bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold">PM</span>
              </div>
              <span className="font-semibold text-lg">Headless PM</span>
            </Link>
            
            <div className="hidden md:flex items-center gap-1">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href || 
                  (item.href !== '/' && pathname.startsWith(item.href));
                
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                      isActive
                        ? "bg-secondary text-secondary-foreground"
                        : "text-muted-foreground hover:bg-secondary/50 hover:text-secondary-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              Real-time Dashboard
            </span>
          </div>
        </div>
      </div>
    </nav>
  );
}