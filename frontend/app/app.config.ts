export default defineAppConfig({
  ui: {
    colors: {
      // Brand accent used across primary CTAs (was color="violet" pre-v4).
      primary: 'violet',
      // Manual utility classes throughout the app use the gray-* palette
      // (e.g. text-gray-900 dark:text-white); keep component-level neutral
      // colors (ghost buttons, badges) on the same palette for consistency.
      neutral: 'gray',
      // Preserves the exact hue used by the old color="orange" seat-limit alert.
      warning: 'orange',
    },
  },
})
