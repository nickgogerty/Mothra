/**
 * Unit Tests for Dashboard Page
 * Tests all statistics display, charts, and interactions
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import Dashboard from '../Dashboard'
import * as apiClient from '../../api/client'

// Mock the API client
vi.mock('../../api/client')

// Helper to wrap component with required providers
const renderWithProviders = (component) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{component}</BrowserRouter>
    </QueryClientProvider>
  )
}

// Mock statistics data
const mockStatistics = {
  overview: {
    total_entities: 15234,
    total_emission_factors: 28456,
    total_sources: 45,
    active_sources: 38,
    validated_entities: 12987,
    avg_quality_score: 0.82,
    entity_types: 8,
    geographic_regions: 156,
    last_update: '2024-10-28T12:00:00Z',
  },
  quality_distribution: [
    { range: '0.8-1.0', count: 8234, percentage: 54.0 },
    { range: '0.6-0.8', count: 4567, percentage: 30.0 },
    { range: '0.4-0.6', count: 1823, percentage: 12.0 },
    { range: '0.2-0.4', count: 456, percentage: 3.0 },
    { range: '0.0-0.2', count: 154, percentage: 1.0 },
  ],
  entity_type_breakdown: [
    { entity_type: 'material', count: 6234, avg_quality: 0.85, validated: 5456, pending: 778 },
    { entity_type: 'process', count: 4567, avg_quality: 0.80, validated: 3890, pending: 677 },
    { entity_type: 'product', count: 2345, avg_quality: 0.78, validated: 1987, pending: 358 },
    { entity_type: 'energy', count: 1456, avg_quality: 0.83, validated: 1234, pending: 222 },
    { entity_type: 'transport', count: 632, avg_quality: 0.75, validated: 420, pending: 212 },
  ],
  source_breakdown: [
    {
      category: 'Government',
      active_sources: 12,
      total_entities: 5678,
      avg_quality: 0.88,
      last_updated: '2024-10-28T10:00:00Z',
    },
    {
      category: 'Industry',
      active_sources: 15,
      total_entities: 6234,
      avg_quality: 0.85,
      last_updated: '2024-10-27T15:30:00Z',
    },
  ],
  scope_distribution: [
    { scope: 1, count: 4567, percentage: 30.0 },
    { scope: 2, count: 6123, percentage: 40.2 },
    { scope: 3, count: 4544, percentage: 29.8 },
  ],
}

describe('Dashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial Render', () => {
    it('should render dashboard with page title and description', () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText(/Comprehensive overview of carbon emissions database/)).toBeInTheDocument()
    })

    it('should show loading skeletons while fetching data', () => {
      apiClient.getStatistics.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockStatistics), 1000))
      )

      renderWithProviders(<Dashboard />)

      // Skeletons are Material-UI components, check for their presence
      const skeletons = document.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe('Overview Statistics Cards', () => {
    it('should display all key metric cards with correct values', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        // Total Entities
        expect(screen.getByText('TOTAL ENTITIES')).toBeInTheDocument()
        expect(screen.getByText('15,234')).toBeInTheDocument()
        expect(screen.getByText('Carbon data points')).toBeInTheDocument()

        // Data Sources
        expect(screen.getByText('DATA SOURCES')).toBeInTheDocument()
        expect(screen.getByText('38')).toBeInTheDocument()
        expect(screen.getByText(/of 45 total/)).toBeInTheDocument()

        // Validated
        expect(screen.getByText('VALIDATED')).toBeInTheDocument()
        expect(screen.getByText('12,987')).toBeInTheDocument()

        // Average Quality
        expect(screen.getByText('AVG QUALITY')).toBeInTheDocument()
        expect(screen.getByText('82%')).toBeInTheDocument()
      })
    })

    it('should calculate and display validation percentage correctly', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        // (12987 / 15234) * 100 = 85.3%
        expect(screen.getByText(/85.3% of total/)).toBeInTheDocument()
      })
    })
  })

  describe('Quality Distribution Chart', () => {
    it('should display quality distribution chart with correct data', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Quality Score Distribution')).toBeInTheDocument()

        // Check if chart ranges are displayed
        expect(screen.getByText('0.8-1.0')).toBeInTheDocument()
        expect(screen.getByText('0.6-0.8')).toBeInTheDocument()
        expect(screen.getByText('0.4-0.6')).toBeInTheDocument()
        expect(screen.getByText('0.2-0.4')).toBeInTheDocument()
        expect(screen.getByText('0.0-0.2')).toBeInTheDocument()
      })
    })

    it('should render bar chart component', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        // Recharts creates SVG elements
        const svgElements = document.querySelectorAll('svg')
        expect(svgElements.length).toBeGreaterThan(0)
      })
    })
  })

  describe('GHG Scope Distribution', () => {
    it('should display scope distribution with all scopes', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('GHG Scope Coverage')).toBeInTheDocument()

        // Check all scopes are displayed
        expect(screen.getByText('Scope 1')).toBeInTheDocument()
        expect(screen.getByText('Direct Emissions')).toBeInTheDocument()

        expect(screen.getByText('Scope 2')).toBeInTheDocument()
        expect(screen.getByText('Indirect Energy')).toBeInTheDocument()

        expect(screen.getByText('Scope 3')).toBeInTheDocument()
        expect(screen.getByText('Value Chain')).toBeInTheDocument()
      })
    })

    it('should display scope percentages correctly', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/4,567.*30.0%/)).toBeInTheDocument()
        expect(screen.getByText(/6,123.*40.2%/)).toBeInTheDocument()
        expect(screen.getByText(/4,544.*29.8%/)).toBeInTheDocument()
      })
    })
  })

  describe('Entity Type Breakdown', () => {
    it('should display entity type breakdown section', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Entity Type Breakdown')).toBeInTheDocument()

        // Check entity types are displayed
        expect(screen.getByText('material')).toBeInTheDocument()
        expect(screen.getByText('process')).toBeInTheDocument()
        expect(screen.getByText('product')).toBeInTheDocument()
        expect(screen.getByText('energy')).toBeInTheDocument()
        expect(screen.getByText('transport')).toBeInTheDocument()
      })
    })

    it('should display entity counts for each type', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('6,234')).toBeInTheDocument() // material
        expect(screen.getByText('4,567')).toBeInTheDocument() // process
        expect(screen.getByText('2,345')).toBeInTheDocument() // product
        expect(screen.getByText('1,456')).toBeInTheDocument() // energy
        expect(screen.getByText('632')).toBeInTheDocument() // transport
      })
    })

    it('should display validation counts and average quality', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/5456 validated/)).toBeInTheDocument()
        expect(screen.getByText(/Avg Quality: 85%/)).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should display error message when API call fails', async () => {
      const errorMessage = 'Unable to connect to the server'
      apiClient.getStatistics.mockRejectedValue(new Error(errorMessage))

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Unable to Load Dashboard')).toBeInTheDocument()
        expect(screen.getByText(errorMessage)).toBeInTheDocument()
        expect(
          screen.getByText(/Please ensure the MOTHRA API backend is running and accessible/)
        ).toBeInTheDocument()
      })
    })

    it('should display retry button on error', async () => {
      apiClient.getStatistics.mockRejectedValue(new Error('Connection failed'))

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        const retryButton = screen.getByRole('button', { name: /Retry Connection/i })
        expect(retryButton).toBeInTheDocument()
        expect(retryButton).toBeEnabled()
      })
    })

    it('should retry fetching data when retry button is clicked', async () => {
      const mockGetStats = vi
        .fn()
        .mockRejectedValueOnce(new Error('Connection failed'))
        .mockResolvedValueOnce(mockStatistics)

      apiClient.getStatistics.mockImplementation(mockGetStats)

      const user = userEvent.setup()
      renderWithProviders(<Dashboard />)

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByText('Unable to Load Dashboard')).toBeInTheDocument()
      })

      const retryButton = screen.getByRole('button', { name: /Retry Connection/i })
      await user.click(retryButton)

      // Should show loading state
      expect(retryButton).toHaveTextContent('Retrying...')

      // Should succeed on retry
      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
        expect(screen.getByText('15,234')).toBeInTheDocument()
      })

      expect(mockGetStats).toHaveBeenCalledTimes(2)
    })
  })

  describe('Data Formatting', () => {
    it('should format large numbers with commas', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        // Should display 15,234 not 15234
        expect(screen.getByText('15,234')).toBeInTheDocument()
        expect(screen.getByText('12,987')).toBeInTheDocument()
      })
    })

    it('should format percentages to one decimal place', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        // Validation percentage: (12987/15234) * 100 = 85.3%
        expect(screen.getByText(/85.3% of total/)).toBeInTheDocument()
      })
    })

    it('should format quality scores as percentages', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        // 0.82 * 100 = 82%
        expect(screen.getByText('82%')).toBeInTheDocument()
        // 0.85 * 100 = 85%
        expect(screen.getByText(/Avg Quality: 85%/)).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Behavior', () => {
    it('should render all grid items', async () => {
      apiClient.getStatistics.mockResolvedValue(mockStatistics)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        // Check that grid containers exist
        const grids = document.querySelectorAll('.MuiGrid-container')
        expect(grids.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Data Integrity', () => {
    it('should handle missing or null data gracefully', async () => {
      const incompleteStats = {
        overview: {
          total_entities: 0,
          total_emission_factors: 0,
          total_sources: 0,
          active_sources: 0,
          validated_entities: 0,
          avg_quality_score: 0,
          entity_types: 0,
          geographic_regions: 0,
          last_update: '2024-10-28T12:00:00Z',
        },
        quality_distribution: [],
        entity_type_breakdown: [],
        source_breakdown: [],
        scope_distribution: [],
      }

      apiClient.getStatistics.mockResolvedValue(incompleteStats)

      renderWithProviders(<Dashboard />)

      await waitFor(() => {
        // Should render with 0 values
        expect(screen.getByText('0')).toBeInTheDocument()
        expect(screen.getByText('0%')).toBeInTheDocument()
      })
    })
  })
})
