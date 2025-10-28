/**
 * Entity Detail Page
 * Comprehensive entity view with all metadata and emission factors
 * Designed for information density and clarity (Tufte principles)
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
  Link,
  LinearProgress,
  Skeleton,
  Alert,
} from '@mui/material'
import {
  ArrowBack as ArrowBackIcon,
  Science as ScienceIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'
import { getEntity } from '../api/client'

// Info Row Component
function InfoRow({ label, value, fullWidth = false }) {
  if (!value && value !== 0) return null

  return (
    <Box sx={{ py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
      <Typography
        variant="caption"
        sx={{
          color: 'text.secondary',
          fontWeight: 600,
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          display: 'block',
          mb: 0.5,
        }}
      >
        {label}
      </Typography>
      <Typography variant="body1">{value}</Typography>
    </Box>
  )
}

// Quality Score Component
function QualityScore({ score }) {
  if (!score && score !== 0) return null

  const percentage = score * 100
  const color =
    score >= 0.8 ? 'success' : score >= 0.6 ? 'info' : score >= 0.4 ? 'warning' : 'error'

  const Icon =
    score >= 0.8 ? CheckCircleIcon : score >= 0.6 ? ScienceIcon : score >= 0.4 ? WarningIcon : ErrorIcon

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Box
          sx={{
            p: 1.5,
            bgcolor: `${color}.50`,
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <Icon sx={{ fontSize: 32, color: `${color}.main` }} />
        </Box>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 0.5 }}>
            {percentage.toFixed(0)}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Quality Score
          </Typography>
        </Box>
      </Box>
      <LinearProgress
        variant="determinate"
        value={percentage}
        color={color}
        sx={{ height: 8, borderRadius: 1 }}
      />
    </Box>
  )
}

function EntityDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: entity, isLoading, error } = useQuery({
    queryKey: ['entity', id],
    queryFn: () => getEntity(id),
  })

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 6 }}>
        <Alert severity="error">{error.message}</Alert>
      </Container>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 3 }}>
        <Link
          component="button"
          variant="body2"
          onClick={() => navigate('/entities')}
          sx={{ textDecoration: 'none', color: 'text.secondary' }}
        >
          Entities
        </Link>
        <Typography variant="body2" color="text.primary">
          {isLoading ? 'Loading...' : entity?.name}
        </Typography>
      </Breadcrumbs>

      {/* Back Button */}
      <IconButton onClick={() => navigate('/entities')} sx={{ mb: 2 }}>
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
              {entity.name}
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              <Chip
                label={entity.entity_type}
                sx={{ textTransform: 'capitalize', fontWeight: 500 }}
              />
              <Chip
                label={entity.validation_status}
                color={
                  entity.validation_status === 'validated'
                    ? 'success'
                    : entity.validation_status === 'pending'
                    ? 'warning'
                    : 'error'
                }
                variant="outlined"
                sx={{ textTransform: 'capitalize' }}
              />
              {entity.custom_tags?.map((tag) => (
                <Chip key={tag} label={tag} size="small" variant="outlined" />
              ))}
            </Stack>
          </Box>

          {/* Main Content Grid */}
          <Grid container spacing={3}>
            {/* Left Column - Details */}
            <Grid item xs={12} md={8}>
              {/* Description */}
              {entity.description && (
                <Paper elevation={0} sx={{ p: 3, mb: 3, border: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="overline" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                    Description
                  </Typography>
                  <Typography variant="body1" sx={{ mt: 1, lineHeight: 1.7 }}>
                    {entity.description}
                  </Typography>
                </Paper>
              )}

              {/* Metadata */}
              <Paper elevation={0} sx={{ p: 3, mb: 3, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  Metadata
                </Typography>
                <Box>
                  <InfoRow label="Source ID" value={entity.source_id} />
                  <InfoRow
                    label="Category"
                    value={entity.category_hierarchy?.join(' → ') || '—'}
                  />
                  <InfoRow
                    label="Geographic Scope"
                    value={entity.geographic_scope?.join(', ') || '—'}
                  />
                  <InfoRow
                    label="Confidence Level"
                    value={
                      entity.confidence_level
                        ? `${(entity.confidence_level * 100).toFixed(0)}%`
                        : '—'
                    }
                  />
                  <InfoRow
                    label="Created"
                    value={new Date(entity.created_at).toLocaleDateString()}
                  />
                  <InfoRow
                    label="Updated"
                    value={new Date(entity.updated_at).toLocaleDateString()}
                  />
                </Box>
              </Paper>

              {/* Emission Factors */}
              {entity.emission_factors && entity.emission_factors.length > 0 && (
                <Paper elevation={0} sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                    Emission Factors ({entity.emission_factors.length})
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Value</TableCell>
                          <TableCell>Unit</TableCell>
                          <TableCell>Scope</TableCell>
                          <TableCell>Stage</TableCell>
                          <TableCell>Standard</TableCell>
                          <TableCell align="right">Quality</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {entity.emission_factors.map((ef) => (
                          <TableRow key={ef.id}>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {ef.value.toFixed(3)}
                              </Typography>
                              {(ef.uncertainty_min || ef.uncertainty_max) && (
                                <Typography variant="caption" color="text.secondary">
                                  ±{' '}
                                  {ef.uncertainty_min?.toFixed(2) || 0}-
                                  {ef.uncertainty_max?.toFixed(2) || 0}
                                </Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">{ef.unit}</Typography>
                            </TableCell>
                            <TableCell>
                              {ef.scope ? (
                                <Chip
                                  label={`Scope ${ef.scope}`}
                                  size="small"
                                  color={
                                    ef.scope === 1 ? 'error' : ef.scope === 2 ? 'warning' : 'info'
                                  }
                                />
                              ) : (
                                '—'
                              )}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                                {ef.lifecycle_stage || '—'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">{ef.accounting_standard || '—'}</Typography>
                            </TableCell>
                            <TableCell align="right">
                              {ef.quality_score ? (
                                <Chip
                                  label={`${(ef.quality_score * 100).toFixed(0)}%`}
                                  size="small"
                                  color={
                                    ef.quality_score >= 0.8
                                      ? 'success'
                                      : ef.quality_score >= 0.6
                                      ? 'info'
                                      : 'warning'
                                  }
                                />
                              ) : (
                                '—'
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              )}
            </Grid>

            {/* Right Column - Quality & Stats */}
            <Grid item xs={12} md={4}>
              {/* Quality Score */}
              <Paper elevation={0} sx={{ p: 3, mb: 3, border: '1px solid', borderColor: 'divider' }}>
                <QualityScore score={entity.quality_score} />
              </Paper>

              {/* Quick Stats */}
              <Paper elevation={0} sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="overline" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                  Quick Stats
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="h4" sx={{ fontWeight: 300 }}>
                      {entity.emission_factors?.length || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Emission Factors
                    </Typography>
                  </Box>
                  {entity.emission_factors && entity.emission_factors.length > 0 && (
                    <>
                      <Divider />
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Scopes Covered
                        </Typography>
                        <Stack direction="row" spacing={0.5}>
                          {[1, 2, 3].map((scope) => {
                            const hasScope = entity.emission_factors.some((ef) => ef.scope === scope)
                            return (
                              <Chip
                                key={scope}
                                label={scope}
                                size="small"
                                color={hasScope ? 'primary' : 'default'}
                                variant={hasScope ? 'filled' : 'outlined'}
                              />
                            )
                          })}
                        </Stack>
                      </Box>
                    </>
                  )}
                </Stack>
              </Paper>
            </Grid>
          </Grid>
        </>
      )}
    </Container>
  )
}

export default EntityDetail
