# GreenLight Design System

## Overview
This document defines the visual design language for the GreenLight application, ensuring consistency across all pages and components.

---

## Color System

### Primary Color Variables (from `globals.css`)

These are the **core design tokens** that should be used for 90% of UI elements. They automatically adapt to light/dark mode.

#### Foundation Colors

```css
--color-primary: #5E6AD2           /* Primary brand purple-blue */
--color-primary-hover: #4F5BC4     /* Darker shade for hover states */
```

**Usage:**
- Primary action buttons (CTA buttons, submit buttons)
- Active states and selections
- Brand elements and accents

**Example:**
```tsx
<button className="bg-(--color-primary) hover:bg-(--color-primary-hover) text-white">
  Submit
</button>
```

#### Background Colors

```css
--color-background: #ffffff        /* Light mode: white */
--color-background: #0D0E12        /* Dark mode: near-black */
--color-input-bg: #F7F7F8         /* Light mode: subtle gray */
--color-input-bg: #16161D         /* Dark mode: dark gray */
```

**Usage:**
- `--color-background`: Page backgrounds, modal backgrounds
- `--color-input-bg`: Input fields, cards, elevated surfaces

**Example:**
```tsx
<div className="bg-(--color-background)">
  <input className="bg-(--color-input-bg)" />
</div>
```

#### Text Colors

```css
--color-text: #16161D              /* Light mode: near-black */
--color-text: #E6E6EA              /* Dark mode: near-white */
--color-text-secondary: #6E6E80    /* Light mode: medium gray */
--color-text-secondary: #8B8B9A    /* Dark mode: lighter gray */
```

**Usage:**
- `--color-text`: Body text, headings, primary labels
- `--color-text-secondary`: Captions, helper text, placeholders, timestamps

**Example:**
```tsx
<h1 className="text-(--color-text)">Main Heading</h1>
<p className="text-(--color-text-secondary)">Subtitle or description</p>
```

#### Border Colors

```css
--color-border: #E6E6EA            /* Light mode: light gray */
--color-border: #2C2D33            /* Dark mode: dark gray */
--color-input-border: #E1E1E5      /* Light mode: slightly darker */
--color-input-border: #2C2D33      /* Dark mode: same as border */
```

**Usage:**
- `--color-border`: Dividers, card borders, section separators
- `--color-input-border`: Input fields, form elements

**Example:**
```tsx
<div className="border border-(--color-border)">
  <input className="border-b border-(--color-input-border)" />
</div>
```

---

### Semantic Color Palette (Status & Feedback)

These colors are used for **status indicators, feedback, and semantic meaning**. They use fixed Tailwind colors for consistency across light/dark modes.

#### Success State (Green)
```
bg-green-500/20       /* Background with 20% opacity */
text-green-400        /* Text/icon color */
border-green-500/50   /* Border with 50% opacity */
```

**Usage:** Completed jobs, success messages, positive indicators

**Example:**
```tsx
<div className="bg-green-500/20 text-green-400 border border-green-500/50">
  ✓ Completado
</div>
```

#### Warning State (Yellow)
```
bg-yellow-500/20
text-yellow-400
border-yellow-500/50
```

**Usage:** Pending jobs, warnings, requires attention

#### Error State (Red)
```
bg-red-500/20
text-red-400
border-red-500/50
```

**Usage:** Failed jobs, errors, destructive actions

**Example:**
```tsx
<button className="text-red-500 hover:text-red-600">Delete</button>
```

#### In Progress State (Blue)
```
bg-blue-500/20
text-blue-400
border-blue-500/50
```

**Usage:** Active processes, loading states, informational messages

---

### Accent Colors (Service Types & Categories)

These are used to **visually distinguish different service types or categories** in the jobs page.

#### Emerald (Research Services)
```
from-emerald-500/20 to-emerald-600/20
text-emerald-400
border-emerald-500/50
```

**Usage:** Research, Market Research, External Research services

#### Pink/Purple (Communication Services)
```
from-pink-500/20 to-purple-500/20
text-pink-400
border-pink-500/50
```

**Usage:** Slack integration, internal communication

#### Blue (Data Services)
```
from-blue-500/20 to-blue-600/20
text-blue-400
border-blue-500/50
```

**Usage:** Internal data, database queries, logs

#### Orange (External Communication)
```
from-orange-500/20 to-orange-600/20
text-orange-400
border-orange-500/50
```

**Usage:** Email services, external contacts

---

### Brand Accent (Emerald for Logo/Title)
```
text-emerald-400
```

**Usage:** The "GreenLight" brand name/logo on the homepage

**Example:**
```tsx
<h1 className="text-emerald-400">GreenLight</h1>
```

---

## Typography

### Font Family
```css
--font-sans: var(--font-outfit)
```

The app uses the **Outfit** font family for all text.

### Text Size Scale

| Class | Size | Usage |
|-------|------|-------|
| `text-xs` | 0.75rem | Helper text, labels, metadata |
| `text-sm` | 0.875rem | Body text, descriptions |
| `text-base` | 1rem | Default body text, inputs |
| `text-lg` | 1.125rem | Section headers, card titles |
| `text-xl` | 1.25rem | Page headers, modal titles |
| `text-2xl` | 1.5rem | Large headers |
| `text-4xl` | 2.25rem | Hero text (mobile) |
| `text-6xl` | 3.75rem | Hero text (tablet) |
| `text-7xl` | 4.5rem | Hero text (desktop) |

### Font Weights

| Class | Weight | Usage |
|-------|--------|-------|
| `font-medium` | 500 | Emphasized text, button labels |
| `font-semibold` | 600 | Headers, important labels |
| `font-bold` | 700 | Large headings, strong emphasis |

---

## Component Patterns

### Buttons

#### Primary Button (CTA)
```tsx
<button className="rounded-md bg-(--color-primary) px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-(--color-primary-hover) disabled:opacity-50 disabled:cursor-not-allowed">
  Continue
</button>
```

#### Secondary Button (Border)
```tsx
<button className="rounded-md border border-(--color-border) px-6 py-2 text-sm font-medium text-(--color-text) transition-colors hover:bg-(--color-input-bg)">
  Cancel
</button>
```

#### Text Button (Navigation)
```tsx
<button className="text-sm text-(--color-text-secondary) transition-colors hover:text-(--color-text)">
  ← Back
</button>
```

### Cards

#### Basic Card
```tsx
<div className="rounded-xl border border-(--color-border) bg-(--color-input-bg) p-5">
  <h3 className="text-sm font-medium text-(--color-text)">Title</h3>
  <p className="mt-1 text-xs text-(--color-text-secondary)">Description</p>
</div>
```

#### Card with Accent Border (Status)
```tsx
<div className="rounded-lg border border-green-500/50 bg-green-500/20 p-4">
  <span className="text-green-400">Success content</span>
</div>
```

### Inputs

#### Text Input
```tsx
<input
  type="text"
  className="w-full bg-(--color-input-bg) border border-(--color-input-border) rounded-lg px-5 py-4 text-base text-(--color-text) outline-none placeholder:text-(--color-text-secondary)"
  placeholder="Enter text..."
/>
```

#### Textarea
```tsx
<textarea
  className="w-full bg-(--color-input-bg) border border-(--color-input-border) rounded-lg px-5 py-4 text-base text-(--color-text) outline-none placeholder:text-(--color-text-secondary) resize-none"
  rows={4}
/>
```

### Status Badges

```tsx
{/* Success */}
<span className="rounded border border-green-500/50 bg-green-500/20 px-2 py-0.5 text-xs font-medium text-green-400">
  Completado
</span>

{/* Warning */}
<span className="rounded border border-yellow-500/50 bg-yellow-500/20 px-2 py-0.5 text-xs font-medium text-yellow-400">
  Pendiente
</span>

{/* Error */}
<span className="rounded border border-red-500/50 bg-red-500/20 px-2 py-0.5 text-xs font-medium text-red-400">
  Fallido
</span>

{/* In Progress */}
<span className="rounded border border-blue-500/50 bg-blue-500/20 px-2 py-0.5 text-xs font-medium text-blue-400">
  En Progreso
</span>
```

### Loading States

#### Spinner (for buttons)
```tsx
<svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
</svg>
```

#### Bounce Dots (for message loading)
```tsx
<div className="flex items-center space-x-2">
  <div className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)" style={{ animationDelay: "0ms" }}></div>
  <div className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)" style={{ animationDelay: "100ms" }}></div>
  <div className="h-2 w-2 animate-bounce rounded-full bg-(--color-text-secondary)" style={{ animationDelay: "300ms" }}></div>
</div>
```

---

## Spacing & Layout

### Container Widths
- **max-w-3xl**: Chat/conversation pages (48rem / 768px)
- **max-w-4xl**: Summary page (56rem / 896px)
- **max-w-6xl**: Jobs page, wide layouts (72rem / 1152px)

### Padding Scale
- **px-4, py-4**: Mobile padding
- **px-6, py-6**: Standard padding for headers, footers
- **px-8, py-8**: Content area padding
- **p-5**: Card padding

### Border Radius
- **rounded-md**: Buttons, small elements
- **rounded-lg**: Inputs, cards, modals
- **rounded-xl**: Large cards, containers
- **rounded-full**: Badges, dots, circular elements

---

## Animation & Transitions

### Standard Transitions
```tsx
transition-colors       // Color changes (buttons, links)
transition-all          // Multiple properties
duration-300           // Standard speed (300ms)
duration-500           // Slower (500ms)
ease-out              // Smooth deceleration
```

### Animations
```tsx
animate-pulse          // Pulsing effect (ready states)
animate-bounce         // Bouncing dots (loading)
animate-spin          // Spinner rotation
animate-fade-in       // Fade in (custom, if defined)
```

---

## Dark Mode Support

All CSS variables automatically adapt to dark mode via `@media (prefers-color-scheme: dark)`.

**DO NOT** use separate dark mode classes. The design system handles this automatically.

**Example - Correct:**
```tsx
<div className="bg-(--color-background) text-(--color-text)">
  {/* Automatically adapts to dark mode */}
</div>
```

**Example - Incorrect:**
```tsx
<div className="bg-white dark:bg-gray-900 text-black dark:text-white">
  {/* Don't do this - use CSS variables instead */}
</div>
```

---

## Guidelines

### When to Use CSS Variables vs. Fixed Colors

#### Use CSS Variables (`--color-*`) for:
- ✅ Backgrounds, surfaces, containers
- ✅ Body text, headings, labels
- ✅ Borders and dividers
- ✅ Primary action buttons
- ✅ Anything that should adapt to light/dark mode

#### Use Fixed Tailwind Colors for:
- ✅ Status indicators (success, error, warning)
- ✅ Semantic feedback (green for success, red for error)
- ✅ Service type badges (pink for Slack, emerald for research)
- ✅ Brand accent color (emerald for "GreenLight")

### Color Contrast & Accessibility

- Ensure text has sufficient contrast against backgrounds
- Use `text-(--color-text)` on `bg-(--color-input-bg)` surfaces
- Use `text-(--color-text-secondary)` for de-emphasized text
- Status colors are pre-tested for accessibility

### Consistency Checklist

Before adding new UI elements, ensure:
1. ✅ Are you using CSS variables for background/text/borders?
2. ✅ Are status colors using the semantic palette?
3. ✅ Are button styles matching existing patterns?
4. ✅ Does it work in both light and dark mode?
5. ✅ Are transitions consistent with the rest of the app?

---

## Page-Specific Examples

### Homepage (`page.tsx`)
- Brand title: `text-emerald-400`
- Input: `bg-(--color-input-bg)` with `border-(--color-input-border)`
- Primary button: `bg-(--color-primary)` with `hover:bg-(--color-primary-hover)`

### Conversation Page (`conversation/page.tsx`)
- User messages: `bg-(--color-primary)` with `text-white`
- Assistant messages: `bg-(--color-input-bg)` with `text-(--color-text)`
- Progress button (disabled): `bg-(--color-text-secondary)` with `opacity-50`
- Progress button (enabled): `bg-(--color-primary)` with `hover:bg-(--color-primary-hover)`
- Progress bar fill: `bg-(--color-primary)` with `opacity-60` for subtle fill effect
- Clear button hover: `hover:text-red-400` (semantic destructive action)

### Jobs Page (`jobs/page.tsx`)
- Service type cards: Use accent colors (emerald, pink, blue, orange)
- Status badges: Use semantic colors (green, yellow, blue, red)
- Card backgrounds: `bg-(--color-input-bg)`

### Summary Page (`summary/page.tsx`)
- Content card: `bg-(--color-input-bg)` with `border-(--color-border)`
- Export button: `bg-(--color-primary)` with `hover:bg-(--color-primary-hover)`

---

## Migration Notes

If updating existing components:

1. **Replace hardcoded backgrounds:**
   - `bg-white` → `bg-(--color-background)`
   - `bg-gray-100` → `bg-(--color-input-bg)`

2. **Replace hardcoded text colors:**
   - `text-black`, `text-gray-900` → `text-(--color-text)`
   - `text-gray-500`, `text-gray-600` → `text-(--color-text-secondary)`

3. **Replace hardcoded borders:**
   - `border-gray-200`, `border-gray-300` → `border-(--color-border)`

4. **Keep semantic colors as-is:**
   - Status badges (green, yellow, red, blue) stay unchanged
   - Service type accents (emerald, pink, orange) stay unchanged

---

## Version History

- **v1.0** (2025-11-22): Initial design system documentation
