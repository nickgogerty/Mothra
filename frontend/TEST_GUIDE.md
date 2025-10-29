# MOTHRA Frontend Testing Guide

## Overview

This guide explains the comprehensive unit tests created for the MOTHRA frontend GUI, covering all user interactions with fields, buttons, and API responses.

## Test Setup

### Installation

Install test dependencies:

```bash
cd frontend
npm install
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with UI
npm run test:ui

# Run tests with coverage report
npm run test:coverage
```

## Test Files

### 1. Search Page Tests (`src/pages/__tests__/Search.test.jsx`)

Comprehensive tests for the semantic search functionality.

#### Test Coverage:

**Initial Render**
- ✓ Renders search page with all elements (title, description, input, button, filters)
- ✓ Shows empty state message
- ✓ Search button is disabled when input is empty

**Search Input Field**
- ✓ Updates input value when user types
- ✓ Enables search button when query has 2+ characters
- ✓ Shows clear button when input has text
- ✓ Clears input when clear button is clicked

**Auto-search Functionality**
- ✓ Triggers search automatically after 500ms of typing (debounced)
- ✓ Does not call API immediately while user is typing

**Search Button**
- ✓ Triggers search when clicked
- ✓ Triggers search when Enter key is pressed
- ✓ Passes correct query parameters to API

**Entity Type Filters**
- ✓ Toggles entity type filter when clicked
- ✓ Includes entity type in search query
- ✓ All filter chips are rendered (process, material, product, energy)

**Search Results Display**
- ✓ Displays loading state while searching
- ✓ Displays search results when data is returned
- ✓ Shows result count and execution time
- ✓ Displays similarity scores correctly
- ✓ Shows "no results" message when search returns empty
- ✓ Displays error message when search fails

**Result Card Interactions**
- ✓ Navigates to entity detail when result card is clicked
- ✓ Proper routing to entity detail page

#### Example Test:

```javascript
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
  fireEvent.keyPress(searchInput, { key: 'Enter' })

  await waitFor(() => {
    expect(mockSearch).toHaveBeenCalledWith('concrete', { entityType: null })
  })
})
```

### 2. Dashboard Page Tests (`src/pages/__tests__/Dashboard.test.jsx`)

Comprehensive tests for the dashboard statistics and visualizations.

#### Test Coverage:

**Initial Render**
- ✓ Renders dashboard with page title and description
- ✓ Shows loading skeletons while fetching data

**Overview Statistics Cards**
- ✓ Displays all key metric cards with correct values
- ✓ Shows Total Entities count
- ✓ Shows Data Sources (active/total)
- ✓ Shows Validated Entities count and percentage
- ✓ Shows Average Quality score as percentage
- ✓ Calculates validation percentage correctly

**Quality Distribution Chart**
- ✓ Displays quality distribution chart with correct data
- ✓ Shows all quality score ranges (0.0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0)
- ✓ Renders bar chart component with SVG elements

**GHG Scope Distribution**
- ✓ Displays scope distribution with all scopes (1, 2, 3)
- ✓ Shows scope labels (Direct Emissions, Indirect Energy, Value Chain)
- ✓ Displays scope percentages correctly

**Entity Type Breakdown**
- ✓ Displays entity type breakdown section
- ✓ Shows all entity types (material, process, product, energy, transport)
- ✓ Displays entity counts for each type
- ✓ Shows validation counts and average quality for each type

**Error Handling**
- ✓ Displays error message when API call fails
- ✓ Shows retry button on error
- ✓ Retries fetching data when retry button is clicked
- ✓ Shows loading state during retry

**Data Formatting**
- ✓ Formats large numbers with commas (15,234)
- ✓ Formats percentages to one decimal place (85.3%)
- ✓ Formats quality scores as percentages

**Data Integrity**
- ✓ Handles missing or null data gracefully
- ✓ Renders with 0 values when no data available

#### Example Test:

```javascript
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

  // Should succeed on retry
  await waitFor(() => {
    expect(screen.getByText('15,234')).toBeInTheDocument()
  })

  expect(mockGetStats).toHaveBeenCalledTimes(2)
})
```

## API Mocking

All tests mock the API client to simulate various scenarios:

```javascript
import * as apiClient from '../../api/client'
vi.mock('../../api/client')

// Mock successful response
apiClient.semanticSearch.mockResolvedValue({
  results: [...],
  total: 10,
  execution_time_ms: 15,
  query: 'steel',
})

// Mock error response
apiClient.semanticSearch.mockRejectedValue(new Error('Connection failed'))
```

## Test Helpers

### `renderWithProviders()`

Wraps components with required providers (React Query, Router):

```javascript
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
```

## User Interaction Testing

Tests use `@testing-library/user-event` for realistic user interactions:

```javascript
const user = userEvent.setup()

// Type in input
await user.type(searchInput, 'steel')

// Click button
await user.click(searchButton)

// Clear input
await user.clear(searchInput)
```

## Async Testing

Tests properly wait for async operations:

```javascript
await waitFor(() => {
  expect(screen.getByText('Results found')).toBeInTheDocument()
})
```

## Coverage Goals

- **Lines:** 80%+
- **Functions:** 80%+
- **Branches:** 75%+
- **Statements:** 80%+

Run `npm run test:coverage` to generate coverage report.

## Best Practices

1. **Test User Behavior**: Focus on what users see and do, not implementation details
2. **Mock API Calls**: Always mock external API calls for predictable tests
3. **Wait for Async**: Use `waitFor()` for async operations
4. **Accessible Queries**: Use `getByRole`, `getByLabelText` when possible
5. **Clean Up**: Tests automatically clean up after each test
6. **Descriptive Names**: Test names should clearly describe what they test

## Troubleshooting

### Tests fail with "Cannot find module"
- Ensure all dependencies are installed: `npm install`

### Tests timeout
- Check that mock APIs resolve/reject properly
- Increase timeout if needed: `{ timeout: 10000 }`

### Components don't render
- Check that providers (QueryClient, Router) are included
- Verify mocks are set up correctly

## Future Tests to Add

- Integration tests with real API (using test database)
- E2E tests with Playwright or Cypress
- Performance tests
- Accessibility tests (a11y)

## Running in CI/CD

Add to your CI pipeline:

```yaml
- name: Run tests
  run: |
    cd frontend
    npm install
    npm test -- --run
    npm run test:coverage
```

## Conclusion

These comprehensive unit tests ensure that all user interactions with the MOTHRA frontend work correctly, from typing in search fields to viewing dashboard statistics. The tests verify both happy paths and error scenarios, providing confidence that the GUI responds correctly to user actions.
