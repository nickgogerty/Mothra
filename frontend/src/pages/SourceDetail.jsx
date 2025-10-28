/**
 * Source Detail Page
 * Comprehensive source monitoring with crawl history
 */

import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Chip,
  Stack,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Breadcrumbs,
  Link as MuiLink,
  Alert,
  Skeleton,
  LinearProgress,
} from '@mui/material'
import {
  ArrowBack as ArrowBackIcon,
  OpenInNew as OpenInNewIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material'
import { getDataSource } from '../api/client'

function SourceDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: source, isLoading, error } = useQuery({
    queryKey: ['source', id],
    queryFn: () => getDataSource(id),
  })

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 6 }}>
        <Alert severity="error">{error.message}</Alert>
      </Container>
    )
  }

  // Status icon
  const StatusIcon = ({ status }) => {
    const config = {
      active: { Icon: CheckCircleIcon, color: 'success.main' },
      completed: { Icon: CheckCircleIcon, color: 'success.main' },
      failed: { Icon: ErrorIcon, color: 'error.main' },
      running: { Icon: ScheduleIcon, color: 'info.main' },
      partial: { Icon: ErrorIcon, color: 'warning.main' },
    }

    const { Icon, color } = config[status] || { Icon: ScheduleIcon, color: 'text.secondary' }

    return <Icon sx={{ fontSize: 20, color }} />
  }

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 3 }}>
        <MuiLink
          component="button"
          variant="body2"
          onClick={() => navigate('/sources')}
          sx={{ textDecoration: 'none', color: 'text.secondary' }}
        >
          Sources
        </MuiLink>
        <Typography variant="body2" color="text.primary">
          {isLoading ? 'Loading...' : source?.name}
        </Typography>
      </Breadcrumbs>

      {/* Back Button */}
      <IconButton onClick={() => navigate('/sources')} sx={{ mb: 2 }}>
        <ArrowBackIcon />
      </IconButton>

      {isLoading ? (
        <Box>
          <Skeleton variant="text" width="60%" height={60} />
          <Skeleton variant="rectangular" height={400} sx={{ mt: 3 }} />
        </Box>
      ) : (
        <>
          {/* Header */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h2" sx={{ mb: 2, fontWeight: 300 }}>
              {source.name}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
              <Chip
                label={source.status}
                color={
                  source.status === 'active'
                    ? 'success'
                    : source.status === 'failed'
                    ? 'error'
                    : 'default'
                }
                sx={{ textTransform: 'capitalize' }}
              />
              <Chip
                label={source.priority}
                color={
                  source.priority === 'critical'
                    ? 'error'
                    : source.priority === 'high'
                    ? 'warning'
                    : 'info'
                }
                variant="outlined"
                sx={{ textTransform: 'capitalize' }}
              />
              <Chip
                label={source.category}
                variant="outlined"
                sx={{ textTransform: 'capitalize' }}
              />
              <MuiLink
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 2 }}
              >
                <Typography variant="body2">Visit Source</Typography>
                <OpenInNewIcon fontSize="small" />
              </MuiLink>
            </Stack>
          </Box>

          <Grid container spacing={3}>
            {/* Left Column - Details */}
            <Grid item xs={12} md={8}>
              {/* Source Configuration */}
              <Paper elevation={0} sx={{ p: 3, mb: 3, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Configuration
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      SOURCE TYPE
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 0.5, textTransform: 'uppercase' }}>
                      {source.source_type}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      ACCESS METHOD
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 0.5, textTransform: 'uppercase' }}>
                      {source.access_method}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      DATA FORMAT
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 0.5, textTransform: 'uppercase' }}>
                      {source.data_format || '—'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      UPDATE FREQUENCY
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 0.5, textTransform: 'capitalize' }}>
                      {source.update_frequency || '—'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      AUTH REQUIRED
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 0.5 }}>
                      {source.auth_required ? 'Yes' : 'No'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      RATE LIMIT
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 0.5 }}>
                      {source.rate_limit ? `${source.rate_limit} req/min` : 'None'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      ESTIMATED SIZE
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 0.5 }}>
                      {source.estimated_size_gb ? `${source.estimated_size_gb.toFixed(1)} GB` : '—'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      ERROR COUNT
                    </Typography>
                    <Typography
                      variant="body1"
                      sx={{ mt: 0.5, color: source.error_count > 0 ? 'error.main' : 'inherit' }}
                    >
                      {source.error_count}
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>

              {/* Crawl History */}
              {source.recent_crawls && source.recent_crawls.length > 0 && (
                <Paper elevation={0} sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                    Recent Crawls ({source.recent_crawls.length})
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Status</TableCell>
                          <TableCell>Started</TableCell>
                          <TableCell align="right">Found</TableCell>
                          <TableCell align="right">Inserted</TableCell>
                          <TableCell align="right">Failed</TableCell>
                          <TableCell align="right">Duration</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {source.recent_crawls.map((crawl) => (
                          <TableRow key={crawl.id} hover>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <StatusIcon status={crawl.status} />
                                <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                                  {crawl.status}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {new Date(crawl.started_at).toLocaleString()}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2">
                                {crawl.records_found.toLocaleString()}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2" sx={{ color: 'success.main', fontWeight: 600 }}>
                                {crawl.records_inserted.toLocaleString()}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography
                                variant="body2"
                                sx={{
                                  color: crawl.records_failed > 0 ? 'error.main' : 'inherit',
                                  fontWeight: crawl.records_failed > 0 ? 600 : 400,
                                }}
                              >
                                {crawl.records_failed.toLocaleString()}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2">
                                {crawl.duration_seconds
                                  ? `${crawl.duration_seconds.toFixed(1)}s`
                                  : '—'}
                              </Typography>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Show error messages for failed crawls */}
                  {source.recent_crawls.some((c) => c.error_message) && (
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="overline" color="error.main" sx={{ fontWeight: 600 }}>
                        Recent Errors
                      </Typography>
                      <Stack spacing={1} sx={{ mt: 1 }}>
                        {source.recent_crawls
                          .filter((c) => c.error_message)
                          .slice(0, 3)
                          .map((crawl) => (
                            <Alert key={crawl.id} severity="error" sx={{ py: 0.5 }}>
                              <Typography variant="caption">
                                {new Date(crawl.started_at).toLocaleString()}: {crawl.error_message}
                              </Typography>
                            </Alert>
                          ))}
                      </Stack>
                    </Box>
                  )}
                </Paper>
              )}
            </Grid>

            {/* Right Column - Stats */}
            <Grid item xs={12} md={4}>
              {/* Summary Stats */}
              <Paper elevation={0} sx={{ p: 3, mb: 3, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="overline" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                  Summary
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Stack spacing={3}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Last Crawled
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 0.5, fontWeight: 500 }}>
                      {source.last_crawled
                        ? new Date(source.last_crawled).toLocaleDateString()
                        : 'Never'}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Last Success
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 0.5, fontWeight: 500 }}>
                      {source.last_successful_crawl
                        ? new Date(source.last_successful_crawl).toLocaleDateString()
                        : 'Never'}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Created
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 0.5, fontWeight: 500 }}>
                      {new Date(source.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Updated
                    </Typography>
                    <Typography variant="body1" sx={{ mt: 0.5, fontWeight: 500 }}>
                      {new Date(source.updated_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                </Stack>
              </Paper>

              {/* Success Rate */}
              {source.recent_crawls && source.recent_crawls.length > 0 && (
                <Paper elevation={0} sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="overline" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                    Recent Performance
                  </Typography>
                  <Divider sx={{ my: 2 }} />
                  {(() => {
                    const successCount = source.recent_crawls.filter(
                      (c) => c.status === 'completed'
                    ).length
                    const successRate = (successCount / source.recent_crawls.length) * 100

                    return (
                      <>
                        <Box sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2">Success Rate</Typography>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {successRate.toFixed(0)}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={successRate}
                            color={successRate >= 80 ? 'success' : successRate >= 50 ? 'warning' : 'error'}
                            sx={{ height: 8, borderRadius: 1 }}
                          />
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          {successCount} of {source.recent_crawls.length} recent crawls succeeded
                        </Typography>
                      </>
                    )
                  })()}
                </Paper>
              )}
            </Grid>
          </Grid>
        </>
      )}
    </Container>
  )
}

export default SourceDetail
