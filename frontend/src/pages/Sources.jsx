/**
 * Data Sources Page
 * Clear provenance and monitoring (Tufte's credibility principle)
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Chip,
  Stack,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper,
  LinearProgress,
  Skeleton,
  Alert,
} from '@mui/material'
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Storage as StorageIcon,
} from '@mui/icons-material'
import { getDataSources } from '../api/client'

function Sources() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')
  const [category, setCategory] = useState('')
  const [priority, setPriority] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['sources', status, category, priority],
    queryFn: () =>
      getDataSources({
        status: status || undefined,
        category: category || undefined,
        priority: priority || undefined,
        page_size: 100,
      }),
  })

  const handleSourceClick = (sourceId) => {
    navigate(`/sources/${sourceId}`)
  }

  // Status badge
  const StatusBadge = ({ status }) => {
    const config = {
      active: { color: 'success', icon: CheckCircleIcon, label: 'Active' },
      inactive: { color: 'default', icon: ScheduleIcon, label: 'Inactive' },
      failed: { color: 'error', icon: ErrorIcon, label: 'Failed' },
      discovered: { color: 'info', icon: StorageIcon, label: 'Discovered' },
      validated: { color: 'success', icon: CheckCircleIcon, label: 'Validated' },
    }

    const { color, icon: Icon, label } = config[status] || {
      color: 'default',
      icon: StorageIcon,
      label: status,
    }

    return (
      <Chip
        icon={<Icon />}
        label={label}
        size="small"
        color={color}
        sx={{ textTransform: 'capitalize' }}
      />
    )
  }

  // Priority badge
  const PriorityBadge = ({ priority }) => {
    const colorMap = {
      critical: 'error',
      high: 'warning',
      medium: 'info',
      low: 'default',
    }

    return (
      <Chip
        label={priority}
        size="small"
        color={colorMap[priority] || 'default'}
        variant="outlined"
        sx={{ textTransform: 'capitalize', fontWeight: 600 }}
      />
    )
  }

  return (
    <Container maxWidth="xl" sx={{ py: 6 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h2" sx={{ mb: 1, fontWeight: 300 }}>
          Data Sources
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor and manage carbon data sources
        </Typography>
      </Box>

      {/* Filters */}
      <Paper elevation={0} sx={{ p: 3, mb: 4, border: '1px solid', borderColor: 'divider' }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="flex-end">
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Status</InputLabel>
            <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
              <MenuItem value="">All Status</MenuItem>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="inactive">Inactive</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
              <MenuItem value="discovered">Discovered</MenuItem>
              <MenuItem value="validated">Validated</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Category</InputLabel>
            <Select value={category} label="Category" onChange={(e) => setCategory(e.target.value)}>
              <MenuItem value="">All Categories</MenuItem>
              <MenuItem value="government">Government</MenuItem>
              <MenuItem value="standards">Standards</MenuItem>
              <MenuItem value="research">Research</MenuItem>
              <MenuItem value="commercial">Commercial</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Priority</InputLabel>
            <Select value={priority} label="Priority" onChange={(e) => setPriority(e.target.value)}>
              <MenuItem value="">All Priorities</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="low">Low</MenuItem>
            </Select>
          </FormControl>

          <Box sx={{ flex: 1 }} />

          <Typography variant="body2" color="text.secondary">
            {data ? `${data.total.toLocaleString()} sources` : '—'}
          </Typography>
        </Stack>
      </Paper>

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error.message}
        </Alert>
      )}

      {/* Sources Grid */}
      <Grid container spacing={3}>
        {isLoading
          ? Array.from(new Array(12)).map((_, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Skeleton variant="rectangular" height={200} />
              </Grid>
            ))
          : data?.sources.map((source) => (
              <Grid item xs={12} sm={6} md={4} key={source.id}>
                <Card
                  elevation={0}
                  sx={{
                    height: '100%',
                    border: '1px solid',
                    borderColor: 'divider',
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  <CardActionArea onClick={() => handleSourceClick(source.id)}>
                    <CardContent>
                      {/* Header */}
                      <Box sx={{ mb: 2 }}>
                        <Typography
                          variant="h6"
                          sx={{
                            mb: 1,
                            fontWeight: 600,
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                            minHeight: 64,
                          }}
                        >
                          {source.name}
                        </Typography>
                        <Stack direction="row" spacing={1}>
                          <StatusBadge status={source.status} />
                          <PriorityBadge priority={source.priority} />
                        </Stack>
                      </Box>

                      {/* Metadata */}
                      <Stack spacing={1.5}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Category
                          </Typography>
                          <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                            {source.category}
                          </Typography>
                        </Box>

                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Type
                          </Typography>
                          <Typography variant="body2" sx={{ textTransform: 'uppercase' }}>
                            {source.source_type}
                          </Typography>
                        </Box>

                        {source.update_frequency && (
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Update Frequency
                            </Typography>
                            <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                              {source.update_frequency}
                            </Typography>
                          </Box>
                        )}

                        {source.estimated_size_gb && (
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Est. Size
                            </Typography>
                            <Typography variant="body2">
                              {source.estimated_size_gb.toFixed(1)} GB
                            </Typography>
                          </Box>
                        )}

                        {source.last_crawled && (
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Last Crawled
                            </Typography>
                            <Typography variant="body2">
                              {new Date(source.last_crawled).toLocaleDateString()}
                            </Typography>
                          </Box>
                        )}

                        {source.error_count > 0 && (
                          <Box>
                            <Typography variant="caption" color="error.main">
                              Errors
                            </Typography>
                            <Typography variant="body2" color="error.main" sx={{ fontWeight: 600 }}>
                              {source.error_count} error(s)
                            </Typography>
                          </Box>
                        )}
                      </Stack>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            ))}
      </Grid>

      {/* Empty State */}
      {data?.sources.length === 0 && !isLoading && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <StorageIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No sources found
          </Typography>
        </Box>
      )}
    </Container>
  )
}

export default Sources
