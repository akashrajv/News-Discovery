/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        mongo: {
          dark: '#001E2B',
          forest: '#00684A',
          green: '#00ED64',
          slate: '#F9FBFA',
          border: '#E8EDEB',
          subtle: '#5C6F84',
          card: '#FFFFFF',
        }
      }
    },
  },
  plugins: [],
}
