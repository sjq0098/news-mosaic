/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // 马卡龙主色调
        primary: {
          50: '#F0FDF4',
          100: '#D1E8F7',
          200: '#A8D8F0',
          300: '#7BC3E8',
          400: '#5BAEE2',
          500: '#3B9ADB',
          600: '#2B7BC7',
          700: '#1E5F9A',
          800: '#164A7A',
          900: '#0F3A5F',
        },
        // 马卡龙色系
        macaron: {
          pink: '#FADADD',
          'pink-light': '#FDF2F8',
          mint: '#D7F0E9',
          'mint-light': '#F0FDF4',
          yellow: '#FFF2CC',
          'yellow-light': '#FFFBEB',
          lavender: '#E8D5FF',
          'lavender-light': '#FAF5FF',
          cream: '#FFFEF7',
          warm: '#F5F5F0',
        },
        // 温暖灰色系
        gray: {
          50: '#F8F8F8',
          100: '#F0F4F8',
          200: '#E2E8F0',
          300: '#CBD5E0',
          400: '#A0AEC0',
          500: '#718096',
          600: '#4A5568',
          700: '#2D3748',
          800: '#1A202C',
          900: '#171923',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'bounce-gentle': 'bounceGentle 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        bounceGentle: {
          '0%, 100%': { transform: 'translateY(-5%)' },
          '50%': { transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio'),
  ],
  corePlugins: {
    preflight: false, // 禁用 Tailwind 的 preflight，避免与 Ant Design 冲突
  },
}; 