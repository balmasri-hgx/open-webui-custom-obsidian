# Obsidian - Open WebUI Customization Summary

## Overview
This document summarizes all changes made to transform Open WebUI into "Obsidian" - an enterprise-grade frontend for n8n workflow agents.

---

## 1. Branding Changes

### Logo Updates
All instances of the Open WebUI logo have been replaced with HLX logos:

| File | Change |
|------|--------|
| `src/app.html` | Favicon and apple-touch-icon → `HLX-black.png` |
| `src/lib/components/chat/ProfileImage.svelte` | Default profile image → `HLX-white.png` |
| `src/lib/components/chat/Placeholder.svelte` | Chat placeholder logo → `HLX-white.png` |
| `src/lib/components/OnBoarding.svelte` | Onboarding logo → `HLX-dark.png` / `HLX-white.png` |
| `src/routes/auth/+page.svelte` | Login page logo → `HLX-black.png` |
| `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte` | Default profile → `HLX-white.png` |
| `src/routes/(app)/workspace/models/create/+page.svelte` | Model creation default → `HLX-white.png` |

### Logo Files Added
- `static/static/HLX-white.png` - White version for dark backgrounds
- `static/static/HLX-black.png` - Black version for light backgrounds
- `static/static/HLX-dark.png` - Dark version for light mode

### Text Branding
- App title changed from "Open WebUI" to "Obsidian" in `src/app.html`
- Sidebar brand name styled with Anurati font via `#sidebar-webui-name` CSS

---

## 2. Theme & Styling

### Custom Fonts
Added custom fonts in `static/static/assets/fonts/`:
- **Anurati** (`Anurati.otf`) - Used ONLY for brand elements (logo text, splash screen title)
- **Archivo** - Primary UI font
- **Inter** - Fallback UI font

### Color Palette
Defined in `static/static/custom.css`:

```css
:root {
  --accent-primary: #7d6c91;      /* Obsidian purple */
  --accent-secondary: #5b4965;    /* Darker purple */
  --accent-glow: rgba(125, 108, 145, 0.35);
  --accent-bright: #9889a8;       /* Lighter purple */
}
```

### Dark Mode Background
Sophisticated gradient replacing solid colors:
```css
.dark body {
  background: linear-gradient(145deg, #1a1721 0%, #201c29 50%, #1a1721 100%);
  background-attachment: fixed;
}
```

### Key Style Files
| File | Purpose |
|------|---------|
| `static/static/custom.css` | Main custom theme overrides |
| `src/app.css` | Global app styles, font declarations |
| `tailwind.config.js` | Tailwind color palette configuration |

---

## 3. Splash Screen

Location: `src/app.html`

### Features
- **Animated grid background** with perspective transform
- **Corner frame decorations** for futuristic look
- **HLX logo** with pulsing glow effect
- **"OBSIDIAN" title** in Anurati font with gradient text
- **"INTELLIGENCE PLATFORM" subtitle** in Segoe UI
- **Progress bar** with gradient fill and glow animation
- **"INITIALIZING SYSTEM" text** in Consolas monospace
- **Minimum 4-second display time** with smooth fade-out

### Animations
- `fadeIn`, `slideIn` - Element reveals
- `pulseGlow`, `logoGlowPulse` - Logo glow effects
- `titleGlow` - Title shadow animation
- `subtitleReveal` - Letter-spacing animation
- `progressBarFill`, `progressBarGlow` - Loading bar effects
- `gridFadeIn`, `gridPan` - Background grid animations

---

## 4. Login Page Enhancements

Location: `src/routes/auth/+page.svelte` and `static/static/custom.css`

### Features
- **Anurati branded title** - "OBSIDIAN" displayed in Anurati font with gradient text
- **Futuristic underscore-style inputs** - Clean line-based inputs instead of boxed fields
- **Animated focus states** - Purple gradient line animates on input focus
- **Autofill fix** - Browser autofill styled to match dark theme (prevents white backgrounds)
- **Gradient button** - Sign-in button with obsidian purple gradient and hover glow

### CSS Classes Added
| Class | Purpose |
|-------|---------|
| `.auth-title-brand` | Anurati font styling for "OBSIDIAN" title |
| `.futuristic-input-group` | Container for input + animated line |
| `.futuristic-input` | Transparent input with bottom border only |
| `.futuristic-input-line` | Animated gradient line on focus |
| `.futuristic-label` | Small uppercase label above inputs |
| `.futuristic-button` | Gradient button with hover effects |

---

## 5. Main Chat Interface

Location: `src/lib/components/chat/MessageInput.svelte` and `static/static/custom.css`

### Features
- **Plus pattern background** - Subtle repeating plus (+) pattern across the main chat area
- **Radial fade mask** - Pattern fades to transparent at center, visible at edges
- **Glassmorphic chat input** - Dark semi-transparent input with purple border glow
- **Custom `.obsidian-chat-input` class** - Added to MessageInput.svelte for clean styling
- **Gradient greeting text** - "Hello, [Name]" displays with purple gradient
- **Styled suggestion cards** - Dark glass effect with purple accent borders
- **Enhanced send button** - Purple gradient with glow on hover

### Chat Input Styling
```css
.obsidian-chat-input {
  background: rgba(22, 19, 32, 0.85);
  border: 1px solid rgba(155, 125, 184, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 40px rgba(155, 125, 184, 0.08);
  backdrop-filter: blur(20px);
}
```

### Plus Pattern Background
```css
body::after {
  background-image: url("data:image/svg+xml,..."); /* SVG plus pattern */
  mask-image: radial-gradient(ellipse at center, transparent 5%, black 70%);
}
```

---

## 6. Local Development Setup

### Hot Reload Configuration
For instant feedback on Svelte/TypeScript/CSS changes without Docker rebuilds:

**1. Start Docker backend only:**
```bash
docker compose up -d ollama open-webui
```

**2. Configure API proxy** (`vite.config.ts`):
```typescript
server: {
  proxy: {
    '/api': 'http://localhost:3000',
    '/ollama': 'http://localhost:3000',
    '/openai': 'http://localhost:3000',
  }
}
```

**3. Update constants** (`src/lib/constants.ts`):
```typescript
export const WEBUI_HOSTNAME = browser ? (dev ? `${location.hostname}:3000` : ``) : '';
```

**4. Run dev server:**
```bash
npm run dev
```

Access at: http://localhost:5173 (Vite with hot reload)

### What Requires Rebuilding
| Change Type | Rebuild Required? |
|-------------|-------------------|
| CSS in `static/static/` | No (volume mounted) |
| Svelte components | No (hot reload) |
| TypeScript files | No (hot reload) |
| `app.html` changes | **Yes** |
| Backend Python changes | **Yes** |
| Docker config changes | **Yes** |

---

## 8. n8n Webhook Integration (Implemented ✓)

> **Full documentation:** See [`docs/N8N_INTEGRATION.md`](docs/N8N_INTEGRATION.md)

### Features Implemented

| Feature | Status | Description |
|---------|--------|-------------|
| Slash Commands | ✓ | Type `/command` to trigger workflow forms |
| Workflow Button | ✓ | Bolt icon button in chat input bar |
| Form Rendering | ✓ | Dynamic forms with text, number, date, select, textarea, file fields |
| File Uploads | ✓ | Upload files to n8n workflows (sent as base64) |
| Workflow-Only Models | ✓ | Models that auto-trigger forms instead of LLM |
| Structured Responses | ✓ | Tables, key-value pairs, file downloads |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/webhooks/config/{model_id}` | GET | Get webhook form configuration |
| `/api/v1/webhooks/invoke` | POST | Trigger webhook with form data |
| `/api/v1/webhooks/invoke-with-files` | POST | Trigger webhook with file uploads |
| `/api/v1/webhooks/models` | GET | List all webhook-enabled models |

### Key Files

| File | Purpose |
|------|---------|
| `src/lib/apis/webhooks/index.ts` | Frontend API client |
| `src/lib/components/chat/WebhookFormModal.svelte` | Form modal component |
| `src/lib/components/chat/MessageInput/WorkflowsMenu.svelte` | Workflow dropdown menu |
| `src/lib/components/chat/WebhookResponseRenderer.svelte` | Response display component |
| `backend/open_webui/routers/webhooks.py` | Backend webhook router |
| `backend/open_webui/models/models.py` | WebhookConfig schema |

### Payload Sent to n8n

```json
{
  "user_id": "uuid",
  "user_email": "user@example.com",
  "user_name": "John Doe",
  "model_id": "workflow-model-id",
  "chat_id": "chat-uuid",
  "form_data": { "field1": "value1" },
  "files": [{ "name": "file.xlsx", "data": "base64..." }]
}
```

### Expected n8n Response

```json
{
  "message": "Success message",
  "file_url": "https://download-link",
  "file_name": "Report.xlsx",
  "data": [{ "col1": "val1" }]
}
```

---

## 9. File Structure

```
open-webui-custom/
├── static/static/
│   ├── custom.css              # Main theme overrides (login, chat, etc.)
│   ├── splash.css              # Splash screen styles
│   ├── HLX-white.png           # White logo
│   ├── HLX-black.png           # Black logo
│   ├── HLX-dark.png            # Dark logo
│   └── assets/fonts/
│       └── Anurati.otf         # Brand font
├── src/
│   ├── app.html                # Splash screen, favicon, font loading
│   ├── app.css                 # Global styles
│   ├── vite.config.ts          # Vite config with API proxy
│   └── lib/
│       ├── constants.ts        # API endpoints (modified for dev)
│       ├── apis/webhooks/      # Webhook API layer
│       └── components/
│           ├── chat/
│           │   ├── MessageInput.svelte  # Modified with .obsidian-chat-input
│           │   ├── ProfileImage.svelte
│           │   └── Placeholder.svelte
│           ├── workspace/Models/
│           │   └── ModelEditor.svelte
│           └── OnBoarding.svelte
├── tailwind.config.js          # Tailwind configuration
├── docker-compose.yaml         # Docker setup with volume mounts
└── OBSIDIAN_CHANGES.md         # This file
```

---

## 10. Development Workflow (Legacy)

### Quick CSS Changes (No Rebuild)
CSS files in `static/static/` are mounted as a Docker volume for live updates:
```yaml
# docker-compose.yaml
volumes:
  - ./static/static:/app/backend/static/static
```

### Full Rebuild (HTML/Svelte/JS Changes)
```bash
docker compose build --no-cache open-webui && docker compose up -d
```

### Local Development (Fastest)
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
./start.sh

# Terminal 2: Frontend
npm run dev
```

Access at: http://localhost:5173 (Vite dev server with hot reload)

---

## 11. Docker Configuration

### Key Settings
- Port: 3000 (mapped from container 8080)
- Ollama URL: http://ollama:11434
- Data persistence: `./data:/app/backend/data`

### Build Commands
```bash
# Full rebuild
docker compose build --no-cache open-webui

# Start services
docker compose up -d

# View logs
docker compose logs -f open-webui

# Stop services
docker compose down
```

---

## 12. Known Issues & Fixes

| Issue | Solution |
|-------|----------|
| npm peer dependency conflicts | Use `npm install --legacy-peer-deps` |
| `y-protocols/awareness` missing | Run `npm install y-protocols --legacy-peer-deps --save` |
| Docker permission denied | Run `sudo service docker start` and `newgrp docker` |
| Changes not appearing | Use `--no-cache` flag when building |
| Fonts not loading | Check path: `/static/assets/fonts/Anurati.otf` |
| Autofill messes with dark theme | Fixed with `-webkit-box-shadow` inset trick in custom.css |
| Chat input text delay | Under investigation - may be TipTap/ProseMirror related |

---

## 13. Next Steps

### Completed ✓
- [x] Complete n8n form rendering component
- [x] Implement webhook trigger on form submission
- [x] Add file upload support for n8n workflows
- [x] Handle n8n responses (Excel downloads, tables, etc.)
- [x] Add user session/context to webhook payloads
- [x] Add workflow-only model mode
- [x] Add workflow trigger button in chat

### Future Enhancements
- [ ] Real-time workflow status updates (WebSocket)
- [ ] Workflow execution history/audit log
- [ ] Scheduled/recurring workflow triggers
- [ ] Workflow chaining (one workflow triggers another)
- [ ] Admin dashboard for workflow analytics

---

*Last Updated: December 27, 2025 - Completed n8n Webhook Integration*

