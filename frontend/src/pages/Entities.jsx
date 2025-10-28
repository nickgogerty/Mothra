/**
 * Entities List Page
 * Clean, table-based display with filtering (Nielsen's user control principle)
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Container,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Chip,
  LinearProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stack,
  IconButton,
  Tooltip,
  Skeleton,
  Alert,
} from '@mui/material'
import {
  Visibility as VisibilityIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material'
import { getEntities, getEntityTypes } from '../api/client'

function Entities() {
  const navigate = useNavigate()
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(20)
  const [entityType, setEntityType] = useState('')
  const [validationStatus, setValidationStatus] = useState('')
  const [minQuality, setMinQuality] = useState('')

  // Fetch entities
  const { data, isLoading, error } = useQuery({
    queryKey: ['entities', page + 1, rowsPerPage, entityType, validationStatus, minQuality],
    queryFn: () =>
      getEntities({
        page: page + 1,
        page_size: rowsPerPage,
        entity_type: entityType || undefined,
        validation_status: validationStatus || undefined,
        min_quality: minQuality || undefined,
      }),
  })

  // Fetch entity types for filter
  const { data: entityTypesData } = useQuery({
    queryKey: ['entity-types'],
    queryFn: getEntityTypes,
  })

  const handleChangePage = (event, newPage) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const handleViewEntity = (entityId) => {
    navigate(`/entities/${entityId}`)
  }

  // Quality badge component
  const QualityBadge = ({ score }) => {
    if (!score) return <Chip label="N/A" size="small" variant="outlined" />

    const percentage = score * 100
    const color =
      score >= 0.8 ? 'success' : score >= 0.6 ? 'info' : score >= 0.4 ? 'warning' : 'error'

    return (
      <Chip
        label={`${percentage.toFixed(0)}%`}
        size="small"
        color={color}
        sx={{ minWidth: 60, fontWeight: 600 }}
      />
    )
  }

  // Validation status badge
  const ValidationBadge = ({ status }) => {
    const config = {
      validated: { color: 'success', label: 'Validated' },
      pending: { color: 'warning', label: 'Pending' },
      rejected: { color: 'error', label: 'Rejected' },
    }

    const { color, label } = config[status] || { color: 'default', label: status }

    return <Chip label={label} size="small" color={color} variant="outlined" />
  }

  return (
    <Container maxWidth="xl" sx={{ py: 6 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h2" sx={{ mb: 1, fontWeight: 300 }}>
          Carbon Entities
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Browse and filter carbon emission data
        </Typography>
      </Box>

      {/* Filters */}
      <Paper elevation={0} sx={{ p: 3, mb: 3, border: '1px solid', borderColor: 'divider' }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="flex-end">
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Entity Type</InputLabel>
            <Select
              value={entityType}
              label="Entity Type"
              onChange={(e) => {
                setEntityType(e.target.value)
                setPage(0)
              }}
            >
              <MenuItem value="">All Types</MenuItem>
              {entityTypesData?.entity_types.map((type) => (
                <MenuItem key={type.type} value={type.type} sx={{ textTransform: 'capitalize' }}>
                  {type.type} ({type.count})
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Validation Status</InputLabel>
            <Select
              value={validationStatus}
              label="Validation Status"
              onChange={(e) => {
                setValidationStatus(e.target.value)
                setPage(0)
              }}
            >
              <MenuItem value="">All Status</MenuItem>
              <MenuItem value="validated">Validated</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="rejected">Rejected</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Min Quality</InputLabel>
            <Select
              value={minQuality}
              label="Min Quality"
              onChange={(e) => {
                setMinQuality(e.target.value)
                setPage(0)
              }}
            >
              <MenuItem value="">Any Quality</MenuItem>
              <MenuItem value="0.8">80%+</MenuItem>
              <MenuItem value="0.6">60%+</MenuItem>
              <MenuItem value="0.4">40%+</MenuItem>
              <MenuItem value="0.2">20%+</MenuItem>
            </Select>
          </FormControl>

          <Box sx={{ flex: 1 }} />

          <Typography variant="body2" color="text.secondary">
            {data ? `${data.total.toLocaleString()} entities` : '—'}
          </Typography>
        </Stack>
      </Paper>

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error.message}
        </Alert>
      )}

      {/* Table */}
      <Paper elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Geography</TableCell>
                <TableCell align="center">Quality</TableCell>
                <TableCell align="center">Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                // Loading skeletons
                Array.from(new Array(rowsPerPage)).map((_, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Skeleton variant="text" />
                    </TableCell>
                    <TableCell>
                      <Skeleton variant="text" />
                    </TableCell>
                    <TableCell>
                      <Skeleton variant="text" />
                    </TableCell>
                    <TableCell>
                      <Skeleton variant="text" />
                    </TableCell>
                    <TableCell>
                      <Skeleton variant="text" />
                    </TableCell>
                    <TableCell>
                      <Skeleton variant="text" />
                    </TableCell>
                  </TableRow>
                ))
              ) : data?.entities.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 8 }}>
                    <Typography variant="body1" color="text.secondary">
                      No entities found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                data?.entities.map((entity) => (
                  <TableRow
                    key={entity.id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => handleViewEntity(entity.id)}
                  >
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {entity.name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={entity.entity_type}
                        size="small"
                        variant="outlined"
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {entity.geographic_scope?.join(', ') || '—'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <QualityBadge score={entity.quality_score} />
                    </TableCell>
                    <TableCell align="center">
                      <ValidationBadge status={entity.validation_status} />
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleViewEntity(entity.id)
                          }}
                        >
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        {data && (
          <TablePagination
            component="div"
            count={data.total}
            page={page}
            onPageChange={handleChangePage}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            rowsPerPageOptions={[10, 20, 50, 100]}
            sx={{
              borderTop: '1px solid',
              borderColor: 'divider',
            }}
          />
        )}
      </Paper>
    </Container>
  )
}

export default Entities
