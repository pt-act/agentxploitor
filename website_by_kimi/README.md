# Agentxploitor Marketing Website

A high-converting waitlist and marketing landing page with comprehensive documentation for Agentxploitor - the first autonomous AI security agent with visual exploit verification.

## Features

### Marketing Site
- **Hero Section** - Compelling headline with hero image from assets
- **Features Grid** - 6 key differentiators with comparison table
- **How It Works** - 6-step workflow with interactive visuals
- **Live Terminal Demo** - Interactive demo showing real agent output
- **Waitlist Form** - Email capture with role selection and benefits
- **Documentation** - Full docs site accessible from navbar

### Documentation Site (`/docs`)
- **Introduction** - What is Agentxploitor and key concepts
- **Quick Start** - Get running in under 5 minutes
- **Demo Script** - Recording guide for video demos
- **Autonomy Philosophy** - Agent vs Bot - understanding true autonomy
- **Visual Verification** - How browser perception enables proof
- **Self-Evaluation** - AI judging its own success
- **Security Checklist** - Pre-deployment security audit
- **Accessibility** - Testing guide for screen readers
- **Audit Report** - Academic security evaluation
- **Final Status** - Production readiness assessment
- **Architecture** - System design and components
- **API Reference** - Agent and model interfaces

## Tech Stack

- Next.js 14 (Static Export)
- React 18 + TypeScript
- Tailwind CSS
- Framer Motion (animations)
- Lucide React (icons)

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Deployment

### Option 1: Netlify Drag & Drop (Easiest)

1. Run `npm run build` locally
2. Drag and drop the `dist/` folder to [Netlify Drop](https://app.netlify.com/drop)
3. Your site is live!

### Option 2: Netlify with Git Integration

1. Push code to GitHub
2. Connect repo to Netlify
3. Set build settings:
   - **Build command:** `npm run build`
   - **Publish directory:** `dist`
4. Deploy!

### Option 3: Other Static Hosts

Deploy the `dist` folder to any static hosting:
- Vercel
- Cloudflare Pages
- GitHub Pages
- AWS S3 + CloudFront

## Structure

```
website_by_kimi/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Root layout with metadata
│   │   ├── page.tsx             # Main page composition
│   │   ├── globals.css          # Global styles + Tailwind
│   │   └── docs/                # Documentation pages
│   │       ├── layout.tsx       # Docs layout with sidebar
│   │       ├── content.ts       # Docs metadata
│   │       └── [[...slug]]/     # Dynamic docs pages
│   │           ├── page.tsx
│   │           └── DocsClient.tsx
│   ├── components/
│   │   ├── navbar.tsx           # Navigation with logo
│   │   ├── hero.tsx             # Hero section + hero.png
│   │   ├── features.tsx         # Feature cards + comparison
│   │   ├── how-it-works.tsx     # 6-step workflow
│   │   ├── demo.tsx             # Live terminal demo
│   │   ├── live-terminal-demo.tsx # Interactive terminal
│   │   ├── waitlist.tsx         # Email capture form
│   │   └── footer.tsx           # Footer with icon
│   └── lib/
│       └── utils.ts             # Utilities + config
├── public/                      # Static assets
│   ├── hero.png                 # Hero section image
│   ├── icon.png                 # Favicon + footer icon
│   ├── logo.png                 # Navbar logo
│   └── _redirects               # Netlify SPA redirect rules
├── netlify.toml                 # Netlify configuration
├── dist/                        # Static export output (deploy this!)
│   ├── index.html               # Homepage
│   ├── _redirects               # SPA routing rules
│   ├── docs.html                # Docs index
│   ├── *.png                    # Copied assets
│   └── docs/                    # All docs pages
├── package.json
├── tailwind.config.ts
├── next.config.js
└── tsconfig.json
```

## Assets

Assets are copied from `/Users/rna/Desktop/ECOSYSTEM/CryptoHexS-AI/bounty/agentxploitor/assets/`:

| Asset | Usage | Location |
|-------|-------|----------|
| `hero.png` | Hero section showcase image | Homepage |
| `icon.png` | Favicon, footer icon, docs mobile header | All pages |
| `logo.png` | Navbar logo, docs sidebar | All pages |

## Key Components

### Live Terminal Demo
The demo section features an interactive terminal that simulates actual agent output:
- Play/Pause/Reset controls
- Real-time log output with color coding
- 37-step demo showing full workflow
- Stats display (steps, execution time, confidence)

### Documentation
Docs are generated from project documentation files:
- `docs/QUICKSTART.md` → Quick Start page
- `docs/AGENT_AUTONOMY_PHILOSOPHY.md` → Autonomy Philosophy
- `docs/DEMO_SCRIPT.md` → Demo Script
- `docs/FINAL_STATUS.md` → Final Status
- `docs/SECURITY_CHECKLIST.md` → Security Checklist
- `docs/ACCESSIBILITY_TESTING.md` → Accessibility
- Security audit reports → Audit Report page

## Troubleshooting

### 404 Errors on Netlify
The `_redirects` file in `public/` handles SPA routing. Contents:
```
/* /index.html 200
```

This ensures all routes serve the index.html (required for client-side routing).

### CSS Issues
Ensure Tailwind CSS is properly configured:
- `tailwind.config.ts` uses ES module export
- `globals.css` imports Tailwind directives
- PostCSS is configured

### Hydration Errors
Don't use `window` object during SSR. Use `useEffect` for client-side only code.

## Customization

- Update `src/lib/utils.ts` for site config
- Modify colors in `tailwind.config.ts`
- Edit docs content in `src/app/docs/[[...slug]]/DocsClient.tsx`
- Connect waitlist form to your backend/API
- Replace assets in `public/` folder

## Navigation

- **Docs link** is in the main navbar (visible on all pages)
- Mobile-responsive menu with Docs access
- Sidebar navigation in docs with search

---

Built for Agentxploitor | Superteam Bounty 2
