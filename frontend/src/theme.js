import { createTheme } from '@mui/material/styles'

/**
 * Swiss Minimal Theme
 * Inspired by: Tufte (data clarity), Swiss Design (minimalism), Nielsen (usability)
 *
 * Principles:
 * - High data-ink ratio (Tufte)
 * - Generous white space (Swiss)
 * - Readable typography (Nielsen)
 * - Limited color palette
 * - Clear visual hierarchy
 */

const theme = createTheme({
  // Swiss typography - clean, highly legible
  typography: {
    fontFamily: '"Inter", "Helvetica Neue", Arial, sans-serif',
    fontSize: 14,
    fontWeightLight: 300,
    fontWeightRegular: 400,
    fontWeightMedium: 500,
    fontWeightBold: 600,

    h1: {
      fontSize: '2.5rem',
      fontWeight: 300,
      letterSpacing: '-0.02em',
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 300,
      letterSpacing: '-0.01em',
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 400,
      letterSpacing: '-0.01em',
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      letterSpacing: '0.00938em',
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
      letterSpacing: '0.01071em',
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.4,
      letterSpacing: '0.03333em',
      color: '#666',
    },
    overline: {
      fontSize: '0.625rem',
      fontWeight: 600,
      letterSpacing: '0.08333em',
      textTransform: 'uppercase',
      lineHeight: 2.5,
    },
  },

  // Minimal color palette - mostly grayscale with one accent
  palette: {
    mode: 'light',
    primary: {
      main: '#1a1a1a',      // Near black (Swiss tradition)
      light: '#4a4a4a',
      dark: '#000000',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#2563eb',      // Minimal blue accent for interactive elements
      light: '#60a5fa',
      dark: '#1e40af',
      contrastText: '#ffffff',
    },
    error: {
      main: '#dc2626',
      light: '#f87171',
      dark: '#991b1b',
    },
    warning: {
      main: '#f59e0b',
      light: '#fbbf24',
      dark: '#b45309',
    },
    success: {
      main: '#059669',
      light: '#34d399',
      dark: '#047857',
    },
    info: {
      main: '#0891b2',
      light: '#22d3ee',
      dark: '#0e7490',
    },
    grey: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#e5e5e5',
      300: '#d4d4d4',
      400: '#a3a3a3',
      500: '#737373',
      600: '#525252',
      700: '#404040',
      800: '#262626',
      900: '#171717',
    },
    background: {
      default: '#ffffff',
      paper: '#fafafa',
    },
    text: {
      primary: '#171717',
      secondary: '#525252',
      disabled: '#a3a3a3',
    },
    divider: '#e5e5e5',
  },

  // Spacing based on 8px grid (Swiss design principle)
  spacing: 8,

  // Shape - minimal border radius
  shape: {
    borderRadius: 2,
  },

  // Component customization
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          // Smooth scrolling
          scrollBehavior: 'smooth',
        },
      },
    },

    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          letterSpacing: '0.00938em',
          borderRadius: 2,
          padding: '8px 24px',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
        outlined: {
          borderWidth: 1,
          '&:hover': {
            borderWidth: 1,
          },
        },
      },
    },

    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        elevation1: {
          boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        },
        elevation2: {
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        },
        elevation3: {
          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        },
      },
    },

    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          border: '1px solid #e5e5e5',
          boxShadow: 'none',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05)',
          },
        },
      },
    },

    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: '#ffffff',
            transition: 'border-color 0.2s ease-in-out',
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: '#a3a3a3',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderWidth: 1,
              borderColor: '#171717',
            },
          },
        },
      },
    },

    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          fontWeight: 500,
          fontSize: '0.75rem',
          letterSpacing: '0.01em',
        },
        outlined: {
          borderWidth: 1,
        },
      },
    },

    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid #f5f5f5',
          padding: '16px',
        },
        head: {
          fontWeight: 600,
          fontSize: '0.75rem',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: '#525252',
          borderBottom: '2px solid #e5e5e5',
        },
      },
    },

    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#171717',
          fontSize: '0.75rem',
          fontWeight: 400,
          padding: '8px 12px',
        },
      },
    },

    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 2,
          height: 6,
        },
      },
    },

    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: '#f5f5f5',
        },
      },
    },
  },

  // Transitions - subtle and fast
  transitions: {
    duration: {
      shortest: 150,
      shorter: 200,
      short: 250,
      standard: 300,
      complex: 375,
      enteringScreen: 225,
      leavingScreen: 195,
    },
    easing: {
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
    },
  },
})

export default theme
