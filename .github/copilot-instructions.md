# GitHub Copilot Instructions for Retail Return Intelligence

When generating or editing frontend code in this repository (`frontend/`):

1. **Mandatory Shadcn/UI Components (`@/components/ui/*`)**:
   - Do NOT output raw `<button>`, `<input>`, `<kbd>`, `<textarea>`, or `<select>`.
   - Use `<Button>`, `<Input>`, `<Kbd>`, `<Textarea>`, `<Select>` from `@/components/ui/*`.
   - Use `<Avatar>`, `<AvatarFallback>`, `<AvatarBadge>` from `@/components/ui/avatar` for users, customers, and agents.
   - Use `<Empty>` components from `@/components/ui/empty` for zero-result states.
   - Use `<Spinner>` from `@/components/ui/spinner` for loading states.
   - Use `<Card>`, `<Tabs>`, `<Badge>`, and `<Dialog>` from `@/components/ui/*`.

2. **Design Language (`design.md`)**:
   - Paper-white canvas (`#ffffff`, `bg-white`).
   - Hairline borders (`border border-neutral-200`).
   - Pill geometry (`rounded-full` for search pills, filters, chips).
   - Monospace typography (`font-mono`) for metrics, IDs, timestamps, and keys.

3. **ESLint Constraint**:
   - The ESLint rule `react/forbid-elements` strictly bans raw interactive elements. Any violation will fail CI and pre-commit hooks.
