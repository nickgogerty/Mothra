/**
 * Dashboard Page
 * High data-density overview following Tufte's principles
 * Swiss minimal design with clear visual hierarchy
 */

import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  Chip,
  Stack,
  LinearProgress,
  Skeleton,
  Alert,
  Button,
} from '@mui/material'
import {
  Science as ScienceIcon,
  Storage as StorageIcon,
  CheckCircle as CheckCircleIcon,
  TrendingUp as TrendingUpIcon,
  Refresh as RefreshIcon,
  ErrorOutline as ErrorIcon,
} from '@mui/icons-material'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getStatistics } from '../api/client'

// Stat Card Component
function StatCard({ title, value, subtitle, icon: Icon, color = 'primary' }) {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        height: '100%',
        border: '1px solid',
        borderColor: 'divider',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.05)',
        },
      }}
    >
      <Stack spacing={2}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Typography
            variant="overline"
            sx={{
              color: 'text.secondary',
              fontWeight: 600,
              letterSpacing: '0.1em',
            }}
          >
            {title}
          </Typography>
          {Icon && (
            <Box
              sx={{
                p: 1,
                bgcolor: `${color}.50`,
                borderRadius: 1,
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <Icon sx={{ fontSize: 20, color: `${color}.main` }} />
            </Box>
          )}
        </Box>

        <Typography variant="h3" sx={{ fontWeight: 300, lineHeight: 1 }}>
          {value.toLocaleString()}
        </Typography>

        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </Stack>
    </Paper>
  )
}

// Quality Distribution Chart
function QualityChart({ data }) {
  if (!data || data.length === 0) return null

  const chartData = data.map((item) => ({
    range: item.range,
    count: item.count,
    percentage: item.percentage,
  }))

  const getBarColor = (range) => {
    if (range.startsWith('0.8')) return '#059669'
    if (range.startsWith('0.6')) return '#0891b2'
    if (range.startsWith('0.4')) return '#f59e0b'
    if (range.startsWith('0.2')) return '#f97316'
    return '#dc2626'
  }

  return (
    <Box sx={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f5f5f5" vertical={false} />
          <XAxis
            dataKey="range"
            tick={{ fill: '#525252', fontSize: 12 }}
            axisLine={{ stroke: '#e5e5e5' }}
          />
          <YAxis
            tick={{ fill: '#525252', fontSize: 12 }}
            axisLine={{ stroke: '#e5e5e5' }}
            label={{ value: 'Count', angle: -90, position: 'insideLeft', style: { fill: '#525252', fontSize: 12 } }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e5e5',
              borderRadius: 4,
              fontSize: 12,
            }}
            formatter={(value, name, props) => [
              `${value} entities (${props.payload.percentage}%)`,
              'Count',
            ]}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.range)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Box>
  )
}

// Entity Type Breakdown
function EntityTypeBreakdown({ data }) {
  if (!data || data.length === 0) return null

  return (
    <Stack spacing={2}>
      {data.slice(0, 5).map((item) => {
        const validatedPercentage = (item.validated / item.count) * 100

        return (
          <Box key={item.entity_type}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                {item.entity_type}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {item.count.toLocaleString()}
              </Typography>
            </Box>

            <LinearProgress
              variant="determinate"
              value={validatedPercentage}
              sx={{
                height: 8,
                borderRadius: 1,
                bgcolor: 'grey.200',
                '& .MuiLinearProgress-bar': {
                  bgcolor: 'success.main',
                },
              }}
            />

            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                {item.validated} validated
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg Quality: {(item.avg_quality * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Box>
        )
      })}
    </Stack>
  )
}

// Scope Distribution
function ScopeDistribution({ data }) {
  if (!data || data.length === 0) return null

  const scopeLabels = {
    1: 'Direct Emissions',
    2: 'Indirect Energy',
    3: 'Value Chain',
  }

  return (
    <Stack spacing={2}>
      {data.map((item) => (
        <Box key={item.scope}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Box>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                Scope {item.scope}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {scopeLabels[item.scope]}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {item.count.toLocaleString()} ({item.percentage}%)
            </Typography>
          </Box>

          <LinearProgress
            variant="determinate"
            value={item.percentage}
            color={item.scope === 1 ? 'error' : item.scope === 2 ? 'warning' : 'info'}
            sx={{ height: 6, borderRadius: 1 }}
          />
        </Box>
      ))}
    </Stack>
  )
}

function Dashboard() {
  const { data: stats, isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: ['statistics'],
    queryFn: getStatistics,
    retry: 2,
    retryDelay: 1000,
  })

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 6 }}>
        <Paper elevation={0} sx={{ p: 4, border: '1px solid', borderColor: 'error.light', bgcolor: 'error.50' }}>
          <Stack spacing={3} alignItems="center">
            <ErrorIcon sx={{ fontSize: 64, color: 'error.main' }} />
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h5" sx={{ mb: 1, color: 'error.dark' }}>
                Unable to Load Dashboard
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                {error.message}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Please ensure the MOTHRA API backend is running and accessible.
              </Typography>
            </Box>
            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={() => refetch()}
              disabled={isRefetching}
            >
              {isRefetching ? 'Retrying...' : 'Retry Connection'}
            </Button>
          </Stack>
        </Paper>
      </Container>
    )
  }

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      {/* Page Header */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h2" sx={{ mb: 1, fontWeight: 300 }}>
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Comprehensive overview of carbon emissions database
        </Typography>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          {isLoading ? (
            <Skeleton variant="rectangular" height={150} />
          ) : (
            <StatCard
              title="Total Entities"
              value={stats?.overview.total_entities || 0}
              subtitle="Carbon data points"
              icon={ScienceIcon}
              color="primary"
            />
          )}
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          {isLoading ? (
            <Skeleton variant="rectangular" height={150} />
          ) : (
            <StatCard
              title="Data Sources"
              value={stats?.overview.active_sources || 0}
              subtitle={`of ${stats?.overview.total_sources || 0} total`}
              icon={StorageIcon}
              color="secondary"
            />
          )}
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          {isLoading ? (
            <Skeleton variant="rectangular" height={150} />
          ) : (
            <StatCard
              title="Validated"
              value={stats?.overview.validated_entities || 0}
              subtitle={`${((stats?.overview.validated_entities / stats?.overview.total_entities) * 100 || 0).toFixed(1)}% of total`}
              icon={CheckCircleIcon}
              color="success"
            />
          )}
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          {isLoading ? (
            <Skeleton variant="rectangular" height={150} />
          ) : (
            <StatCard
              title="Avg Quality"
              value={((stats?.overview.avg_quality_score || 0) * 100).toFixed(0) + '%'}
              subtitle="Database-wide"
              icon={TrendingUpIcon}
              color="info"
            />
          )}
        </Grid>
      </Grid>

      {/* Charts and Breakdowns */}
      <Grid container spacing={3}>
        {/* Quality Distribution */}
        <Grid item xs={12} md={8}>
          <Paper elevation={0} sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
              Quality Score Distribution
            </Typography>
            {isLoading ? (
              <Skeleton variant="rectangular" height={300} />
            ) : (
              <QualityChart data={stats?.quality_distribution} />
            )}
          </Paper>
        </Grid>

        {/* GHG Scope Distribution */}
        <Grid item xs={12} md={4}>
          <Paper elevation={0} sx={{ p: 3, border: '1px solid', borderColor: 'divider', height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
              GHG Scope Coverage
            </Typography>
            {isLoading ? (
              <Skeleton variant="rectangular" height={250} />
            ) : (
              <ScopeDistribution data={stats?.scope_distribution} />
            )}
          </Paper>
        </Grid>

        {/* Entity Type Breakdown */}
        <Grid item xs={12}>
          <Paper elevation={0} sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
              Entity Type Breakdown
            </Typography>
            {isLoading ? (
              <Skeleton variant="rectangular" height={300} />
            ) : (
              <EntityTypeBreakdown data={stats?.entity_type_breakdown} />
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  )
}

export default Dashboard
