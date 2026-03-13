/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',   // blue-600
        secondary: '#475569', // slate-600
        success: '#22c55e',   // green-500
        warning: '#eab308',   // yellow-500
        danger: '#ef4444',    // red-500
      },
    },
  },
  plugins: [],
}
