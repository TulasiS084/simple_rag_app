---
name: uiux-design
description: Comprehensive UI/UX design guide covering user research, information architecture, wireframing, design systems, visual hierarchy, color theory, typography, component specs, accessibility, interaction design, and design-to-dev handoff.
---

# UI/UX Design Skill

Standards for designing intuitive, accessible, and visually polished user interfaces.

---

## 1. Design Process

```
Discover → Define → Design → Prototype → Validate → Handoff
```

Never skip to visuals before understanding the user and their goals.

---

## 2. User Research

Before designing any screen:
- **Who is the user?** — define persona: goals, pain points, technical literacy, device preference
- **What job are they doing?** — use Jobs-to-be-Done framing ("When I _____, I want to _____ so I can _____")
- **What are the critical paths?** — identify the 3–5 flows users do most (login, primary action, error recovery)

---

## 3. Information Architecture

Structure content before styling it:

```
App
├── Auth
│   ├── Login
│   └── Register
├── Dashboard (primary workspace)
│   ├── Overview / summary
│   └── Primary list/grid
├── Detail view
│   ├── Content
│   └── Actions
└── Settings / Profile
```

**Rules:**
- Max 3 levels of navigation depth (users get lost beyond that)
- Group related items — don't scatter related actions across the UI
- Every screen needs a clear **primary action** (the most important thing the user does there)
- Secondary actions must be visually subordinate to the primary

---

## 4. Design Tokens — Define Before Designing

Always define tokens before designing components:

```json
{
  "color": {
    "brand-primary": "#4f46e5",
    "brand-secondary": "#7c3aed",
    "text-primary": "#111827",
    "text-secondary": "#6b7280",
    "text-muted": "#9ca3af",
    "bg-base": "#f9fafb",
    "bg-surface": "#ffffff",
    "bg-elevated": "#f3f4f6",
    "border": "#e5e7eb",
    "danger": "#dc2626",
    "success": "#16a34a",
    "warning": "#d97706"
  },
  "spacing": {
    "xs": "4px", "sm": "8px", "md": "16px",
    "lg": "24px", "xl": "32px", "2xl": "48px"
  },
  "radius": {
    "sm": "6px", "md": "10px", "lg": "16px", "full": "9999px"
  },
  "font-size": {
    "xs": "11px", "sm": "13px", "base": "15px",
    "lg": "18px", "xl": "22px", "2xl": "28px", "3xl": "36px"
  },
  "font-weight": {
    "normal": 400, "medium": 500, "semibold": 600, "bold": 700
  },
  "shadow": {
    "sm": "0 1px 3px rgba(0,0,0,0.08)",
    "md": "0 4px 12px rgba(0,0,0,0.08)",
    "lg": "0 10px 30px rgba(0,0,0,0.10)"
  }
}
```

**Never** use magic numbers (`padding: 13px`) in designs — always reference a token.

---

## 5. Visual Hierarchy

Every screen needs clear hierarchy — users scan in priority order:

1. **Size** — bigger = more important
2. **Weight** — bold = primary, regular = secondary
3. **Color** — accent color draws attention
4. **Contrast** — high contrast = important, low = secondary
5. **Space** — more space around an element = more important
6. **Position** — top-left first (in LTR languages)

**Checklist:**
- [ ] Can you identify the primary action in < 2 seconds?
- [ ] Is the page title/heading clear and prominent?
- [ ] Are secondary actions visually subordinate?
- [ ] Is destructive actions (delete, cancel) styled with danger color AND require confirmation?

---

## 6. Typography

```
Page title:     28–36px, bold (700), letter-spacing -0.5px
Section title:  20–24px, semibold (600)
Body text:      15–16px, regular (400), line-height 1.6
Label:          12–13px, medium (500), uppercase + letter-spacing 0.06em
Caption:        11–12px, regular (400), muted color
Code:           13–14px, monospace
```

**Rules:**
- Maximum 2 font families per product (one for headings, one for body — or just one)
- Line length: 60–80 characters for body text (beyond that: hard to read)
- Line height: 1.5–1.7 for body, 1.1–1.2 for headings
- Never use font weight below 400 for body text

---

## 7. Color Usage

```
Primary/accent: 5–10% of the UI (buttons, links, highlights)
Neutral:        80–85% (backgrounds, text, borders)
Semantic:       5–10% (success green, error red, warning yellow)
```

**Accessibility — minimum contrast ratios:**
- Body text: 4.5:1 against background (WCAG AA)
- Large text (18px bold or 24px regular): 3:1
- UI components/icons: 3:1
- Never convey information by color alone — add icon or label

**Dark mode rule:** Define all colors with both light and dark values — never hardcode `#ffffff` or `#000000` directly.

---

## 8. Component Specifications

When specifying components for developers, always include:

```markdown
## Button — Primary

**Purpose**: Main call-to-action. One per view.

**Anatomy**:
- Background: `color.brand-primary` → hover: darken 8%
- Text: white, font-weight: 600, font-size: sm (13px)
- Padding: `spacing.sm spacing.md` (8px 16px)
- Border-radius: `radius.sm` (6px)
- Height: 36px (sm), 42px (md, default), 48px (lg)
- Transition: background 150ms ease

**States**:
- Default: brand-primary bg
- Hover: brand-primary darkened 8%
- Focus: 2px outline, brand-primary, 2px offset (MUST be visible)
- Disabled: 50% opacity, cursor: not-allowed
- Loading: spinner icon + disabled state

**Don'ts**:
- Never use more than one primary button per page section
- Never disable without explaining why (show tooltip or error)
```

---

## 9. Spacing & Layout

**8-point grid system:** All spacing must be multiples of 4 or 8.
```
✅ 4, 8, 12, 16, 20, 24, 32, 40, 48, 64
❌ 5, 7, 13, 17 (magic numbers)
```

**Layout containers:**
```
Full width:   100%
Wide content: max-width 1200px
Content:      max-width 900px
Narrow/form:  max-width 480px
```

**Card layout rules:**
- Cards need consistent padding (16–24px)
- Cards need border or shadow — not both (pick one visual cue)
- Card corner radius consistent with the design system

---

## 10. Interaction Design

**Feedback for every user action:**
- Button click → immediate visual response (loading state, or success)
- Form submission → clear success/error state
- Async operations → loading indicator, not a blank screen
- Destructive actions → confirmation dialog, not instant execution

**Animation principles:**
- Duration: 100–300ms for UI responses, 300–500ms for page transitions
- Easing: `ease-out` for elements entering, `ease-in` for elements leaving
- Purpose: animations must communicate state change, not just decorate
- Respect `prefers-reduced-motion` — provide a no-animation fallback

---

## 11. Responsive Design

```
Mobile:  < 640px   — single column, bottom navigation, full-width buttons
Tablet:  640–1024px — 2-column layouts, side navigation appears
Desktop: > 1024px  — full navigation, multi-column, sidebar patterns
```

**Mobile-first rule:** Design for 375px width first, then scale up.
**Touch targets:** Minimum 44×44px for any interactive element on mobile.
**Thumb zone:** Primary actions in the bottom 60% of the mobile screen.

---

## 12. Design-to-Dev Handoff Checklist

Before handing off to `ui-component-worker` or `frontend-lead`:
- [ ] All design tokens documented in `design-spec.md`
- [ ] Every component state designed: default, hover, focus, active, disabled, loading, error, empty
- [ ] All responsive breakpoints specified
- [ ] All ARIA roles and labels specified for interactive components
- [ ] Color contrast verified (use a contrast checker)
- [ ] All icons from a consistent icon set (no mixing icon libraries)
- [ ] Font sizes use the token scale (no arbitrary sizes)
- [ ] Spacing uses the 8-point grid (no arbitrary spacing)
- [ ] Component spec includes: purpose, anatomy, states, do's and don'ts
