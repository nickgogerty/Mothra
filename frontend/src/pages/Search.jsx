/**
 * Search Page
 * Real-time semantic search with clear feedback (Nielsen's visibility)
 * Minimal design focusing on search results (Tufte's data-ink ratio)
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Container,
  TextField,
  Typography,
  Paper,
  Chip,
  Stack,
  CircularProgress,
  InputAdornment,
  IconButton,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  LinearProgress,
  Alert,
  Autocomplete,
} from '@mui/material'
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  Science as ScienceIcon,
} from '@mui/icons-material'
import { semanticSearch, getSearchSuggestions } from '../api/client'

function Search() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [entityType, setEntityType] = useState(null)

  // Debounced search
  const { data, isLoading, error } = useQuery({
    queryKey: ['search', searchQuery, entityType],
    queryFn: () => semanticSearch(searchQuery, { entityType }),
    enabled: searchQuery.length >= 2,
  })

  const handleSearch = (value) => {
    setSearchQuery(value)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && query.length >= 2) {
      handleSearch(query)
    }
  }

  const handleClear = () => {
    setQuery('')
    setSearchQuery('')
  }

  const handleEntityClick = (entityId) => {
    navigate(`/entities/${entityId}`)
  }

  // Quality indicator component
  const QualityIndicator = ({ score }) => {
    if (!score) return null

    const percentage = score * 100
    const color =
      score >= 0.8 ? 'success' : score >= 0.6 ? 'info' : score >= 0.4 ? 'warning' : 'error'

    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="caption" sx={{ minWidth: 60, color: 'text.secondary' }}>
          Quality
        </Typography>
        <Box sx={{ flex: 1, maxWidth: 100 }}>
          <LinearProgress
            variant="determinate"
            value={percentage}
            color={color}
            sx={{ height: 6, borderRadius: 1 }}
          />
        </Box>
        <Typography variant="caption" sx={{ minWidth: 40, fontWeight: 600 }}>
          {percentage.toFixed(0)}%
        </Typography>
      </Box>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      {/* Page Header */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h2" sx={{ mb: 1, fontWeight: 300 }}>
          Semantic Search
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Search carbon entities using natural language. Results ranked by relevance.
        </Typography>
      </Box>

      {/* Search Input */}
      <Paper elevation={0} sx={{ p: 3, mb: 4, border: '1px solid', borderColor: 'divider' }}>
        <TextField
          fullWidth
          placeholder="Search for materials, processes, or products..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          variant="outlined"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: 'text.secondary' }} />
              </InputAdornment>
            ),
            endAdornment: query && (
              <InputAdornment position="end">
                <IconButton onClick={handleClear} size="small">
                  <ClearIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              fontSize: '1.125rem',
            },
          }}
        />

        {/* Search Button */}
        <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
          <IconButton
            onClick={() => handleSearch(query)}
            disabled={query.length < 2}
            sx={{
              bgcolor: 'primary.main',
              color: 'primary.contrastText',
              '&:hover': { bgcolor: 'primary.dark' },
              '&:disabled': { bgcolor: 'grey.200' },
            }}
          >
            <SearchIcon />
          </IconButton>

          {/* Entity Type Filter */}
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {['process', 'material', 'product', 'energy'].map((type) => (
              <Chip
                key={type}
                label={type}
                onClick={() => setEntityType(entityType === type ? null : type)}
                variant={entityType === type ? 'filled' : 'outlined'}
                color={entityType === type ? 'primary' : 'default'}
                size="small"
                sx={{ textTransform: 'capitalize' }}
              />
            ))}
          </Stack>
        </Box>
      </Paper>

      {/* Search Status */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2, color: 'text.secondary' }}>
            Searching...
          </Typography>
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error.message}
        </Alert>
      )}

      {/* Results */}
      {data && !isLoading && (
        <>
          {/* Results Header */}
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              Found <strong>{data.total}</strong> results in{' '}
              <strong>{data.execution_time_ms}ms</strong>
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Query: "{data.query}"
            </Typography>
          </Box>

          {/* Results Grid */}
          {data.results.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <ScienceIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No results found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Try adjusting your search query
              </Typography>
            </Box>
          ) : (
            <Grid container spacing={2}>
              {data.results.map((result) => (
                <Grid item xs={12} key={result.id}>
                  <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
                    <CardActionArea onClick={() => handleEntityClick(result.id)}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="h6" sx={{ mb: 0.5, fontWeight: 500 }}>
                              {result.name}
                            </Typography>
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              sx={{
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                              }}
                            >
                              {result.description || 'No description available'}
                            </Typography>
                          </Box>

                          {/* Similarity Score */}
                          <Box sx={{ ml: 3, textAlign: 'right', minWidth: 80 }}>
                            <Typography variant="caption" color="text.secondary">
                              Similarity
                            </Typography>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              {(result.similarity * 100).toFixed(0)}%
                            </Typography>
                          </Box>
                        </Box>

                        {/* Metadata */}
                        <Stack direction="row" spacing={1} sx={{ mb: 2 }} flexWrap="wrap">
                          <Chip
                            label={result.entity_type}
                            size="small"
                            variant="outlined"
                            sx={{ textTransform: 'capitalize' }}
                          />
                          {result.geographic_scope && result.geographic_scope.length > 0 && (
                            <Chip
                              label={result.geographic_scope[0]}
                              size="small"
                              variant="outlined"
                            />
                          )}
                          {result.category && result.category.length > 0 && (
                            <Chip
                              label={result.category[result.category.length - 1]}
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Stack>

                        {/* Quality Indicator */}
                        <QualityIndicator score={result.quality_score} />
                      </CardContent>
                    </CardActionArea>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </>
      )}

      {/* Empty State */}
      {!searchQuery && !isLoading && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <SearchIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
            Start searching
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Enter at least 2 characters to begin semantic search
          </Typography>
        </Box>
      )}
    </Container>
  )
}

export default Search
