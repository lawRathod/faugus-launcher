/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  theme: {
    extend: {
      colors: {
        surface: {
          base:   "var(--surface-base)",
          elevated: "var(--surface-elevated)",
          card:   "var(--surface-card)",
          border: "var(--surface-border)",
          hover:  "var(--surface-hover)",
        },
        // Keep legacy surface-XXX aliases for compatibility
        950: "var(--surface-base)",
        900: "var(--surface-elevated)",
        800: "var(--surface-card)",
        700: "var(--surface-border)",
        600: "var(--surface-hover)",
      },
      textColor: {
        white: "var(--text-primary)",
        gray: {
          200: "var(--text-primary)",
          300: "var(--text-primary)",
          400: "var(--text-secondary)",
          500: "var(--text-muted)",
          600: "var(--text-muted)",
        },
      },
      borderColor: {
        surface: {
          800: "var(--surface-border)",
          700: "var(--surface-border)",
        },
      },
    },
  },
  plugins: [],
};
