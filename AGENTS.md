# Repository Developer & Agent Guidelines

## Design System Constraints & Locked Rules

When writing frontend code under `frontend/`:
1. **Always use shadcn/ui Nova components (`@/components/ui/*`)**:
   - **Interactive Elements**: Raw HTML elements `<button>`, `<input>`, `<kbd>`, `<textarea>`, `<select>` are **prohibited** in application code (`src/components/app/**` and `src/App.tsx`). Use `<Button>`, `<Input>`, `<Kbd>`, `<Textarea>`, `<Select>` from `@/components/ui/*`.
   - **Avatars**: Always use `<Avatar>`, `<AvatarFallback>`, `<AvatarBadge>`, `<AvatarImage>` from `@/components/ui/avatar` for users, customers, and agent icons.
   - **Empty States**: Use `<Empty>` primitives from `@/components/ui/empty` when lists or search queries return 0 items.
   - **Loading States**: Use `<Spinner>` from `@/components/ui/spinner`.
   - **Containers**: Use `<Card>`, `<CardHeader>`, `<CardTitle>`, `<CardDescription>`, `<CardContent>` from `@/components/ui/card`.
   - **Tabs**: Use `<Tabs>`, `<TabsList>`, `<TabsTrigger>`, `<TabsContent>` from `@/components/ui/tabs`.
2. **Design Language (`design.md`)**:
   - Paper-white canvas (`bg-white`, `#ffffff`), hairline borders (`border-neutral-200`), subtle gray secondary backgrounds (`bg-neutral-50`/`bg-neutral-100`).
   - Pill geometry for filters, nav triggers, and badges (`rounded-full`).
   - Monospace accents (`font-mono`) for metrics, IDs, and timestamps.
3. **Automated Enforcement**:
   - ESLint rule `react/forbid-elements` strictly flags any forbidden raw elements during `npm run lint` and git commits via Husky (`.husky/pre-commit` -> `lint-staged`).
   - Do not bypass or disable these rules without architectural review.
