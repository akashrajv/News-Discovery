/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        linkedin: {
          blue: '#0A66C2',       // Classic LinkedIn Blue
          hover: '#004182',      // LinkedIn Blue Dark Hover
          active: '#09223B',     // LinkedIn Blue Pressed
          light: '#EBF4FD',      // Light ice blue for active tabs/cards/badges
          lighter: '#F3F8FD',    // Subtle blue background
          border: '#D0E3F5',     // Soft blue border
          dark: '#1D2226',       // LinkedIn Primary Text
          subtle: '#57687A',     // LinkedIn Subdued Gray-Blue Text
          bg: '#F3F2F0',         // LinkedIn Canvas Background
          card: '#FFFFFF',       // Pure White Card
        },
        mongo: {
          dark: '#1D2226',
          forest: '#0A66C2',
          green: '#0A66C2',
          slate: '#F3F2F0',
          border: '#E0DFDC',
          subtle: '#57687A',
          card: '#FFFFFF',
        }
      }
    },
  },
  plugins: [],
}
