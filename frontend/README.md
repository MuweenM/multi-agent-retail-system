# Frontend Design System & Component Guidelines

## Architecture Overview
This frontend is built using **React 18 + Vite + TypeScript + Tailwind CSS**, powered by the **shadcn/ui Nova preset** (`radix-nova` base). It follows the design guidelines set forth in `design.md`.

---

## 🔒 Design System Lock & Enforced Rules

To ensure strict visual consistency and prevent component fragmentation across all contributors and AI agents, the following constraints are **enforced via ESLint (`react/forbid-elements`) and Husky pre-commit hooks (`lint-staged`)**:

### 1. Prohibited Raw HTML Elements
Raw HTML elements for form controls and interactive primitives are strictly forbidden in application code (`src/components/app/**/*.{ts,tsx}` and `src/App.tsx`). You must use the corresponding shadcn/ui components:

| Raw HTML Element | Required shadcn/ui Component | Import Path |
| :--- | :--- | :--- |
| `<button>` | `<Button>` | `@/components/ui/button` |
| `<input>` | `<Input>` | `@/components/ui/input` |
| `<kbd>` | `<Kbd>` | `@/components/ui/kbd` |
| `<textarea>` | `<Textarea>` | `@/components/ui/textarea` |
| `<select>` | `<Select>` | `@/components/ui/select` |

### 2. Avatars
Never render customer, operator, or agent initials or profile circles using raw `<div>` or text tags. Always use the shadcn `Avatar` suite:
```tsx
import { Avatar, AvatarFallback, AvatarBadge } from '@/components/ui/avatar';

// Operator Profile:
<Avatar size="sm" className="border border-neutral-200">
  <AvatarFallback className="bg-neutral-100 text-neutral-900 font-mono text-[11px] font-semibold">
    OP
  </AvatarFallback>
  <AvatarBadge className="bg-emerald-500" />
</Avatar>

// Customer Initials in Table:
<Avatar size="sm" className="border border-neutral-200 shrink-0">
  <AvatarFallback className="bg-neutral-100 text-neutral-700 font-mono text-[10px] font-medium">
    JD
  </AvatarFallback>
</Avatar>
```

### 3. State & Feedback Primitives
- **Empty States**: Use `<Empty>`, `<EmptyMedia>`, `<EmptyHeader>`, `<EmptyTitle>`, `<EmptyDescription>` from `@/components/ui/empty` whenever search results or table rows are empty.
- **Spinners / Loading**: Use `<Spinner>` from `@/components/ui/spinner`.
- **Status Badges**: Use `<Badge>` from `@/components/ui/badge` with `variant="outline"` or `variant="secondary"`.
- **Containers & Surfaces**: Use `<Card>`, `<CardHeader>`, `<CardTitle>`, `<CardDescription>`, `<CardContent>` from `@/components/ui/card`.
- **Tabs**: Use `<Tabs>`, `<TabsList>`, `<TabsTrigger>`, `<TabsContent>` from `@/components/ui/tabs`.

---

## 🎨 Visual Aesthetics & Tokens (`design.md`)

- **Canvas**: Pure Paper White (`#ffffff`, `bg-white`)
- **Hairline Borders**: `border border-neutral-200` (`#e5e5e5`)
- **Secondary Surfaces**: `bg-neutral-50` / `bg-neutral-100` (`#f9fafb` / `#f4f4f5`)
- **Pill Geometry**: Outer search pills, top navigation tabs, status chips, and filter toggles must adhere to `rounded-full` or `rounded-xl` / `rounded-2xl` card containers.
- **Typography**:
  - Headings & Body: Inter / Sans
  - IDs, Metrics, Timestamps, Labels: JetBrains Mono (`font-mono`, `uppercase`, `tracking-wider`)

---

## 🛠️ Verification & CI Commands

Before committing changes, ensure both linting and type-checking pass:

```bash
# In /frontend:
npm run lint    # Runs ESLint (verifies forbidden raw elements)
npm run build   # Validates TypeScript types and Vite bundle
```
