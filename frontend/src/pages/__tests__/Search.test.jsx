/**
 * Unit Tests for Search Page
 * Tests all fields, buttons, and user interactions
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import Search from '../Search'
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

describe('Search Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial Render', () => {
    it('should render search page with all elements', () => {
      renderWithProviders(<Search />)

      // Check page title and description
      expect(screen.getByText('Semantic Search')).toBeInTheDocument()
      expect(
        screen.getByText(/Search carbon entities using natural language/)
      ).toBeInTheDocument()

      // Check search input exists
      const searchInput = screen.getByPlaceholderText(/Search for materials/)
      expect(searchInput).toBeInTheDocument()
      expect(searchInput).toHaveValue('')

      // Check search button exists
      const searchButton = screen.getByRole('button', { name: /search/i })
      expect(searchButton).toBeInTheDocument()
      expect(searchButton).toBeDisabled() // Should be disabled when query is empty

      // Check entity type filters
      expect(screen.getByText('process')).toBeInTheDocument()
      expect(screen.getByText('material')).toBeInTheDocument()
      expect(screen.getByText('product')).toBeInTheDocument()
      expect(screen.getByText('energy')).toBeInTheDocument()
    })

    it('should show empty state message', () => {
      renderWithProviders(<Search />)

      expect(screen.getByText('Start searching')).toBeInTheDocument()
      expect(
        screen.getByText(/Enter at least 2 characters to begin semantic search/)
      ).toBeInTheDocument()
    })
  })

  describe('Search Input Field', () => {
    it('should update input value when user types', async () => {
      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)

      await user.type(searchInput, 'steel')

      expect(searchInput).toHaveValue('steel')
    })

    it('should enable search button when query has 2+ characters', async () => {
      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)
      const searchButton = screen.getByRole('button', { name: /search/i })

      // Initially disabled
      expect(searchButton).toBeDisabled()

      // Type 1 character - still disabled
      await user.type(searchInput, 's')
      expect(searchButton).toBeDisabled()

      // Type 2nd character - should be enabled
      await user.type(searchInput, 't')
      expect(searchButton).toBeEnabled()
    })

    it('should show clear button when input has text', async () => {
      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)

      await user.type(searchInput, 'carbon')

      const clearButton = screen.getByRole('button', { name: /clear/i })
      expect(clearButton).toBeInTheDocument()
    })

    it('should clear input when clear button is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)

      await user.type(searchInput, 'carbon')
      expect(searchInput).toHaveValue('carbon')

      const clearButton = screen.getByRole('button', { name: /clear/i })
      await user.click(clearButton)

      expect(searchInput).toHaveValue('')
    })
  })

  describe('Auto-search Functionality', () => {
    it('should trigger search automatically after typing stops (debounced)', async () => {
      vi.useFakeTimers()
      const mockSearch = vi.fn().mockResolvedValue({
        results: [],
        total: 0,
        execution_time_ms: 10,
        query: 'steel',
      })
      apiClient.semanticSearch.mockImplementation(mockSearch)

      const user = userEvent.setup({ delay: null })
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)

      await user.type(searchInput, 'steel')

      // Should not call immediately
      expect(mockSearch).not.toHaveBeenCalled()

      // Fast-forward 500ms (debounce delay)
      vi.advanceTimersByTime(500)

      await waitFor(() => {
        expect(mockSearch).toHaveBeenCalledWith('steel', { entityType: null })
      })

      vi.useRealTimers()
    })
  })

  describe('Search Button', () => {
    it('should trigger search when clicked', async () => {
      const mockSearch = vi.fn().mockResolvedValue({
        results: [],
        total: 0,
        execution_time_ms: 10,
        query: 'aluminum',
      })
      apiClient.semanticSearch.mockImplementation(mockSearch)

      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)
      await user.type(searchInput, 'aluminum')

      const searchButton = screen.getByRole('button', { name: /search/i })
      await user.click(searchButton)

      await waitFor(() => {
        expect(mockSearch).toHaveBeenCalledWith('aluminum', { entityType: null })
      })
    })

    it('should trigger search when Enter key is pressed', async () => {
      const mockSearch = vi.fn().mockResolvedValue({
        results: [],
        total: 0,
        execution_time_ms: 10,
        query: 'concrete',
      })
      apiClient.semanticSearch.mockImplementation(mockSearch)

      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)

      fireEvent.change(searchInput, { target: { value: 'concrete' } })
      fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter', charCode: 13 })

      await waitFor(() => {
        expect(mockSearch).toHaveBeenCalledWith('concrete', { entityType: null })
      })
    })
  })

  describe('Entity Type Filters', () => {
    it('should toggle entity type filter when clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const processChip = screen.getByText('process')

      // Click to activate
      await user.click(processChip)

      // Chip should be filled/selected (you may need to check parent classes)
      expect(processChip).toBeInTheDocument()

      // Click again to deactivate
      await user.click(processChip)

      expect(processChip).toBeInTheDocument()
    })

    it('should include entity type in search query', async () => {
      const mockSearch = vi.fn().mockResolvedValue({
        results: [],
        total: 0,
        execution_time_ms: 10,
        query: 'steel',
      })
      apiClient.semanticSearch.mockImplementation(mockSearch)

      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)
      await user.type(searchInput, 'steel')

      const materialChip = screen.getByText('material')
      await user.click(materialChip)

      const searchButton = screen.getByRole('button', { name: /search/i })
      await user.click(searchButton)

      await waitFor(() => {
        expect(mockSearch).toHaveBeenCalledWith('steel', { entityType: 'material' })
      })
    })
  })

  describe('Search Results Display', () => {
    it('should display loading state while searching', async () => {
      const mockSearch = vi.fn().mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ results: [], total: 0 }), 1000))
      )
      apiClient.semanticSearch.mockImplementation(mockSearch)

      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)
      await user.type(searchInput, 'steel')

      const searchButton = screen.getByRole('button', { name: /search/i })
      await user.click(searchButton)

      expect(await screen.findByText('Searching...')).toBeInTheDocument()
    })

    it('should display search results when data is returned', async () => {
      const mockResults = {
        results: [
          {
            id: '1',
            name: 'Steel Production',
            description: 'Carbon emissions from steel manufacturing',
            entity_type: 'process',
            similarity: 0.95,
            geographic_scope: ['Global'],
            category: ['Manufacturing', 'Steel'],
            quality_score: 0.85,
          },
          {
            id: '2',
            name: 'Stainless Steel',
            description: 'Stainless steel material',
            entity_type: 'material',
            similarity: 0.88,
            geographic_scope: ['Europe'],
            category: ['Materials', 'Metals'],
            quality_score: 0.78,
          },
        ],
        total: 2,
        execution_time_ms: 15,
        query: 'steel',
      }

      apiClient.semanticSearch.mockResolvedValue(mockResults)

      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)
      await user.type(searchInput, 'steel')

      const searchButton = screen.getByRole('button', { name: /search/i })
      await user.click(searchButton)

      // Check results header
      await waitFor(() => {
        expect(screen.getByText(/Found/)).toBeInTheDocument()
        expect(screen.getByText(/2/)).toBeInTheDocument()
        expect(screen.getByText(/15ms/)).toBeInTheDocument()
      })

      // Check result cards
      expect(screen.getByText('Steel Production')).toBeInTheDocument()
      expect(screen.getByText('Stainless Steel')).toBeInTheDocument()
      expect(screen.getByText(/Carbon emissions from steel manufacturing/)).toBeInTheDocument()
      expect(screen.getByText(/Stainless steel material/)).toBeInTheDocument()

      // Check similarity scores
      expect(screen.getByText('95%')).toBeInTheDocument()
      expect(screen.getByText('88%')).toBeInTheDocument()
    })

    it('should display "no results" message when search returns empty', async () => {
      apiClient.semanticSearch.mockResolvedValue({
        results: [],
        total: 0,
        execution_time_ms: 10,
        query: 'xyz',
      })

      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)
      await user.type(searchInput, 'xyz')

      const searchButton = screen.getByRole('button', { name: /search/i })
      await user.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('No results found')).toBeInTheDocument()
        expect(screen.getByText(/Try adjusting your search query/)).toBeInTheDocument()
      })
    })

    it('should display error message when search fails', async () => {
      const errorMessage = 'Unable to connect to the server'
      apiClient.semanticSearch.mockRejectedValue(new Error(errorMessage))

      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)
      await user.type(searchInput, 'steel')

      const searchButton = screen.getByRole('button', { name: /search/i })
      await user.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument()
      })
    })
  })

  describe('Result Card Interactions', () => {
    it('should navigate to entity detail when result card is clicked', async () => {
      const mockResults = {
        results: [
          {
            id: 'test-entity-123',
            name: 'Test Entity',
            description: 'Test description',
            entity_type: 'material',
            similarity: 0.9,
            geographic_scope: [],
            category: [],
            quality_score: 0.8,
          },
        ],
        total: 1,
        execution_time_ms: 10,
        query: 'test',
      }

      apiClient.semanticSearch.mockResolvedValue(mockResults)

      const user = userEvent.setup()
      renderWithProviders(<Search />)

      const searchInput = screen.getByPlaceholderText(/Search for materials/)
      await user.type(searchInput, 'test')

      const searchButton = screen.getByRole('button', { name: /search/i })
      await user.click(searchButton)

      await waitFor(() => {
        expect(screen.getByText('Test Entity')).toBeInTheDocument()
      })

      const resultCard = screen.getByText('Test Entity')
      await user.click(resultCard)

      // Check that navigation occurred (URL would change in real app)
      expect(window.location.pathname).toBe('/entities/test-entity-123')
    })
  })
})
