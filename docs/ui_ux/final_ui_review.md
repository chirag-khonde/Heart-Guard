# HeartGuard UI/UX Final Review — Phase 18

## Design System

### Color Tokens
The application uses a centralized color palette defined in `src/ui/charts.py` (PALETTE) and `src/ui/theme.py` (COLORS):

| Token | Hex | Usage |
|---|---|---|
| primary | `#1e3a8a` | Headers, primary buttons, branding |
| clinical | `#0284c7` | Clinical risk components (70%) |
| lifestyle | `#10b981` | Lifestyle risk components (30%) |
| overall | `#4f46e5` | Multimodal overall risk |
| low | `#16a34a` | Low risk category |
| elevated | `#d97706` | Elevated risk category |
| high | `#ea580c` | High risk category |
| critical | `#dc2626` | Critical risk category |
| success | `#16a34a` | Success states |
| warning | `#d97706` | Warning states |
| error | `#dc2626` | Error states |
| info | `#2563eb` | Informational states |
| muted | `#64748b` | Muted text, captions |
| border | `#e2e8f0` | Card borders, dividers |
| surface | `#f8fafc` | Card backgrounds, sidebar |

### Typography
- Font: System font stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`)
- Headings: 1.3 line height, `--hg-text` color
- Body: Streamlit default
- Labels: 0.85rem, uppercase, letter-spacing 0.025em

### Spacing
Consistent spacing via CSS custom properties:
- `--hg-space-xs`: 0.25rem
- `--hg-space-sm`: 0.5rem
- `--hg-space-md`: 1rem
- `--hg-space-lg`: 1.5rem
- `--hg-space-xl`: 2rem

### Border Radius
- Cards: 8px (`--hg-radius`)
- Small elements: 4px (`--hg-radius-sm`)
- Large containers: 12px (`--hg-radius-lg`)
- Progress bars: 999px (pill)

### Shadows
- Default: `0 1px 3px rgba(0,0,0,0.08)`
- Hover: `0 4px 6px rgba(0,0,0,0.07)`

## Responsive Behavior

### Streamlit Column Layout
The application uses Streamlit's built-in `st.columns()` which auto-adjusts:
- Desktop (1920px): Full multi-column layouts
- Tablet (768px): Columns collapse to 2 or 1
- Mobile (360px): Single column

### CSS Responsive Breakpoints
Global CSS in `src/ui/theme.py` includes:
- `@media (max-width: 768px)`: Metric values reduce font size
- `@media (max-width: 480px)`: Further metric size reduction

## Accessibility

### Implemented
- All badges include text labels (never color-only)
- Form fields have labels and help text
- `st.metric` has `help_text` for tooltips
- Focus-visible outline: `2px solid var(--hg-primary-light)`
- Keyboard navigation supported via Streamlit's built-in tab order
- Reduced motion: `@media (prefers-reduced-motion: reduce)` disables animations

### Limitations (Streamlit Framework)
- ARIA attributes are managed by Streamlit's rendering engine
- Screen reader support depends on Streamlit's semantic HTML output
- Custom modal/dialog accessibility limited by Streamlit framework

## Major UX Changes (Phase 18)

### 1. Unified Sidebar Navigation
**Before:** 9 of 15 pages had minimal sidebars (logout only). Users on risk_assessment, history, explainable_ai, etc. could not navigate without browser back button.

**After:** All 15 pages use `render_sidebar()` from `src/ui/sidebar.py`. Consistent navigation with role-based sections (Patient, Clinical Tools, Administration).

### 2. Global CSS Design System
**Before:** No global CSS. Only login/register had inline HTML styles. No design tokens.

**After:** `src/ui/theme.py` injects comprehensive CSS with design tokens, consistent styling for cards, metrics, buttons, forms, tables, alerts, expanders, and tabs.

### 3. Streamlit Theme Configuration
**Before:** No `.streamlit/config.toml`. Default Streamlit theme.

**After:** `.streamlit/config.toml` configures primary color (#1e3a8a), background, text color, and font family.

### 4. Security Fix: Traceback Exposure
**Before:** `explainable_ai.py` displayed raw Python tracebacks to users via `st.code(traceback.format_exc())`.

**After:** Tracebacks are logged server-side only. Users see generic error messages.

### 5. Shared Clinical Input Form
**Before:** Clinical input form (11 fields) was duplicated in `risk_assessment.py` and `explainable_ai.py`.

**After:** `src/ui/forms.py` provides `render_clinical_inputs()` — single source of truth.

## Theme Consistency

| Page | Global Theme | Shared Sidebar | Design System |
|---|---|---|---|
| login.py | ✅ | N/A | ✅ |
| register.py | ✅ | N/A | ✅ |
| dashboard.py | ✅ | ✅ | ✅ |
| risk_assessment.py | ✅ | ✅ | ✅ |
| explainable_ai.py | ✅ | ✅ | ✅ |
| history.py | ✅ | ✅ | ✅ |
| lifestyle_analyzer.py | ✅ | ✅ | ✅ |
| model_performance.py | ✅ | ✅ | ✅ |
| admin.py | ✅ | ✅ | ✅ |
| review.py | ✅ | ✅ | ✅ |
| security.py | ✅ | ✅ | ✅ |
| about.py | ✅ | ✅ | ✅ |
| patient_analytics.py | ✅ | ✅ | ✅ |
| analytics_dashboard.py | ✅ | ✅ | ✅ |
| model_monitoring.py | ✅ | ✅ | ✅ |

## Known Limitations

1. **Streamlit framework constraints**: ARIA landmarks, custom keyboard shortcuts, and advanced focus management are limited by Streamlit's rendering model
2. **Dark mode**: Not added per spec (do not add unless it can be implemented cleanly). The Streamlit theme config supports light mode only
3. **Mobile navigation**: Streamlit sidebar auto-collapses on mobile; no custom hamburger menu
4. **Charts**: All charts use Altair (consistent). Native `st.bar_chart`/`st.line_chart` remain in some pages as they are functionally adequate
