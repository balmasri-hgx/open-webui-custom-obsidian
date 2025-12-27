import typography from '@tailwindcss/typography';
import containerQueries from '@tailwindcss/container-queries';

/** @type {import('tailwindcss').Config} */
export default {
	darkMode: 'class',
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				/* Clean neutral grays for UI - with subtle obsidian undertone */
				gray: {
					50: '#f8f7fa',
					100: '#f0eef2',
					200: '#e4e1e8',
					300: '#cdc8d4',
					400: '#a9a1b4',
					500: '#857b94',
					600: '#6b6079',
					700: '#564c65',
					800: '#3d354b',   /* Obsidian tone starts here */
					850: '#2e293a',
					900: '#252131',
					950: '#1a1721'
				},
				/* Obsidian accent palette */
				obsidian: {
					50: '#f0edf3',
					100: '#d8d2de',
					200: '#b8aec4',
					300: '#9889a8',
					400: '#7d6c91',
					500: '#62507a',
					600: '#5b4965',
					700: '#4a3d55',
					800: '#3d354b',
					900: '#2e293a',
					950: '#1a1721'
				}
			},
			typography: {
				DEFAULT: {
					css: {
						pre: false,
						code: false,
						'pre code': false,
						'code::before': false,
						'code::after': false
					}
				}
			},
			padding: {
				'safe-bottom': 'env(safe-area-inset-bottom)'
			},
			transitionProperty: {
				width: 'width'
			}
		}
	},
	plugins: [typography, containerQueries]
};
