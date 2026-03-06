# Accessibility Testing Guide

## Screen Reader Testing Checklist

### VoiceOver (macOS)

1. **Enable VoiceOver**: `Cmd + F5`
2. **Navigate to Dashboard**: Use `VO + Arrow Keys`
3. **Test Items**:
   - [ ] Page landmarks (banner, main, contentinfo)
   - [ ] Heading hierarchy (h1 → h2 → h3)
   - [ ] Form labels and associations
   - [ ] Button and link names
   - [ ] Live regions for dynamic content

### NVDA (Windows)

1. **Start NVDA**: `Ctrl + Alt + N`
2. **Navigate Elements**: `Tab`, `Shift + Tab`
3. **Test Items**:
   - [ ] Focus indicators visible
   - [ ] ARIA roles correct
   - [ ] Dynamic updates announced
   - [ ] Error messages announced

### Testing Commands

```bash
# VoiceOver
VO + Cmd + H     # Navigate by heading
VO + Cmd + J      # Navigate to next landmark
VO + Cmd + L      # Navigate to next link
VO + Cmd + X      # Navigate to next table
VO + Space        # Activate button

# NVDA
NVDA + T          # Read title
NVDA + H          # Navigate by heading
NVDA + D          # Navigate to landmark
Tab               # Move through interactive elements
```

## Automated Testing

```bash
# Install axe-core
npm install @axe-core/cli

# Run accessibility tests
axe http://localhost:3000 --exit

# Run with specific standards
axe http://localhost:3000 --tags wcag2a,wcag2aa,section508
```

## Manual Testing Checklist

### Focus Management
- [ ] All interactive elements focusable
- [ ] Focus order logical
- [ ] Focus visible at all times
- [ ] No focus traps

### Keyboard Navigation
- [ ] All functions accessible via keyboard
- [ ] No keyboard traps
- [ ] Escape closes modals
- [ ] Enter/Space activates buttons
- [ ] Arrow keys navigate menus

### Screen Reader
- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Error messages announced
- [ ] Dynamic content announced
- [ ] Headings in logical order

### Visual
- [ ] Color contrast 4.5:1 minimum
- [ ] Text resizable to 200%
- [ ] No content relies on color alone
- [ ] Focus indicators visible
