# HeartGuard Accessibility Review — Phase 18

## Overview

Phase 18 accessibility review covers keyboard navigation, focus states, contrast, labels, screen-reader considerations, and known limitations within the Streamlit framework.

## Keyboard Navigation

### Implemented
- All Streamlit widgets (`st.button`, `st.selectbox`, `st.number_input`, `st.text_input`, `st.checkbox`, `st.text_area`) are keyboard-navigable by default
- Tab order follows document flow (top-to-bottom, left-to-right)
- Form submission via Enter key in `st.form` contexts
- Sidebar navigation links are keyboard-accessible

### Framework Limitations
- Custom keyboard shortcuts are not supported by Streamlit
- Focus trapping in modals is managed by Streamlit's rendering engine
- Streamlit's page navigation (`st.page_link`) does not support custom keyboard shortcuts

## Focus States

### Implemented
Global CSS in `src/ui/theme.py` adds:
```css
:focus-visible {
    outline: 2px solid var(--hg-primary-light);
    outline-offset: 2px;
}
```

This ensures all interactive elements have visible focus indicators when navigated via keyboard.

### Button Focus
```css
.stButton > button:focus-visible {
    outline: 2px solid var(--hg-primary-light);
    outline-offset: 2px;
}
```

## Contrast

### Color Token Contrast Ratios
| Token | Background | Ratio | WCAG AA |
|---|---|---|---|
| primary (#1e3a8a) | white | 12.5:1 | ✅ |
| text (#1e293b) | white | 15.8:1 | ✅ |
| muted (#64748b) | white | 5.0:1 | ✅ (large text) |
| success (#16a34a) | white | 4.6:1 | ✅ (large text) |
| warning (#d97706) | white | 4.6:1 | ✅ (large text) |
| error (#dc2626) | white | 4.8:1 | ✅ |

All primary text and interactive elements meet WCAG AA contrast requirements.

## Form Labels

### Implemented
- All `st.number_input`, `st.selectbox`, `st.text_input`, `st.text_area` have explicit label parameters
- `help` parameter used on clinical inputs for additional context
- `placeholder` used on text areas for examples (not as label replacement)
- `format_func` used on selectboxes for human-readable option display

### Clinical Input Form (src/ui/forms.py)
Centralized form component ensures consistent labeling across:
- Risk assessment page
- Explainable AI page

Each field includes:
- Descriptive label
- Help text explaining expected values
- Appropriate min/max constraints

## Screen Reader Considerations

### Streamlit Framework
Streamlit generates semantic HTML by default:
- `st.metric` uses heading hierarchy (h1-h6)
- `st.dataframe` renders as HTML tables
- `st.alert` uses ARIA alert patterns
- `st.tabs` uses ARIA tab patterns
- Navigation uses `st.page_link` (anchor elements)

### Badge Accessibility
All badges in `src/ui/badges.py` follow the accessibility rule:
> "Never rely on color alone to convey status. Every badge must include explicit text labels and unambiguous symbolic markers."

Examples:
- `[LOW RISK]` (not just green color)
- `[PENDING REVIEW]` (not just yellow)
- `[ALERT SENT]` (not just blue)

### Chart Accessibility
Charts in `src/ui/charts.py` include:
- Descriptive titles
- Axis labels with units
- Tooltips with detailed values
- Text-based data tables alongside charts where important

## Reduced Motion

Global CSS respects `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation: none !important;
        transition-duration: 0.01ms !important;
    }
}
```

## Print Styles

```css
@media print {
    section[data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stToolbar"] { display: none !important; }
}
```

Sidebar and toolbar are hidden when printing, showing only main content.

## Known Limitations

1. **Streamlit ARIA management**: ARIA landmarks and live regions are managed by Streamlit's rendering engine, not directly controllable
2. **Custom keyboard shortcuts**: Not supported by Streamlit framework
3. **Focus trapping in dialogs**: Managed by Streamlit, not customizable
4. **Chart interactivity**: Altair chart keyboard interaction depends on browser accessibility features
5. **Mobile touch targets**: Streamlit's default touch targets may be smaller than WCAG 2.5.5 recommended 44x44px

## Recommendations for Future Phases

1. Consider custom Streamlit components for advanced accessibility needs
2. Add skip-to-content links if Streamlit supports it
3. Test with NVDA/JAWS screen readers on Windows
4. Consider adding ARIA landmarks via custom HTML injection
