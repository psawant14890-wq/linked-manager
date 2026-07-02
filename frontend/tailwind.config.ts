import type { Config } from "tailwindcss";

/**
 * Design tokens for LinkedIQ.
 *
 * The signature idea: priority score is the product's core concept, so it
 * becomes the UI's recurring visual motif -- a thin colored "priority rail"
 * appears next to inbox items, report stat blocks, and dashboard cards,
 * using the same five-color scale everywhere (recruiter/collaboration/
 * genuine/general/spam). Nothing else competes with it for color.
 *
 * Type: Fraunces (display serif, used sparingly for headings/hero numbers)
 * + Inter (body/UI) + JetBrains Mono (stats, counts, timestamps -- this is
 * a data-and-reports product, numbers deserve a distinct voice from prose).
 */
const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        border: "hsl(var(--border))",
        ring: "hsl(var(--ring))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        priority: {
          recruiter: "hsl(var(--priority-recruiter))",
          collaboration: "hsl(var(--priority-collaboration))",
          genuine: "hsl(var(--priority-genuine))",
          general: "hsl(var(--priority-general))",
          spam: "hsl(var(--priority-spam))",
        },
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "ui-serif", "Georgia", "serif"],
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
};

export default config;
