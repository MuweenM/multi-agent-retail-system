import { cn } from 'cn';

function Kbd({ className, ...props }: React.ComponentProps<'kbd'>) {
  return (
    <kbd
      data-slot="kbd"
      className={cn(
        "in-data-[slot=tooltip-content]:bg-white/15 in-data-[slot=tooltip-content]:text-white pointer-events-none inline-flex h-5 w-fit min-w-5 select-none items-center justify-center gap-1 rounded border border-neutral-200 bg-white px-1.5 font-mono text-[10px] font-medium text-neutral-600 shadow-[0_1px_1px_rgba(0,0,0,0.04)] dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-400 [&_svg:not([class*='size-'])]:size-3",
        className
      )}
      {...props}
    />
  );
}

function KbdGroup({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <kbd
      data-slot="kbd-group"
      className={cn('inline-flex items-center gap-1', className)}
      {...props}
    />
  );
}

export { Kbd, KbdGroup };
