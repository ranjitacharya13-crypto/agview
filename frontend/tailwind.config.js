/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        vscode: {
          bg: '#0e0e10',
          sidebar: '#181818',
          activity: '#181818',
          editor: '#1f1f1f',
          panel: '#181818',
          border: '#2d2d30',
          borderLight: '#3a3d41',
          text: '#cccccc',
          textDim: '#858585',
          textBright: '#ffffff',
          accent: '#007acc',
          accentHover: '#005a9e',
          success: '#89d185',
          warning: '#cca700',
          error: '#f85149',
          listHover: '#2a2d2e',
          listActive: '#37373d'
        }
      },
      fontFamily: {
        mono: ['Cascadia Code', 'Consolas', 'Monaco', 'monospace'],
        sans: ['Segoe UI', 'Inter', 'system-ui', 'sans-serif']
      }
    },
  },
  plugins: [],
}
