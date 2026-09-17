# Claude Guidelines for Retail Return Intelligence

## Frontend Guidelines & Design System Enforcement

When working in `frontend/`:
1. **Always use shadcn/ui Nova components (`@/components/ui/*`)**:
   - Interactive elements: Raw HTML elements `<button>`, `<input>`, `<kbd>`, `<textarea>`, `<select>` are **prohibited** in application code (`src/components/app/**` and `src/App.tsx`). Always use `<Button>`, `<Input>`, `<Kbd>`, `<Textarea>`, `<Select>` from `@/components/ui/*`.
   - Avatars: Always use `<Avatar>`, `<AvatarFallback>`, `<AvatarBadge>`, `<AvatarImage>` from `@/components/ui/avatar` for users, customers, and agents.
   - Empty states: Use `<Empty>` primitives from `@/components/ui/empty`.
   - Loading states: Use `<Spinner>` from `@/components/ui/spinner`.
   - Containers: Use `<Card>`, `<CardHeader>`, `<CardTitle>`, `<CardDescription>`, `<CardContent>` from `@/components/ui/card`.
   - Tabs: Use `<Tabs>`, `<TabsList>`, `<TabsTrigger>`, `<TabsContent>` from `@/components/ui/tabs`.

2. **Design Language (`design.md`)**:
   - Paper-white canvas (`bg-white`, `#ffffff`), hairline borders (`border-neutral-200`), subtle gray secondary backgrounds (`bg-neutral-50`/`bg-neutral-100`).
   - Pill geometry for filters, search bars, nav triggers, and badges (`rounded-full`).
   - Monospace accents (`font-mono`) for metrics, IDs, timestamps, and keys.

3. **Validation Commands**:
   - Run `npm run lint` in `frontend/` to verify no forbidden elements or lint errors.
   - Run `npm run build` in `frontend/` to verify TypeScript and Vite compilation.
